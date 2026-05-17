# Approach Document: SHL Assessment Recommender Agent

## 1. Architecture Overview
The application follows a clean, modular architecture centered around FastAPI. The design enforces a **stateless backend**, meaning no conversation state is preserved on the server. The entire conversation history is passed in every request. 
- **API Layer**: Exposes `/health` and `/chat`.
- **Service Layer**: An `Intent Router` analyzes the conversation history to classify the user's intent into five categories: *Clarification, Recommendation, Refinement, Comparison, Refusal*.
- **RAG Pipeline**: A local `FAISS` vector store loaded into memory upon startup.
- **LLM Integration**: A lightweight wrapper around `Groq` and `Gemini` API clients, completely avoiding heavy frameworks like LangChain to reduce latency and memory overhead.

## 2. Retrieval Strategy
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`. It creates 384-dimensional dense vectors. It is highly optimized for semantic search and runs quickly on CPU.
- **Vector DB**: `faiss-cpu`. The index is persisted locally to `data/faiss_index` to avoid re-embedding on startup, which is crucial for fast cold-starts on platforms like Render or Railway.
- **Metadata Awareness**: The retrieval process combines semantic search with basic heuristic filtering. For instance, if the prompt asks for "personality", we can boost results that have "personality" in their category or description.
- **Hallucination Prevention**: If the top retrieval similarity score falls below a set threshold (`SIMILARITY_THRESHOLD = 0.3`), the system falls back to asking clarifying questions instead of blindly recommending a potentially mismatched assessment.

## 3. Prompt Design & Guardrails
The system uses specialized prompts for each intent type, injecting only the necessary context. 
- **Refusal Guardrails**: The LLM is explicitly instructed to refuse questions regarding legal advice, non-SHL topics, or prompt injection.
- **Strict Schema Enforcement**: The prompt mandates outputting only the JSON properties expected, and the service layer validates and cleans the output using Pydantic models. If the model hallucinates an assessment not in the retrieved context, the post-processing filter strips it out.

## 4. Evaluation Strategy
Testing is conducted via `pytest`. We cover:
- **Flow Tests**: Ensuring vague queries yield no recommendations, while specific ones yield 1-10 recommendations.
- **Guardrail Tests**: Sending known jailbreak phrases to ensure `recommendations=[]` and refusal language is returned.
- **Schema Validation**: Using Pydantic to ensure all mock API responses strictly match the prompt requirements.

## 5. Tradeoffs
- **Custom LLM Wrapper vs Langchain**: I chose a custom wrapper. *Tradeoff*: We lose some of Langchain's built-in memory management and tool calling, but gain a massive reduction in dependency weight, cold start times, and debugging complexity.
- **Local FAISS vs Cloud VectorDB**: I chose local FAISS. *Tradeoff*: deployment is simpler and completely free, but scaling horizontally requires each node to hold the index in memory.

## 6. What Did Not Work
- Relying on the LLM to output perfect JSON 100% of the time, especially smaller models like Llama 3 8B. *Solution*: We use regex extraction to pull the JSON block from the response and utilize Pydantic to repair or validate the structure, aggressively defaulting to a safe empty recommendation list if parsing fails.

## 7. AI Tools Used
- Google Gemini 1.5 Pro and Groq Llama 3 for text generation.
- HuggingFace `sentence-transformers` for embeddings.
