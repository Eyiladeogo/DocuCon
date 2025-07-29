import uuid
import random
from typing import Dict, List, Optional


class MockVectorStore:
    """
    Simulates a vector database for storing document embeddings.
    Uses an in-memory dictionary.
    """

    _embeddings: Dict[str, List[float]] = {}  # {embedding_id: [vector_floats]}

    async def add_embedding(self, embedding_vector: List[float]) -> str:
        """
        Adds an embedding vector to the store and returns a unique ID.
        """
        embedding_id = str(uuid.uuid4())
        self._embeddings[embedding_id] = embedding_vector
        print(f"MockVectorStore: Added embedding with ID '{embedding_id}'.")
        return embedding_id

    async def get_embedding(self, embedding_id: str) -> Optional[List[float]]:
        """
        Retrieves an embedding vector by its ID.
        """
        embedding = self._embeddings.get(embedding_id)
        if embedding:
            print(f"MockVectorStore: Retrieved embedding with ID '{embedding_id}'.")
        else:
            print(f"MockVectorStore: Embedding with ID '{embedding_id}' not found.")
        return embedding

    async def delete_embedding(self, embedding_id: str) -> bool:
        """
        Deletes an embedding vector by its ID.
        """
        if embedding_id in self._embeddings:
            del self._embeddings[embedding_id]
            print(f"MockVectorStore: Deleted embedding with ID '{embedding_id}'.")
            return True
        print(
            f"MockVectorStore: Embedding with ID '{embedding_id}' not found for deletion."
        )
        return False

    async def generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generates a mock embedding vector for a given text.
        In a real application, this would use an actual embedding model (e.g., OpenAI, Sentence Transformers).
        """
        # Create a fixed-size vector of random floats for demonstration
        # The actual values don't matter for a mock, only the structure.
        embedding_size = (
            1536  # Common size for many models (e.g., OpenAI's text-embedding-ada-002)
        )
        print(
            f"MockVectorStore: Generating mock embedding for text (length {len(text)})."
        )
        return [random.uniform(-1, 1) for _ in range(embedding_size)]


# Instantiate the mock vector store
mock_vector_store = MockVectorStore()
