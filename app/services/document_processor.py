from typing import List, Tuple


class DocumentProcessor:
    """
    Handles document processing for AI context, including text extraction and chunking.
    """

    async def extract_text(self, document_content: str) -> str:
        """
        Simulates text extraction from a document.
        For this mock, it simply returns the provided content.
        In a real application, this would involve parsing PDFs, DOCX, etc.
        """
        # Simulate some processing time
        # await asyncio.sleep(0.1)
        print("DocumentProcessor: Text extraction simulated.")
        return document_content

    async def chunk_text(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        """
        Splits text into smaller chunks with optional overlap.
        This is a simple character-based chunking.
        In a real application, more sophisticated methods (e.g., NLTK, spaCy, LangChain text splitters)
        would be used to respect sentence/paragraph boundaries.
        """
        if not text:
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
            if (
                start < 0
            ):  # Handle cases where overlap is larger than chunk size (shouldn't happen with positive values)
                start = 0
        print(f"DocumentProcessor: Text chunked into {len(chunks)} parts.")
        return chunks


# Instantiate the processor
document_processor = DocumentProcessor()
