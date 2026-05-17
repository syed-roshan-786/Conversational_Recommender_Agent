import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# .env file is loaded automatically by Pydantic Settings if present.
# Render directly injects environment variables without a .env file.

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str
    LLM_MODEL_NAME: str
    
    VECTOR_DB_PATH: str = "data/faiss_index"
    CATALOG_PATH: str = "data/catalog.json"
    TOP_K_RETRIEVAL: int = 3
    SIMILARITY_THRESHOLD: float = 0.3

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

settings = Settings()

# Explicit Provider Validation
valid_providers = ["groq", "gemini"]
provider = settings.LLM_PROVIDER.lower()
if provider not in valid_providers:
    raise ValueError(f"CRITICAL STARTUP ERROR: Unsupported LLM_PROVIDER '{provider}'. Must be one of {valid_providers}.")

logger.info(f"Configuration Loaded Successfully. Provider: [{provider}], Model: [{settings.LLM_MODEL_NAME}]")
