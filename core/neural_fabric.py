"""
Neural Fabric for NeuroERP.

This module implements the "neural fabric" - a self-organizing data layer that combines 
knowledge graphs, vector embeddings, and semantic connections to provide an AI-native 
alternative to traditional relational databases.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Set, Callable
import json
import hashlib

from .config import Config
from .event_bus import EventBus, Event

logger = logging.getLogger(__name__)

class NeuralNode:
    """A node in the neural fabric representing a piece of information."""
    
    def __init__(self, 
                 node_type: str,
                 properties: Dict[str, Any],
                 id: Optional[str] = None,
                 vector: Optional[List[float]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a neural node.
        
        Args:
            node_type: Type of node (e.g., 'customer', 'invoice', 'product')
            properties: Node properties/attributes
            id: Unique node ID (generated if not provided)
            vector: Vector embedding representing node semantics
            metadata: Additional metadata about the node
        """
        self.id = id or str(uuid.uuid4())
        self.node_type = node_type
        self.properties = properties.copy()
        self.vector = vector.copy() if vector else None
        self.metadata = metadata.copy() if metadata else {}
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.connections: Dict[str, Set[str]] = {}  # Relationship type -> Set of node IDs
    
    def add_connection(self, relation_type: str, target_node_id: str):
        """Add a connection to another node.
        
        Args:
            relation_type: Type of relationship
            target_node_id: ID of the node to connect to
        """
        if relation_type not in self.connections:
            self.connections[relation_type] = set()
        
        self.connections[relation_type].add(target_node_id)
        self.updated_at = time.time()
    
    def remove_connection(self, relation_type: str, target_node_id: str) -> bool:
        """Remove a connection to another node.
        
        Args:
            relation_type: Type of relationship
            target_node_id: ID of the node to disconnect from
            
        Returns:
            True if the connection was removed, False otherwise
        """
        if relation_type not in self.connections:
            return False
        
        if target_node_id not in self.connections[relation_type]:
            return False
        
        self.connections[relation_type].remove(target_node_id)
        
        # Clean up empty connection sets
        if not self.connections[relation_type]:
            del self.connections[relation_type]
            
        self.updated_at = time.time()
        return True
    
    def update_properties(self, properties: Dict[str, Any]):
        """Update node properties.
        
        Args:
            properties: New properties to merge with existing ones
        """
        self.properties.update(properties)
        self.updated_at = time.time()
    
    def set_vector(self, vector: List[float]):
        """Set the vector embedding for this node.
        
        Args:
            vector: Vector embedding
        """
        self.vector = vector.copy()
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "node_type": self.node_type,
            "properties": self.properties,
            "vector": self.vector,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "connections": {
                rel_type: list(node_ids)
                for rel_type, node_ids in self.connections.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NeuralNode':
        """Create node from dictionary representation."""
        node = cls(
            id=data["id"],
            node_type=data["node_type"],
            properties=data["properties"],
            vector=data["vector"],
            metadata=data["metadata"]
        )
        node.created_at = data["created_at"]
        node.updated_at = data["updated_at"]
        
        # Restore connections
        for rel_type, node_ids in data.get("connections", {}).items():
            node.connections[rel_type] = set(node_ids)
            
        return node


class NeuralFabric:
    """Self-organizing data layer combining graph and vector representations."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one neural fabric exists."""
        if cls._instance is None:
            cls._instance = super(NeuralFabric, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, vector_store=None, embedding_function=None):
        """Initialize the neural fabric.
        
        Args:
            vector_store: Optional external vector store client
            embedding_function: Function to generate embeddings for nodes
        """
        # Skip if already initialized (singleton pattern)
        if self._initialized:
            return
            
        self._config = Config()
        self._event_bus = EventBus()
        
        # In-memory storage for nodes and indices
        self._nodes: Dict[str, NeuralNode] = {}
        self._node_type_index: Dict[str, Set[str]] = {}  # node_type -> Set of node IDs
        self._property_index: Dict[str, Dict[Any, Set[str]]] = {}  # prop_name -> value -> Set of node IDs
        
        # External integrations
        self._vector_store = vector_store
        self._embedding_function = embedding_function
        
        # Node change tracking for vector updates
        self._nodes_pending_embedding: Set[str] = set()
        
        # Statistics
        self._statistics = {
            "node_count": 0,
            "connection_count": 0,
            "query_count": 0
        }
        
        # Subscribe to auto-embedding events if embedding function available
        self._enable_auto_embedding()
        
        self._initialized = True
        logger.info("Neural fabric initialized")
    
    def _enable_auto_embedding(self):
        """Set up automatic embedding generation for nodes."""
        if self._embedding_function:
            # Create event handler for node creation/updates
            def handle_node_change(event: Event):
                node_id = event.payload.get("node_id")
                if node_id and node_id in self._nodes:
                    self._nodes_pending_embedding.add(node_id)
            
            # Subscribe to node events
            self._event_bus.subscribe("node.created", handle_node_change)
            self._event_bus.subscribe("node.updated", handle_node_change)
            
            # Start background thread for embedding processing
            import threading
            embedding_thread = threading.Thread(
                target=self._embedding_worker,
                name="embedding-worker",
                daemon=True
            )
            embedding_thread.start()
    
    def _embedding_worker(self):
        """Background worker to process nodes needing embeddings."""
        while True:
            try:
                # Process a batch of nodes needing embeddings
                batch_size = 16  # Process reasonable batches
                batch = set()
                
                # Get a batch of nodes
                while len(batch) < batch_size and self._nodes_pending_embedding:
                    try:
                        node_id = self._nodes_pending_embedding.pop()
                        batch.add(node_id)
                    except KeyError:
                        break
                
                if not batch:
                    # Sleep if no work to do
                    time.sleep(1)
                    continue
                
                self._process_embedding_batch(batch)
            except Exception as e:
                logger.error(f"Error in embedding worker: {e}", exc_info=True)
                time.sleep(5)  # Back off on error
    
    def _process_embedding_batch(self, node_ids: Set[str]):
        """Generate embeddings for a batch of nodes.
        
        Args:
            node_ids: Set of node IDs to process
        """
        nodes_to_embed = []
        
        # Collect valid nodes
        for node_id in node_ids:
            if node_id in self._nodes:
                nodes_to_embed.append(self._nodes[node_id])
        
        if not nodes_to_embed:
            return
            
        try:
            # Extract text representations for embedding
            texts = []
            for node in nodes_to_embed:
                # Create a text representation of the node
                text = f"{node.node_type}: "
                
                # Add property values
                for key, value in node.properties.items():
                    if isinstance(value, (str, int, float, bool)):
                        text += f"{key}={value} "
                
                texts.append(text)
            
            # Generate embeddings
            embeddings = self._embedding_function(texts)
            
            # Update nodes with embeddings
            for i, node in enumerate(nodes_to_embed):
                node.set_vector(embeddings[i])
                
                # Update vector store if available
                if self._vector_store:
                    self._vector_store.upsert_vector(node.id, embeddings[i], node.to_dict())
                    
            logger.debug(f"Generated embeddings for {len(nodes_to_embed)} nodes")
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            
            # Put nodes back in queue for retry
            for node in nodes_to_embed:
                self._nodes_pending_embedding.add(node.id)
    
    def create_node(self, 
                   node_type: str,
                   properties: Dict[str, Any],
                   id: Optional[str] = None,
                   generate_embedding: bool = True) -> str:
        """Create a new node in the neural fabric.
        
        Args:
            node_type: Type of node
            properties: Node properties
            id: Optional node ID (generated if not provided)
            generate_embedding: Whether to generate embedding
            
        Returns:
            Node ID
        """
        # Create node
        node = NeuralNode(
            node_type=node_type,
            properties=properties,
            id=id
        )
        
        # Add to storage
        self._nodes[node.id] = node
        
        # Update indices
        if node_type not in self._node_type_index:
            self._node_type_index[node_type] = set()
        self._node_type_index[node_type].add(node.id)
        
        # Index properties
        for prop_name, prop_value in properties.items():
            # Only index simple properties (strings, numbers, booleans)
            if isinstance(prop_value, (str, int, float, bool)):
                if prop_name not in self._property_index:
                    self._property_index[prop_name] = {}
                
                if prop_value not in self._property_index[prop_name]:
                    self._property_index[prop_name][prop_value] = set()
                
                self._property_index[prop_name][prop_value].add(node.id)
        
        # Update statistics
        self._statistics["node_count"] += 1
        
        # Queue for embedding if requested
        if generate_embedding and self._embedding_function:
            self._nodes_pending_embedding.add(node.id)
        
        # Publish event
        self._event_bus.publish(
            event_type="node.created",
            payload={
                "node_id": node.id,
                "node_type": node_type
            }
        )
        
        logger.debug(f"Created node {node.id} of type '{node_type}'")
        return node.id
    
    def get_node(self, node_id: str) -> Optional[NeuralNode]:
        """Get a node by ID.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Node if found, None otherwise
        """
        return self._nodes.get(node_id)
    
    def update_node(self, 
                   node_id: str,
                   properties: Dict[str, Any],
                   generate_embedding: bool = True) -> bool:
        """Update a node's properties.
        
        Args:
            node_id: ID of the node
            properties: New properties to merge
            generate_embedding: Whether to generate new embedding
            
        Returns:
            True if node was updated, False if not found
        """
        if node_id not in self._nodes:
            return False
            
        node = self._nodes[node_id]
        old_properties = node.properties.copy()
        
        # Update node properties
        node.update_properties(properties)
        
        # Update indices for changed properties
        for prop_name, prop_value in properties.items():
            # Remove from old index if property changed
            if prop_name in old_properties:
                old_value = old_properties[prop_name]
                if isinstance(old_value, (str, int, float, bool)):
                    if prop_name in self._property_index and old_value in self._property_index[prop_name]:
                        self._property_index[prop_name][old_value].discard(node_id)
            
            # Add to new index
            if isinstance(prop_value, (str, int, float, bool)):
                if prop_name not in self._property_index:
                    self._property_index[prop_name] = {}
                
                if prop_value not in self._property_index[prop_name]:
                    self._property_index[prop_name][prop_value] = set()
                
                self._property_index[prop_name][prop_value].add(node_id)
        
        # Queue for embedding if requested
        if generate_embedding and self._embedding_function:
            self._nodes_pending_embedding.add(node_id)
        
        # Publish event
        self._event_bus.publish(
            event_type="node.updated",
            payload={
                "node_id": node_id,
                "node_type": node.node_type
            }
        )
        
        logger.debug(f"Updated node {node_id}")
        return True
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            True if node was deleted, False if not found
        """
        if node_id not in self._nodes:
            return False
            
        node = self._nodes[node_id]
        
        # Remove from type index
        if node.node_type in self._node_type_index:
            self._node_type_index[node.node_type].discard(node_id)
            
            # Clean up empty sets
            if not self._node_type_index[node.node_type]:
                del self._node_type_index[node.node_type]
        
        # Remove from property indices
        for prop_name, prop_value in node.properties.items():
            if isinstance(prop_value, (str, int, float, bool)):
                if prop_name in self._property_index and prop_value in self._property_index[prop_name]:
                    self._property_index[prop_name][prop_value].discard(node_id)
                    
                    # Clean up empty sets
                    if not self._property_index[prop_name][prop_value]:
                        del self._property_index[prop_name][prop_value]
                        
                    if not self._property_index[prop_name]:
                        del self._property_index[prop_name]
        
        # Remove from main storage
        del self._nodes[node_id]
        
        # Remove from embedding queue if present
        self._nodes_pending_embedding.discard(node_id)
        
        # Update statistics
        self._statistics["node_count"] -= 1
        
        # Publish event
        self._event_bus.publish(
            event_type="node.deleted",
            payload={
                "node_id": node_id,
                "node_type": node.node_type
            }
        )
        
        logger.debug(f"Deleted node {node_id}")
        return True
    
    def connect_nodes(self, 
                     source_id: str,
                     target_id: str,
                     relation_type: str) -> bool:
        """Connect two nodes with a relationship.
        
        Args:
            source_id: ID of source node
            target_id: ID of target node
            relation_type: Type of relationship
            
        Returns:
            True if connection was created, False otherwise
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return False
            
        source_node = self._nodes[source_id]
        target_node = self._nodes[target_id]
        
        # Create bidirectional connection
        source_node.add_connection(relation_type, target_id)
        
        # Create inverse relationship if not a self-connection
        if source_id != target_id:
            inverse_relation = f"{relation_type}_inverse"
            target_node.add_connection(inverse_relation, source_id)
        
        # Update statistics
        self._statistics["connection_count"] += 1
        
        # Publish event
        self._event_bus.publish(
            event_type="connection.created",
            payload={
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": relation_type
            }
        )
        
        logger.debug(f"Connected node {source_id} to {target_id} with relation '{relation_type}'")
        return True
    
    def disconnect_nodes(self,
                        source_id: str,
                        target_id: str,
                        relation_type: str) -> bool:
        """Remove a connection between nodes.
        
        Args:
            source_id: ID of source node
            target_id: ID of target node
            relation_type: Type of relationship
            
        Returns:
            True if connection was removed, False otherwise
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return False
            
        source_node = self._nodes[source_id]
        target_node = self._nodes[target_id]
        
        # Remove connection in source node
        source_removed = source_node.remove_connection(relation_type, target_id)
        
        # Remove inverse relationship
        if source_id != target_id:
            inverse_relation = f"{relation_type}_inverse"
            target_node.remove_connection(inverse_relation, source_id)
        
        if source_removed:
            # Update statistics
            self._statistics["connection_count"] -= 1
            
            # Publish event
            self._event_bus.publish(
                event_type="connection.deleted",
                payload={
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": relation_type
                }
            )
            
            logger.debug(f"Disconnected node {source_id} from {target_id} with relation '{relation_type}'")
            
        return source_removed
    
    def get_connected_nodes(self,
                           node_id: str,
                           relation_type: Optional[str] = None) -> Dict[str, List[NeuralNode]]:
        """Get nodes connected to a given node.
        
        Args:
            node_id: ID of the node
            relation_type: Optional filter for relationship type
            
        Returns:
            Dictionary mapping relation types to lists of connected nodes
        """
        if node_id not in self._nodes:
            return {}
            
        node = self._nodes[node_id]
        result = {}
        
        # Filter by relation type if provided
        relation_types = [relation_type] if relation_type else node.connections.keys()
        
        for rel_type in relation_types:
            if rel_type in node.connections:
                result[rel_type] = []
                for connected_id in node.connections[rel_type]:
                    if connected_id in self._nodes:
                        result[rel_type].append(self._nodes[connected_id])
        
        return result
    
    def query_nodes(self,
                   node_type: Optional[str] = None,
                   filters: Optional[Dict[str, Any]] = None,
                   limit: int = 100,
                   offset: int = 0) -> List[NeuralNode]:
        """Query nodes by type and property filters.
        
        Args:
            node_type: Optional node type filter
            filters: Property filters (property name -> value)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of matching nodes
        """
        # Update statistics
        self._statistics["query_count"] += 1
        
        # Start with all nodes or filter by type
        if node_type:
            if node_type not in self._node_type_index:
                return []
            candidates = self._node_type_index[node_type].copy()
        else:
            candidates = set(self._nodes.keys())
        
        # Apply property filters
        if filters:
            for prop_name, prop_value in filters.items():
                if prop_name in self._property_index and prop_value in self._property_index[prop_name]:
                    # Intersect with nodes matching this filter
                    candidates &= self._property_index[prop_name][prop_value]
                else:
                    # No nodes match this filter
                    return []
        
        # Convert to list and apply pagination
        result_ids = list(candidates)[offset:offset + limit]
        return [self._nodes[node_id] for node_id in result_ids]
    
    def semantic_search(self,
                       query_vector: List[float],
                       node_type: Optional[str] = None,
                       limit: int = 10) -> List[Tuple[NeuralNode, float]]:
        """Search for nodes semantically similar to a vector.
        
        Args:
            query_vector: Query vector embedding
            node_type: Optional node type filter
            limit: Maximum number of results
            
        Returns:
            List of (node, similarity_score) tuples
        """
        # Update statistics
        self._statistics["query_count"] += 1
        
        # Use external vector store if available
        if self._vector_store:
            # Convert results from vector store
            metadata_filter = {"node_type": node_type} if node_type else None
            vector_results = self._vector_store.search(
                vector=query_vector,
                limit=limit,
                metadata_filter=metadata_filter
            )
            
            results = []
            for result in vector_results:
                node_id = result["id"]
                if node_id in self._nodes:
                    results.append((self._nodes[node_id], result["score"]))
            return results
        
        # Otherwise, perform in-memory search
        candidates = []
        
        # Filter by node type if specified
        if node_type:
            if node_type not in self._node_type_index:
                return []
            node_ids = self._node_type_index[node_type]
        else:
            node_ids = self._nodes.keys()
        
        # Calculate similarity for nodes with vectors
        from numpy import dot
        from numpy.linalg import norm
        
        for node_id in node_ids:
            node = self._nodes[node_id]
            if node.vector:
                # Cosine similarity
                similarity = dot(query_vector, node.vector) / (norm(query_vector) * norm(node.vector))
                candidates.append((node, similarity))
        
        # Sort by similarity (descending) and return top results
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]
    
    def text_to_vector(self, text: str) -> Optional[List[float]]:
        """Convert text to vector embedding.
        
        Args:
            text: Input text
            
        Returns:
            Vector embedding or None if embedding function not available
        """
        if not self._embedding_function:
            return None
            
        return self._embedding_function([text])[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the neural fabric."""
        # Count actual connections
        connection_count = sum(
            sum(len(connections) for connections in node.connections.values())
            for node in self._nodes.values()
        )
        
        # Update statistics
        self._statistics["connection_count"] = connection_count
        self._statistics["node_count"] = len(self._nodes)
        
        stats = self._statistics.copy()
        
        # Add node type distribution
        stats["node_types"] = {
            node_type: len(nodes)
            for node_type, nodes in self._node_type_index.items()
        }
        
        # Add pending embeddings count
        stats["pending_embeddings"] = len(self._nodes_pending_embedding)
        
        return stats
    
    def export_to_file(self, path: str):
        """Export neural fabric to a file.
        
        Args:
            path: Path to save the export
        """
        data = {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "metadata": {
                "version": "1.0",
                "timestamp": time.time(),
                "statistics": self.get_stats()
            }
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Exported neural fabric to {path} with {len(self._nodes)} nodes")
    
    def import_from_file(self, path: str) -> int:
        """Import neural fabric from a file.
        
        Args:
            path: Path to the import file
            
        Returns:
            Number of nodes imported
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Process nodes
        for node_data in data["nodes"]:
            node = NeuralNode.from_dict(node_data)
            
            # Add to storage
            self._nodes[node.id] = node
            
            # Update indices
            if node.node_type not in self._node_type_index:
                self._node_type_index[node.node_type] = set()
            self._node_type_index[node.node_type].add(node.id)
            
            # Index properties
            for prop_name, prop_value in node.properties.items():
                if isinstance(prop_value, (str, int, float, bool)):
                    if prop_name not in self._property_index:
                        self._property_index[prop_name] = {}
                    
                    if prop_value not in self._property_index[prop_name]:
                        self._property_index[prop_name][prop_value] = set()
                    
                    self._property_index[prop_name][prop_value].add(node.id)
        
        # Update statistics
        self._statistics["node_count"] = len(self._nodes)
        
        # Calculate connection count
        connection_count = sum(
            sum(len(connections) for connections in node.connections.values())
            for node in self._nodes.values()
        )
        self._statistics["connection_count"] = connection_count
        
        logger.info(f"Imported neural fabric from {path} with {len(self._nodes)} nodes")
        return len(self._nodes)