import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Lazily initialize the client based on the configured provider."""
        if self._client is not None:
            return self._client
            
        logger.info(f"Initializing {self.provider.upper()} client lazily...")
        
        if self.provider == "groq":
            if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
                raise ValueError("CRITICAL ERROR: GROQ_API_KEY is missing or invalid in .env")
            # Only import when needed
            from groq import Groq
            self._client = Groq(api_key=settings.GROQ_API_KEY)
            
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
                raise ValueError("CRITICAL ERROR: GEMINI_API_KEY is missing or invalid in .env")
            # Only import when needed
            from google import genai
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
            
        return self._client

    def generate(self, messages: list, json_mode: bool = False) -> str:
        """
        Generates a response from the chosen LLM provider.
        messages format: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        client = self._get_client()
        
        if self.provider == "groq":
            params = {
                "model": settings.LLM_MODEL_NAME,
                "messages": messages,
                "temperature": 0.1,
            }
            if json_mode:
                params["response_format"] = {"type": "json_object"}
                
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content

        elif self.provider == "gemini":
            # Gemini Python SDK doesn't directly map to OpenAI messages array easily
            system_instruction = ""
            contents = []
            from google.genai import types
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction += msg["content"] + "\n"
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
            
            config = types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=system_instruction if system_instruction else None
            )
            if json_mode:
                config.response_mime_type = "application/json"

            model_name = 'gemini-2.5-flash' if 'flash' in settings.LLM_MODEL_NAME.lower() else settings.LLM_MODEL_NAME
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            return response.text

llm_client = LLMClient()
