from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self):
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Could not load embedding model: {e}")

    def embed(self, text: str) -> list[float]:
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            vector = self.model.encode(text)
            return vector.tolist()
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise RuntimeError(f"Embedding failed: {e}")

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        try:
            if not texts:
                raise ValueError("Texts list cannot be empty")
            texts = [t for t in texts if t and t.strip()]
            if not texts:
                raise ValueError("All texts were empty after filtering")
            vectors = self.model.encode(texts, show_progress_bar=True)
            return vectors.tolist()
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise RuntimeError(f"Batch embedding failed: {e}")