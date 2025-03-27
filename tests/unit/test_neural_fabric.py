"""
Unit Tests for Neural Data Fabric

This module tests the Neural Data Fabric components, including
vector database, knowledge graph, and event stream processing.
"""

import unittest
import os
import sys
import json
import datetime
import numpy as np
import uuid
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import neural fabric components
from neural_fabric.vector_db import VectorDatabase
from neural_fabric.knowledge_graph import KnowledgeGraph
from neural_fabric.event_processor import EventProcessor
from neural_fabric.embedding_service import EmbeddingService


class TestVectorDatabase(unittest.TestCase):
    """Test the vector database implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock embedding service
        self.embedding_service = MagicMock()
        self.embedding_service.embed_text.return_value = np.random.randn(384)
        
        # Create a vector database with mocked components
        self.vector_db = VectorDatabase(embedding_service=self.embedding_service)
        
        # Sample document
        self.sample_doc = {
            "id": "doc-1001",
            "title": "Neural Data Fabric Architecture",
            "content": "This document describes the architecture of the Neural Data Fabric component...",
            "metadata": {
                "author": "AI Systems Team",
                "date": "2025-03-15",
                "tags": ["architecture", "neural-fabric", "data-system"]
            }
        }
    
    def test_store_document(self):
        """Test storing a document in the vector database."""
        # Mock internal storage method
        self.vector_db._store_vector = MagicMock()
        
        # Store the document
        result = self.vector_db.store_document(
            document_id=self.sample_doc["id"],
            text=self.sample_doc["title"] + " " + self.sample_doc["content"],
            metadata=self.sample_doc["metadata"]
        )
        
        # Verify the embedding service was called
        self.embedding_service.embed_text.assert_called_once()
        
        # Verify the storage method was called
        self.vector_db._store_vector.assert_called_once()
        
        # Verify the result
        self.assertIn("id", result)
        self.assertEqual(result["id"], self.sample_doc["id"])
    
    def test_search(self):
        """Test semantic search in the vector database."""
        # Mock internal search method to return sample results
        mock_results = [
            {"id": "doc-1001", "score": 0.92, "metadata": self.sample_doc["metadata"]},
            {"id": "doc-1042", "score": 0.85, "metadata": {"author": "Data Team", "tags": ["architecture"]}},
            {"id": "doc-1053", "score": 0.78, "metadata": {"author": "Engineering", "tags": ["neural-fabric"]}}
        ]
        self.vector_db._search_vectors = MagicMock(return_value=mock_results)
        
        # Perform search
        query = "neural data architecture design"
        results = self.vector_db.search(query, limit=3)
        
        # Verify the embedding service was called
        self.embedding_service.embed_text.assert_called_once_with(query)
        
        # Verify the search method was called
        self.vector_db._search_vectors.assert_called_once()
        
        # Verify the results
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["id"], "doc-1001")
        self.assertEqual(results[0]["score"], 0.92)
    
    def test_filter_search(self):
        """Test filtered semantic search in the vector database."""
        # Mock internal search method to return sample results
        mock_results = [
            {"id": "doc-1001", "score": 0.92, "metadata": self.sample_doc["metadata"]},
        ]
        self.vector_db._search_vectors = MagicMock(return_value=mock_results)
        
        # Perform filtered search
        query = "neural data architecture design"
        filters = {
            "author": "AI Systems Team",
            "tags": ["architecture"]
        }
        results = self.vector_db.search(query, filters=filters, limit=3)
        
        # Verify the embedding service was called
        self.embedding_service.embed_text.assert_called_once_with(query)
        
        # Verify the search method was called with filters
        self.vector_db._search_vectors.assert_called_once()
        args, kwargs = self.vector_db._search_vectors.call_args
        self.assertIn("filters", kwargs)
        self.assertEqual(kwargs["filters"], filters)
        
        # Verify the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "doc-1001")
    
    def test_batch_store(self):
        """Test batch storing of documents."""
        # Mock internal storage method
        self.vector_db._store_vector = MagicMock()
        
        # Create batch of documents
        docs = [
            {
                "id": "doc-1001",
                "text": "Document one content",
                "metadata": {"author": "Author 1", "tags": ["tag1", "tag2"]}
            },
            {
                "id": "doc-1002",
                "text": "Document two content",
                "metadata": {"author": "Author 2", "tags": ["tag2", "tag3"]}
            },
            {
                "id": "doc-1003",
                "text": "Document three content",
                "metadata": {"author": "Author 3", "tags": ["tag1", "tag3"]}
            }
        ]
        
        # Batch store
        results = self.vector_db.batch_store_documents(docs)
        
        # Verify the embedding service was called for each document
        self.assertEqual(self.embedding_service.embed_text.call_count, 3)
        
        # Verify the storage method was called for each document
        self.assertEqual(self.vector_db._store_vector.call_count, 3)
        
        # Verify the results
        self.assertEqual(len(results), 3)
        self.assertIn("id", results[0])
    
    def test_delete_document(self):
        """Test deleting a document from the vector database."""
        # Mock internal delete method
        self.vector_db._delete_vector = MagicMock(return_value=True)
        
        # Delete a document
        result = self.vector_db.delete_document("doc-1001")
        
        # Verify the delete method was called
        self.vector_db._delete_vector.assert_called_once_with("doc-1001")
        
        # Verify the result
        self.assertTrue(result)
    
    def test_update_document(self):
        """Test updating a document in the vector database."""
        # Mock internal methods
        self.vector_db._delete_vector = MagicMock(return_value=True)
        self.vector_db._store_vector = MagicMock()
        
        # Update a document
        updated_doc = {
            "id": "doc-1001",
            "text": "Updated document content",
            "metadata": {"author": "Updated Author", "tags": ["updated", "tags"]}
        }
        
        result = self.vector_db.update_document(
            document_id=updated_doc["id"],
            text=updated_doc["text"],
            metadata=updated_doc["metadata"]
        )
        
        # Verify the methods were called
        self.vector_db._delete_vector.assert_called_once_with(updated_doc["id"])
        self.embedding_service.embed_text.assert_called_once_with(updated_doc["text"])
        self.vector_db._store_vector.assert_called_once()
        
        # Verify the result
        self.assertIn("id", result)
        self.assertEqual(result["id"], updated_doc["id"])


class TestKnowledgeGraph(unittest.TestCase):
    """Test the knowledge graph implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a knowledge graph
        self.knowledge_graph = KnowledgeGraph()
        
        # Sample entity and relationship data
        self.entities = [
            {
                "id": "entity-1001",
                "type": "person",
                "name": "John Smith",
                "properties": {
                    "title": "CEO",
                    "company": "Acme Corp",
                    "location": "New York"
                }
            },
            {
                "id": "entity-1002",
                "type": "company",
                "name": "Acme Corp",
                "properties": {
                    "industry": "Technology",
                    "founded": 2010,
                    "location": "New York"
                }
            },
            {
                "id": "entity-1003",
                "type": "product",
                "name": "Widget Pro",
                "properties": {
                    "category": "Software",
                    "release_date": "2024-01-15",
                    "price": 199.99
                }
            }
        ]
        
        self.relationships = [
            {
                "id": "rel-1001",
                "type": "works_at",
                "source": "entity-1001",
                "target": "entity-1002",
                "properties": {
                    "since": "2015-03-10",
                    "role": "Executive"
                }
            },
            {
                "id": "rel-1002",
                "type": "manufactures",
                "source": "entity-1002",
                "target": "entity-1003",
                "properties": {
                    "since": "2024-01-15",
                    "units_sold": 5000
                }
            }
        ]
    
    def test_add_entity(self):
        """Test adding an entity to the knowledge graph."""
        # Mock internal storage method
        self.knowledge_graph._store_entity = MagicMock(return_value=self.entities[0]["id"])
        
        # Add an entity
        result = self.knowledge_graph.add_entity(self.entities[0])
        
        # Verify the storage method was called
        self.knowledge_graph._store_entity.assert_called_once_with(self.entities[0])
        
        # Verify the result
        self.assertIn("id", result)
        self.assertEqual(result["id"], self.entities[0]["id"])
    
    def test_add_relationship(self):
        """Test adding a relationship to the knowledge graph."""
        # Mock internal methods
        self.knowledge_graph._validate_relationship = MagicMock(return_value=True)
        self.knowledge_graph._store_relationship = MagicMock(return_value=self.relationships[0]["id"])
        
        # Add a relationship
        result = self.knowledge_graph.add_relationship(self.relationships[0])
        
        # Verify the methods were called
        self.knowledge_graph._validate_relationship.assert_called_once_with(self.relationships[0])
        self.knowledge_graph._store_relationship.assert_called_once_with(self.relationships[0])
        
        # Verify the result
        self.assertIn("id", result)
        self.assertEqual(result["id"], self.relationships[0]["id"])
    
    def test_get_entity(self):
        """Test retrieving an entity from the knowledge graph."""
        # Mock internal retrieval method
        self.knowledge_graph._get_entity = MagicMock(return_value=self.entities[0])
        
        # Get an entity
        result = self.knowledge_graph.get_entity(self.entities[0]["id"])
        
        # Verify the retrieval method was called
        self.knowledge_graph._get_entity.assert_called_once_with(self.entities[0]["id"])
        
        # Verify the result
        self.assertEqual(result["id"], self.entities[0]["id"])
        self.assertEqual(result["type"], "person")
        self.assertEqual(result["name"], "John Smith")
    
    def test_get_relationships(self):
        """Test retrieving relationships from the knowledge graph."""
        # Mock internal retrieval method
        self.knowledge_graph._get_relationships = MagicMock(return_value=[self.relationships[0]])
        
        # Get relationships for an entity
        result = self.knowledge_graph.get_relationships(
            entity_id=self.entities[0]["id"],
            relationship_type="works_at",
            direction="outgoing"
        )
        
        # Verify the retrieval method was called
        self.knowledge_graph._get_relationships.assert_called_once()
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], self.relationships[0]["id"])
        self.assertEqual(result[0]["type"], "works_at")
    
    def test_query_graph(self):
        """Test querying the knowledge graph."""
        # Mock internal query method
        query_result = {
            "entities": [self.entities[0], self.entities[1]],
            "relationships": [self.relationships[0]]
        }
        self.knowledge_graph._execute_query = MagicMock(return_value=query_result)
        
        # Execute a query
        query = """
        MATCH (p:person)-[r:works_at]->(c:company)
        WHERE c.name = 'Acme Corp'
        RETURN p, r, c
        """
        
        result = self.knowledge_graph.query(query)
        
        # Verify the query method was called
        self.knowledge_graph._execute_query.assert_called_once_with(query)
        
        # Verify the result
        self.assertIn("entities", result)
        self.assertIn("relationships", result)
        self.assertEqual(len(result["entities"]), 2)
        self.assertEqual(len(result["relationships"]), 1)
    
    def test_update_entity(self):
        """Test updating an entity in the knowledge graph."""
        # Mock internal methods
        self.knowledge_graph._get_entity = MagicMock(return_value=self.entities[0])
        self.knowledge_graph._update_entity = MagicMock(return_value=True)
        
        # Update properties
        updated_properties = {
            "title": "President",
            "location": "San Francisco"
        }
        
        result = self.knowledge_graph.update_entity(
            entity_id=self.entities[0]["id"],
            properties=updated_properties
        )
        
        # Verify the methods were called
        self.knowledge_graph._get_entity.assert_called_once_with(self.entities[0]["id"])
        self.knowledge_graph._update_entity.assert_called_once()
        
        # Verify the result
        self.assertTrue(result)
    
    def test_delete_entity(self):
        """Test deleting an entity from the knowledge graph."""
        # Mock internal methods
        self.knowledge_graph._get_relationships = MagicMock(return_value=[])
        self.knowledge_graph._delete_entity = MagicMock(return_value=True)
        
        # Delete an entity
        result = self.knowledge_graph.delete_entity(self.entities[0]["id"])
        
        # Verify the methods were called
        self.knowledge_graph._get_relationships.assert_called_once()
        self.knowledge_graph._delete_entity.assert_called_once_with(self.entities[0]["id"])
        
        # Verify the result
        self.assertTrue(result)
    
    def test_delete_relationship(self):
        """Test deleting a relationship from the knowledge graph."""
        # Mock internal method
        self.knowledge_graph._delete_relationship = MagicMock(return_value=True)
        
        # Delete a relationship
        result = self.knowledge_graph.delete_relationship(self.relationships[0]["id"])
        
        # Verify the method was called
        self.knowledge_graph._delete_relationship.assert_called_once_with(self.relationships[0]["id"])
        
        # Verify the result
        self.assertTrue(result)


class TestEventProcessor(unittest.TestCase):
    """Test the event processor implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a vector database mock (for event storage)
        self.vector_db = MagicMock()
        
        # Create an event processor
        self.event_processor = EventProcessor(vector_db=self.vector_db)
        
        # Sample events
        self.events = [
            {
                "id": "event-1001",
                "type": "order_placed",
                "timestamp": "2025-03-15T10:30:00Z",
                "source": "e-commerce",
                "data": {
                    "order_id": "O-12345",
                    "customer_id": "C-5001",
                    "items": [
                        {"product_id": "P-101", "quantity": 2, "price": 129.99},
                        {"product_id": "P-205", "quantity": 1, "price": 89.99}
                    ],
                    "total": 349.97
                },
                "metadata": {
                    "region": "North America",
                    "channel": "web",
                    "user_agent": "Mozilla/5.0..."
                }
            },
            {
                "id": "event-1002",
                "type": "payment_processed",
                "timestamp": "2025-03-15T10:32:15Z",
                "source": "payment-gateway",
                "data": {
                    "order_id": "O-12345",
                    "payment_id": "PMT-98765",
                    "amount": 349.97,
                    "currency": "USD",
                    "method": "credit_card",
                    "status": "approved"
                },
                "metadata": {
                    "region": "North America",
                    "gateway": "stripe"
                }
            }
        ]
    
    def test_process_event(self):
        """Test processing an individual event."""
        # Mock vector DB store method
        self.vector_db.store_document = MagicMock(return_value={"id": self.events[0]["id"]})
        
        # Process an event
        result = self.event_processor.process_event(self.events[0])
        
        # Verify the vector DB store method was called
        self.vector_db.store_document.assert_called_once()
        
        # Verify result
        self.assertIn("id", result)
        self.assertEqual(result["id"], self.events[0]["id"])
    
    def test_batch_process_events(self):
        """Test batch processing of events."""
        # Mock vector DB batch store method
        self.vector_db.batch_store_documents = MagicMock(return_value=[
            {"id": self.events[0]["id"]},
            {"id": self.events[1]["id"]}
        ])
        
        # Batch process events
        results = self.event_processor.batch_process_events(self.events)
        
        # Verify the vector DB batch store method was called
        self.vector_db.batch_store_documents.assert_called_once()
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], self.events[0]["id"])
        self.assertEqual(results[1]["id"], self.events[1]["id"])
    
    def test_query_events(self):
        """Test querying events."""
        # Mock vector DB search method
        mock_results = [
            {"id": self.events[0]["id"], "score": 0.95, "document": self.events[0]},
            {"id": self.events[1]["id"], "score": 0.85, "document": self.events[1]}
        ]
        self.vector_db.search = MagicMock(return_value=mock_results)
        
        # Query events
        query = {
            "type": "order_placed",
            "time_range": {
                "start": "2025-03-15T00:00:00Z",
                "end": "2025-03-16T00:00:00Z"
            },
            "filters": {
                "metadata.region": "North America"
            }
        }
        
        results = self.event_processor.query_events(query)
        
        # Verify the vector DB search method was called
        self.vector_db.search.assert_called_once()
        
        # Verify results
        self.assertIn("events", results)
        self.assertEqual(len(results["events"]), 2)
    
    def test_get_event_by_id(self):
        """Test retrieving an event by ID."""
        # Mock vector DB get document method
        self.vector_db.get_document = MagicMock(return_value=self.events[0])
        
        # Get event by ID
        result = self.event_processor.get_event_by_id(self.events[0]["id"])
        
        # Verify the vector DB get document method was called
        self.vector_db.get_document.assert_called_once_with(self.events[0]["id"])
        
        # Verify result
        self.assertEqual(result["id"], self.events[0]["id"])
        self.assertEqual(result["type"], "order_placed")
    
    def test_get_events_by_relation(self):
        """Test retrieving related events."""
        # Mock vector DB search method
        mock_results = [
            {"id": self.events[1]["id"], "score": 1.0, "document": self.events[1]}
        ]
        self.vector_db.search = MagicMock(return_value=mock_results)
        
        # Get related events
        relation_field = "data.order_id"
        relation_value = "O-12345"
        
        results = self.event_processor.get_events_by_relation(
            relation_field=relation_field,
            relation_value=relation_value
        )
        
        # Verify the vector DB search method was called
        self.vector_db.search.assert_called_once()
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.events[1]["id"])


class TestEmbeddingService(unittest.TestCase):
    """Test the embedding service implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create an embedding service with a mock model
        with patch('neural_fabric.embedding_service.ModelRegistry') as mock_registry:
            # Create a mock model that returns random embeddings
            mock_model = MagicMock()
            mock_model.embed_text = MagicMock(
                side_effect=lambda text: np.random.randn(384).astype(np.float32)
            )
            
            # Make the registry return our mock model
            mock_registry_instance = mock_registry.return_value
            mock_registry_instance.get_model.return_value = mock_model
            
            # Create the embedding service
            self.embedding_service = EmbeddingService(model_name="test-embedding-model")
    
    def test_embed_text(self):
        """Test text embedding generation."""
        # Test text
        text = "This is a sample text for embedding generation."
        
        # Generate embedding
        embedding = self.embedding_service.embed_text(text)
        
        # Verify the embedding
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape, (384,))
        self.assertEqual(embedding.dtype, np.float32)
    
    def test_batch_embed_texts(self):
        """Test batch text embedding generation."""
        # Test texts
        texts = [
            "This is the first sample text.",
            "This is the second sample text.",
            "This is the third sample text."
        ]
        
        # Generate batch embeddings
        embeddings = self.embedding_service.batch_embed_texts(texts)
        
        # Verify the embeddings
        self.assertIsInstance(embeddings, list)
        self.assertEqual(len(embeddings), 3)
        for embedding in embeddings:
            self.assertIsInstance(embedding, np.ndarray)
            self.assertEqual(embedding.shape, (384,))
    
    def test_embed_sparse(self):
        """Test sparse embedding generation."""
        # Test text
        text = "This is a sample text for sparse embedding generation."
        
        # Generate sparse embedding
        embedding = self.embedding_service.embed_sparse(text)
        
        # Verify the embedding (sparse embeddings have different properties)
        self.assertIsInstance(embedding, dict)
        self.assertIn("indices", embedding)
        self.assertIn("values", embedding)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        # Create two random embeddings
        embedding1 = np.random.randn(384).astype(np.float32)
        embedding2 = np.random.randn(384).astype(np.float32)
        
        # Calculate similarity
        similarity = self.embedding_service.cosine_similarity(embedding1, embedding2)
        
        # Verify the similarity
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, -1.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_embed_document(self):
        """Test document embedding generation."""
        # Test document
        document = {
            "title": "Test Document",
            "content": "This is the content of the test document.",
            "metadata": {
                "author": "Test Author",
                "tags": ["test", "document", "embedding"]
            }
        }
        
        # Generate document embedding
        embedding = self.embedding_service.embed_document(
            title=document["title"],
            content=document["content"],
            metadata=document["metadata"]
        )
        
        # Verify the embedding
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape, (384,))


if __name__ == '__main__':
    unittest.main()