import json
import os
import faiss
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag.embeddings import embedding_model
from app.core.config import settings

def ingest_data():
    if not os.path.exists(settings.CATALOG_PATH):
        print(f"Error: Catalog file not found at {settings.CATALOG_PATH}")
        print("Please run scraper.py first, or ensure mock data exists.")
        return

    with open(settings.CATALOG_PATH, 'r') as f:
        data = json.load(f)

    if not data:
        print("Catalog is empty.")
        return

    print(f"Loaded {len(data)} items from catalog.")
    
    # Prepare text for embedding
    texts_to_embed = []
    for item in data:
        # Create a rich representation for embedding
        skills = ", ".join(item.get("skills_measured", []))
        keywords = ", ".join(item.get("keywords", []))
        text = f"{item['name']}. {item['description']}. Category: {item['category']}. Skills: {skills}. Keywords: {keywords}."
        texts_to_embed.append(text)

    print("Generating embeddings...")
    embeddings = embedding_model.encode(texts_to_embed)
    
    # Normalize for inner product (cosine similarity mapping to L2)
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    
    # Using Inner Product index. Since vectors are normalized, IP == Cosine Similarity
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    os.makedirs(os.path.dirname(settings.VECTOR_DB_PATH), exist_ok=True)
    faiss.write_index(index, settings.VECTOR_DB_PATH)
    print(f"Successfully created FAISS index at {settings.VECTOR_DB_PATH}")

if __name__ == "__main__":
    ingest_data()
