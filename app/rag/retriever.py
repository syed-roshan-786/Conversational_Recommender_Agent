import os
import json
import faiss
import numpy as np
from app.rag.embeddings import embedding_model
from app.core.config import settings
from app.models.schemas import CatalogItem

class Retriever:
    def __init__(self):
        self.index = None
        self.catalog = []
        self._load_data()

    def _load_data(self):
        if not os.path.exists(settings.CATALOG_PATH):
            print(f"Warning: Catalog file not found at {settings.CATALOG_PATH}")
            return
            
        with open(settings.CATALOG_PATH, 'r') as f:
            data = json.load(f)
            self.catalog = [CatalogItem(**item) for item in data]

        if os.path.exists(settings.VECTOR_DB_PATH):
            self.index = faiss.read_index(settings.VECTOR_DB_PATH)
        else:
            print("Warning: FAISS index not found. Run ingest.py.")

    def search(self, query: str, top_k: int = None) -> list[tuple[CatalogItem, float]]:
        if self.index is None or not self.catalog:
            return []

        if top_k is None:
            top_k = settings.TOP_K_RETRIEVAL

        query_vector = embedding_model.encode([query])
        faiss.normalize_L2(query_vector) 
        
        # Search returns Inner Product (Cosine Similarity because of L2 normalization)
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                # Dist is already cosine similarity (-1 to 1)
                similarity = float(dist)
                results.append((self.catalog[idx], similarity))

        return results

    def format_context(self, items: list[CatalogItem]) -> str:
        if not items:
            return "No relevant catalog items found."
        context_parts = []
        for item in items:
            skills = ", ".join(item.skills_measured)
            context_parts.append(
                f"Name: {item.name}\n"
                f"URL: {item.url}\n"
                f"Description: {item.description}\n"
                f"Category: {item.category}\n"
                f"Skills: {skills}\n"
                f"Test Type: {item.test_type}\n"
            )
        return "\n---\n".join(context_parts)

    def get_item_by_url(self, url: str) -> CatalogItem | None:
        """Strict validation helper to prevent hallucinations."""
        for item in self.catalog:
            if item.url == url:
                return item
        return None

retriever = Retriever()
