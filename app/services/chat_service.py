import json
import logging
import re
from app.core.llm import llm_client
from app.rag.retriever import retriever
from app.models.schemas import ChatResponse, Recommendation
from app.prompts import templates
from app.core.config import settings
from app.utils.helpers import extract_json_from_text

logger = logging.getLogger(__name__)

def normalize_name(text: str) -> str:
    """Helper to normalize names for robust matching (punctuation, whitespace, case)"""
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def normalize_url(url: str) -> str:
    """Helper to normalize URLs (trailing slashes, whitespace, scheme, www)"""
    if not url:
        return ""
    url = str(url).lower().strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url

class ChatService:
    def process_chat(self, messages: list[dict]) -> ChatResponse:
        
        # 1. Construct a stronger retrieval query
        user_msgs = [msg["content"] for msg in messages if msg["role"] == "user"]
        recent_user_context = " ".join(user_msgs[-3:]) if user_msgs else ""
        
        # 2. Retrieve Context
        top_items = []
        context = ""
        confidence_level = "LOW"
        if recent_user_context:
            retrieved_results = retriever.search(recent_user_context)
            
            if retrieved_results:
                best_score = retrieved_results[0][1]
                
                if best_score >= 0.3:
                    confidence_level = "HIGH"
                elif best_score >= 0.2:
                    confidence_level = "MEDIUM"
                else:
                    confidence_level = "LOW"
                    
                logger.info(f"[DEBUG RAG] Best similarity score: {best_score} | Confidence: {confidence_level}")
                logger.info(f"[DEBUG RAG] Retrieved items and scores: {[(item.name, score) for item, score in retrieved_results]}")
                
                if confidence_level in ["HIGH", "MEDIUM"]:
                    top_items = [res[0] for res in retrieved_results]
                    context = retriever.format_context(top_items)
                    logger.info(f"[DEBUG RAG] Context preserved. Top items grounded: {[item.name for item in top_items]}")
                else:
                    logger.warning(f"[DEBUG RAG] Confidence LOW. Context dropped.")

        # 3. Generate Response
        system_msg = templates.SYSTEM_PROMPT.format(context=context)
        if confidence_level == "MEDIUM":
            system_msg += "\n\nNOTE: The retrieved context is a partial match (MEDIUM confidence). Provide tentative recommendations but encourage the user to clarify their exact needs."
        elif confidence_level == "LOW":
            system_msg += "\n\nNOTE: No relevant context found (LOW confidence). Do NOT provide recommendations. Ask the user for clarification."
            
        llm_messages = [{"role": "system", "content": system_msg}]
        llm_messages.extend(messages[-8:])

        logger.info(f"[DEBUG LLM] Raw Prompt Sent to LLM: {json.dumps(llm_messages, indent=2)}")
        raw_response = llm_client.generate(llm_messages, json_mode=True)
        logger.info(f"[DEBUG LLM] Raw LLM JSON Response: {raw_response}")
        
        # 4. Parse Response
        try:
            parsed_json = extract_json_from_text(raw_response)
            logger.info(f"[DEBUG PARSER] Parsed JSON Object: {parsed_json}")
        except Exception as e:
            logger.error(f"[DEBUG PARSER] Extraction Exception: {e}")
            parsed_json = {}
        
        reply = parsed_json.get("reply", "I'm sorry, I couldn't process that.")
        raw_recs = parsed_json.get("recommendations", [])
        end_of_conversation = parsed_json.get("end_of_conversation", False)
        
        logger.info(f"[DEBUG PARSER] Parsed recommendations array: {raw_recs}")

        valid_recs = []
        if isinstance(raw_recs, list) and len(raw_recs) > 0:
            top_urls_norm = [normalize_url(t.url) for t in top_items]
            
            for i, r in enumerate(raw_recs):
                if not isinstance(r, dict):
                    logger.warning(f"[DEBUG HYDRATION] Item {i} discarded: Not a dictionary.")
                    continue
                    
                r_url = r.get("url", "")
                r_name = r.get("name", "")
                
                norm_r_url = normalize_url(r_url)
                norm_r_name = normalize_name(r_name)
                
                logger.info(f"[DEBUG HYDRATION] Item {i} - Raw URL: '{r_url}' -> Norm URL: '{norm_r_url}'")
                logger.info(f"[DEBUG HYDRATION] Item {i} - Raw Name: '{r_name}' -> Norm Name: '{norm_r_name}'")
                
                real_item = None
                match_strategy = None
                
                # 1. Match ONLY within top_items (strict grounding) via normalized URL
                if norm_r_url:
                    for item in top_items:
                        if normalize_url(item.url) == norm_r_url:
                            real_item = item
                            match_strategy = "TopItems URL match"
                            break
                            
                # 2. Match ONLY within top_items via normalized Name (fallback)
                if not real_item and norm_r_name:
                    for item in top_items:
                        if normalize_name(item.name) == norm_r_name:
                            real_item = item
                            match_strategy = "TopItems Name match"
                            break
                            
                if not real_item:
                    logger.warning(f"[DEBUG HYDRATION] Item {i} discarded: No matching catalog item found in top_items. (Hallucination prevention)")
                    continue
                    
                # 3. Guardrail: Prevent duplicates
                if any(v.url == real_item.url for v in valid_recs):
                    logger.warning(f"[DEBUG HYDRATION] Item {i} discarded: Duplicate recommendation.")
                    continue
                    
                valid_recs.append(Recommendation(
                    name=real_item.name,
                    url=real_item.url,
                    test_type=real_item.test_type,
                    reason=r.get("reason", "")
                ))
                logger.info(f"[DEBUG HYDRATION] Item {i} Hydration SUCCESS via {match_strategy}: {real_item.name}")
        
        # 4. Enforce Schema Limits
        if len(valid_recs) > 10:
            valid_recs = valid_recs[:10]

        final_dicts = [{"name": r.name, "url": r.url, "test_type": r.test_type, "reason": r.reason} for r in valid_recs]
        logger.info(f"[DEBUG FINAL] Final hydrated recommendations array before returning response: {final_dicts}")

        return ChatResponse(
            reply=reply,
            recommendations=valid_recs,
            end_of_conversation=end_of_conversation
        )

chat_service = ChatService()
