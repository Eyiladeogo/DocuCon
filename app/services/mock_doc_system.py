import uuid
from typing import Dict, Any, Optional


class MockDocumentSystem:
    """
    Simulates an external document management system API.
    Stores documents in memory.
    """

    _documents: Dict[str, Dict[str, Any]] = {}  # {mock_system_id: {title, content}}

    async def upload_document(self, title: str, content: str) -> Dict[str, Any]:
        """
        Simulates uploading a document to the external system.
        Generates a unique mock_system_id.
        """
        mock_system_id = str(uuid.uuid4())
        self._documents[mock_system_id] = {
            "title": title,
            "content": content,
            "mock_system_id": mock_system_id,
        }
        print(f"MockDocSystem: Document '{title}' uploaded with ID '{mock_system_id}'")
        return self._documents[mock_system_id]

    async def get_document_content(self, mock_system_id: str) -> Optional[str]:
        """
        Simulates retrieving document content from the external system.
        """
        doc = self._documents.get(mock_system_id)
        if doc:
            print(f"MockDocSystem: Content for ID '{mock_system_id}' retrieved.")
            return doc["content"]
        print(f"MockDocSystem: Document with ID '{mock_system_id}' not found.")
        return None

    async def delete_document(self, mock_system_id: str) -> bool:
        """
        Simulates deleting a document from the external system.
        """
        if mock_system_id in self._documents:
            del self._documents[mock_system_id]
            print(f"MockDocSystem: Document with ID '{mock_system_id}' deleted.")
            return True
        print(
            f"MockDocSystem: Document with ID '{mock_system_id}' not found for deletion."
        )
        return False


# Instantiate the mock system
mock_document_system = MockDocumentSystem()
