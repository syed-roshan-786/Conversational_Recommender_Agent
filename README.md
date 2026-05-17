# SHL Assessment Recommender Agent

A conversational AI agent built with FastAPI and RAG, designed to recommend SHL assessments based on a scraped catalog. It handles vagueness, recommendations, refinements, and comparisons, all while strictly adhering to SHL boundaries and security guardrails.

## Features
- **Stateless API**: Complies with the exact schema requirements for `/health` and `/chat`.
- **Lightweight RAG**: Uses `sentence-transformers/all-MiniLM-L6-v2` and FAISS for fast local retrieval.
- **Intent Router**: intelligently routes between Clarification, Recommendation, Refinement, Comparison, and Refusal based on conversation context.
- **Configurable LLM**: Supports Groq (Llama 3/Gemma) and Gemini Flash for free, low-latency generation.
- **Security**: Guardrails against prompt injections, jailbreaks, and out-of-scope requests.

## Architecture
```
app/
├── api/          # FastAPI routes
├── core/         # Config & LLM client wrapper
├── models/       # Pydantic schemas
├── prompts/      # Prompt templates and logic
├── rag/          # Embedding & FAISS vector store
├── services/     # Chat orchestrator and intent routing
├── utils/        # Helper functions
└── main.py       # App entry point
```

## Setup Instructions

1. **Clone and create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY or GEMINI_API_KEY
   ```

4. **Data Ingestion (Optional, pre-mocked data is included):**
   ```bash
   # 1. Scrape catalog (if needed)
   python scripts/scraper.py
   # 2. Ingest and build FAISS index
   python scripts/ingest.py
   ```

5. **Run the Application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Usage

### Health Check
```bash
curl -X GET http://127.0.0.1:8000/health
```

### Chat Endpoint
```bash
curl -X POST http://127.0.0.1:8000/chat \
-H "Content-Type: application/json" \
-d '{"messages": [{"role": "user", "content": "I am hiring a Java developer"}]}'
```

## Deployment

The application is containerized and optimized for Render or Railway free tiers.
1. Connect your GitHub repo to Render/Railway.
2. Select Docker as the environment.
3. Provide the `GROQ_API_KEY` in the environment variables settings.
4. Deploy!

## Limitations & Future Improvements
- **Limitations**: The scraper relies on standard HTML structures. If SHL significantly changes their website layout, `scripts/scraper.py` will need updates. Local FAISS index is read-only in production; updates require rebuilding the index and redeploying.
- **Improvements**: Integration with a proper cloud VectorDB (like Pinecone or hosted Chroma) for real-time catalog syncing without redeployments. Expanded evaluation metrics.
