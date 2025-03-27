import os
import weaviate
from typing import Dict, Any, List, Optional

class VectorStore:
    """Vector database interface for semantic data storage"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.environ.get("VECTOR_DB_HOST", "localhost")
        self.port = port or int(os.environ.get("VECTOR_DB_PORT", "8080"))
        self.client = weaviate.Client(f"http://{self.host}:{self.port}")
        
    def create_schema(self, class_name: str, properties: List[Dict[str, Any]]):
        """Create a schema class for storing vectors"""
        class_obj = {
            "class": class_name,
            "vectorizer": "none",  # We'll provide our own vectors
            "properties": properties
        }
        
        self.client.schema.create_class(class_obj)
        
    def add_data(self, class_name: str, data: Dict[str, Any], vector: List[float]):
        """Add data with its vector representation"""
        return self.client.data_object.create(
            class_name=class_name,
            data_object=data,
            vector=vector
        )
        
    def semantic_search(self, class_name: str, vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for semantically similar data"""
        result = (
            self.client.query
            .get(class_name, ["id", "data"])
            .with_near_vector({"vector": vector})
            .with_limit(limit)
            .do()
        )
        
        return result["data"]["Get"][class_name]
        
    def delete_data(self, class_name: str, uuid: str):
        """Delete data by UUID"""
        self.client.data_object.delete(uuid, class_name)