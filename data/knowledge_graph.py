"""
Knowledge Graph for NeuroERP.

This module provides a specialized knowledge graph implementation that extends
the basic functionality of the neural fabric with semantic knowledge representation,
reasoning capabilities, and domain-specific business logic.
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union, Set, Iterator
from datetime import datetime
import json
import re

from ..core.config import Config
from ..core.neural_fabric import NeuralFabric
from ..core.event_bus import EventBus, Event

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """Enhanced knowledge graph for semantic business data representation."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one knowledge graph instance exists."""
        if cls._instance is None:
            cls._instance = super(KnowledgeGraph, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, neural_fabric=None, ai_engine=None):
        """Initialize the knowledge graph.
        
        Args:
            neural_fabric: Neural fabric instance (or create a new one)
            ai_engine: AI engine for advanced processing
        """
        # Skip if already initialized (singleton pattern)
        if self._initialized:
            return
            
        self.config = Config()
        self.neural_fabric = neural_fabric or NeuralFabric()
        self.event_bus = EventBus()
        self.ai_engine = ai_engine
        
        # Domain-specific ontology definitions
        self._ontology = {}
        
        # Load ontology definitions
        self._load_ontology()
        
        # Register event handlers
        self._register_event_handlers()
        
        self._initialized = True
        logger.info("Knowledge graph initialized")
    
    def _load_ontology(self):
        """Load domain ontology definitions."""
        # Base ontology with entity types and their relationships
        base_ontology = {
            # Core business entities
            "Customer": {
                "properties": ["name", "email", "phone", "address", "type", "status"],
                "relationships": {
                    "PLACED": "Order",
                    "HAS_CONTACT": "Person",
                    "BELONGS_TO": "CustomerGroup"
                }
            },
            "Product": {
                "properties": ["name", "sku", "description", "price", "cost", "category", "status"],
                "relationships": {
                    "BELONGS_TO": "ProductCategory",
                    "SUPPLIED_BY": "Supplier",
                    "INCLUDED_IN": "Order",
                    "STORED_AT": "Warehouse",
                    "HAS_ATTRIBUTE": "ProductAttribute"
                }
            },
            "Order": {
                "properties": ["order_number", "date", "status", "total", "payment_status"],
                "relationships": {
                    "PLACED_BY": "Customer",
                    "CONTAINS": "Product",
                    "FULFILLED_BY": "Shipment",
                    "PAID_WITH": "Payment"
                }
            },
            
            # Financial entities
            "Invoice": {
                "properties": ["invoice_number", "date", "due_date", "amount", "status"],
                "relationships": {
                    "BILLED_TO": "Customer",
                    "REFERENCES": "Order",
                    "PAID_BY": "Payment"
                }
            },
            "Payment": {
                "properties": ["payment_number", "date", "amount", "method", "status"],
                "relationships": {
                    "MADE_BY": "Customer",
                    "APPLIES_TO": "Invoice",
                    "PROCESSED_BY": "Employee"
                }
            },
            "Account": {
                "properties": ["number", "name", "type", "balance", "active"],
                "relationships": {
                    "PARENT": "Account",
                    "AFFECTED_BY": "Transaction"
                }
            },
            "Transaction": {
                "properties": ["reference", "date", "amount", "description", "type"],
                "relationships": {
                    "AFFECTS": "Account",
                    "CREATED_BY": "Employee",
                    "RELATES_TO": "Invoice"
                }
            },
            
            # Inventory and supply chain entities
            "Warehouse": {
                "properties": ["name", "code", "location", "capacity", "status"],
                "relationships": {
                    "STORES": "Product",
                    "MANAGED_BY": "Employee",
                    "SHIPS_FROM": "Shipment"
                }
            },
            "Inventory": {
                "properties": ["quantity", "location", "status", "last_updated"],
                "relationships": {
                    "OF_PRODUCT": "Product",
                    "AT_WAREHOUSE": "Warehouse",
                    "AFFECTED_BY": "InventoryTransaction"
                }
            },
            "Supplier": {
                "properties": ["name", "code", "contact", "status", "lead_time"],
                "relationships": {
                    "SUPPLIES": "Product",
                    "PROVIDES": "PurchaseOrder"
                }
            },
            "Shipment": {
                "properties": ["shipment_number", "date", "status", "tracking"],
                "relationships": {
                    "CONTAINS": "Product",
                    "SHIPS_TO": "Customer",
                    "FULFILLS": "Order",
                    "SHIPS_FROM": "Warehouse",
                    "CARRIED_BY": "Carrier"
                }
            },
            
            # Human resources entities
            "Employee": {
                "properties": ["name", "position", "department", "hire_date", "status"],
                "relationships": {
                    "REPORTS_TO": "Employee",
                    "MANAGES": "Department",
                    "PROCESSES": "Order"
                }
            },
            "Department": {
                "properties": ["name", "code", "budget", "location"],
                "relationships": {
                    "MANAGED_BY": "Employee",
                    "PART_OF": "Department"
                }
            },
            
            # Support and service entities
            "SupportTicket": {
                "properties": ["ticket_number", "title", "description", "status", "priority"],
                "relationships": {
                    "SUBMITTED_BY": "Customer",
                    "ASSIGNED_TO": "Employee",
                    "RELATES_TO": "Product"
                }
            },
            "Project": {
                "properties": ["name", "description", "start_date", "end_date", "status"],
                "relationships": {
                    "MANAGED_BY": "Employee",
                    "FOR_CUSTOMER": "Customer",
                    "HAS_TASK": "Task"
                }
            }
        }
        
        # Apply any custom ontology extensions from configuration
        custom_ontology = self.config.get("knowledge_graph.ontology", {})
        
        # Merge base and custom ontologies
        self._ontology = base_ontology
        
        # Apply custom extensions
        for entity_type, definition in custom_ontology.items():
            if entity_type in self._ontology:
                # Extend existing entity type
                if "properties" in definition:
                    self._ontology[entity_type]["properties"].extend(
                        [p for p in definition["properties"] if p not in self._ontology[entity_type]["properties"]]
                    )
                
                if "relationships" in definition:
                    self._ontology[entity_type]["relationships"].update(definition["relationships"])
            else:
                # Add new entity type
                self._ontology[entity_type] = definition
        
        logger.info(f"Loaded ontology with {len(self._ontology)} entity types")
    
    def _register_event_handlers(self):
        """Register event handlers for knowledge graph updates."""
        # Listen for entity changes
        self.event_bus.subscribe("node.created", self._handle_node_created)
        self.event_bus.subscribe("node.updated", self._handle_node_updated)
        self.event_bus.subscribe("node.deleted", self._handle_node_deleted)
        
        # Listen for relationship changes
        self.event_bus.subscribe("connection.created", self._handle_connection_created)
        self.event_bus.subscribe("connection.deleted", self._handle_connection_deleted)
        
        # Listen for AI-driven insights
        self.event_bus.subscribe("anomaly.detected", self._handle_anomaly_detected)
        self.event_bus.subscribe("forecast.created", self._handle_forecast_created)
    
    def _handle_node_created(self, event: Event):
        """Handle node creation events."""
        node_id = event.payload.get("node_id")
        node_type = event.payload.get("node_type")
        
        if node_id and node_type:
            self._enrich_entity(node_id, node_type)
    
    def _handle_node_updated(self, event: Event):
        """Handle node update events."""
        node_id = event.payload.get("node_id")
        if node_id:
            node = self.neural_fabric.get_node(node_id)
            if node:
                self._validate_entity(node)
                self._infer_relationships(node)
    
    def _handle_node_deleted(self, event: Event):
        """Handle node deletion events."""
        # Cleanup is handled by neural fabric, nothing special to do here
        pass
    
    def _handle_connection_created(self, event: Event):
        """Handle connection creation events."""
        source_id = event.payload.get("source_id")
        target_id = event.payload.get("target_id")
        relation_type = event.payload.get("relation_type")
        
        if source_id and target_id and relation_type:
            self._validate_relationship(source_id, target_id, relation_type)
    
    def _handle_connection_deleted(self, event: Event):
        """Handle connection deletion events."""
        # Cleanup is handled by neural fabric, nothing special to do here
        pass
    
    def _handle_anomaly_detected(self, event: Event):
        """Handle anomaly detection events."""
        # Process insights from anomaly detection
        anomaly_id = event.payload.get("anomaly_id")
        if anomaly_id:
            anomaly = self.neural_fabric.get_node(anomaly_id)
            if anomaly and anomaly.node_type == "anomaly":
                self._process_anomaly_insight(anomaly)
    
    def _handle_forecast_created(self, event: Event):
        """Handle forecast creation events."""
        # Process insights from forecasts
        forecast_id = event.payload.get("forecast_id")
        if forecast_id:
            forecast = self.neural_fabric.get_node(forecast_id)
            if forecast and forecast.node_type == "forecast":
                self._process_forecast_insight(forecast)
    
    def create_entity(self, 
                     entity_type: str, 
                     properties: Dict[str, Any], 
                     relationships: Optional[List[Dict[str, Any]]] = None) -> str:
        """Create a new entity in the knowledge graph.
        
        Args:
            entity_type: Type of entity to create
            properties: Entity properties
            relationships: Optional relationships to other entities
            
        Returns:
            Entity ID
        """
        # Validate entity type against ontology
        if entity_type not in self._ontology:
            logger.warning(f"Creating entity with unknown type: {entity_type}")
        
        # Apply entity type naming convention if needed
        node_type = self._normalize_type_name(entity_type)
        
        # Create entity node in neural fabric
        entity_id = self.neural_fabric.create_node(
            node_type=node_type,
            properties=properties
        )
        
        # Create relationships if provided
        if relationships:
            for rel in relationships:
                target_id = rel.get("target_id")
                relation_type = rel.get("relation_type")
                if target_id and relation_type:
                    self.neural_fabric.connect_nodes(
                        source_id=entity_id,
                        target_id=target_id,
                        relation_type=relation_type
                    )
        
        # Enrich entity with inferred properties and relationships
        self._enrich_entity(entity_id, entity_type)
        
        return entity_id
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID with enriched representation.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Enriched entity or None if not found
        """
        node = self.neural_fabric.get_node(entity_id)
        if not node:
            return None
        
        # Convert to enriched representation
        return self._node_to_entity(node)
    
    def update_entity(self, 
                     entity_id: str, 
                     properties: Dict[str, Any], 
                     relationships: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Update an existing entity.
        
        Args:
            entity_id: Entity ID to update
            properties: Updated properties
            relationships: Optional relationships to modify
            
        Returns:
            True if update successful, False otherwise
        """
        # Verify entity exists
        node = self.neural_fabric.get_node(entity_id)
        if not node:
            return False
        
        # Update properties
        if properties:
            self.neural_fabric.update_node(
                node_id=entity_id,
                properties=properties
            )
        
        # Update relationships
        if relationships:
            for rel in relationships:
                action = rel.get("action", "create")
                target_id = rel.get("target_id")
                relation_type = rel.get("relation_type")
                
                if not target_id or not relation_type:
                    continue
                
                if action == "create":
                    self.neural_fabric.connect_nodes(
                        source_id=entity_id,
                        target_id=target_id,
                        relation_type=relation_type
                    )
                elif action == "delete":
                    self.neural_fabric.disconnect_nodes(
                        source_id=entity_id,
                        target_id=target_id,
                        relation_type=relation_type
                    )
        
        # Re-validate the entity
        self._validate_entity(node)
        
        return True
    
    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity from the knowledge graph.
        
        Args:
            entity_id: Entity ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        # This simply delegates to neural fabric
        return self.neural_fabric.delete_node(entity_id)
    
    def search_entities(self,
                       entity_type: Optional[str] = None,
                       properties: Optional[Dict[str, Any]] = None,
                       filters: Optional[Dict[str, Any]] = None,
                       limit: int = 100,
                       offset: int = 0) -> List[Dict[str, Any]]:
        """Search for entities with specified criteria.
        
        Args:
            entity_type: Optional entity type filter
            properties: Optional property filters
            filters: Optional advanced filters
            limit: Maximum results to return
            offset: Offset for pagination
            
        Returns:
            List of matching entities
        """
        # Apply entity type naming convention if needed
        node_type = self._normalize_type_name(entity_type) if entity_type else None
        
        # Convert property filters to neural fabric format
        query_filters = {}
        if properties:
            for key, value in properties.items():
                query_filters[key] = value
        
        # Apply additional filters if provided
        if filters:
            # Handle special filter operators (>, <, >=, <=, !=)
            for key, value in filters.items():
                if isinstance(value, dict) and key not in query_filters:
                    # Handle operators like {"price": {"$gt": 100}}
                    for op, op_value in value.items():
                        # Neural fabric doesn't support these directly,
                        # so we'll filter results after querying
                        pass
        
        # Perform base query
        nodes = self.neural_fabric.query_nodes(
            node_type=node_type,
            filters=query_filters,
            limit=limit + offset  # Fetch extra for post-filtering
        )
        
        # Apply advanced filters that neural fabric doesn't support
        if filters:
            filtered_nodes = []
            for node in nodes:
                include = True
                
                for key, value in filters.items():
                    if isinstance(value, dict):
                        node_value = node.properties.get(key)
                        
                        for op, op_value in value.items():
                            if op == "$gt" and not (node_value > op_value):
                                include = False
                                break
                            elif op == "$lt" and not (node_value < op_value):
                                include = False
                                break
                            elif op == "$gte" and not (node_value >= op_value):
                                include = False
                                break
                            elif op == "$lte" and not (node_value <= op_value):
                                include = False
                                break
                            elif op == "$ne" and node_value == op_value:
                                include = False
                                break
                        
                        if not include:
                            break
                
                if include:
                    filtered_nodes.append(node)
                    
                    if len(filtered_nodes) >= limit + offset:
                        break
            
            nodes = filtered_nodes
        
        # Apply pagination
        paginated_nodes = nodes[offset:offset + limit]
        
        # Convert nodes to enriched entity representation
        entities = [self._node_to_entity(node) for node in paginated_nodes]
        
        return entities
    
    def query(self, query_str: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a graph query.
        
        Args:
            query_str: Query string in custom query format or natural language
            parameters: Optional query parameters
            
        Returns:
            Query results
        """
        if not parameters:
            parameters = {}
        
        # Check if this is a natural language query
        is_natural_language = not (
            query_str.strip().startswith('MATCH') or
            query_str.strip().startswith('FIND') or
            query_str.strip().startswith('GET') or
            '{' in query_str or
            '[' in query_str
        )
        
        if is_natural_language and self.ai_engine:
            # Use AI to translate natural language to structured query
            return self._execute_natural_language_query(query_str, parameters)
        else:
            # Parse and execute structured query
            return self._execute_structured_query(query_str, parameters)
    
    def _execute_natural_language_query(self, query_str: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a natural language query using AI translation.
        
        Args:
            query_str: Natural language query string
            parameters: Query parameters
            
        Returns:
            Query results
        """
        # Use AI to translate to structured query
        structured_query = self._translate_query(query_str)
        
        # Execute the structured query
        if structured_query:
            try:
                return self._execute_structured_query(structured_query, parameters)
            except Exception as e:
                logger.error(f"Error executing translated query: {e}")
                # Fallback to simple keyword search
                return self._execute_keyword_search(query_str)
        else:
            # Fallback to simple keyword search
            return self._execute_keyword_search(query_str)
    
    def _translate_query(self, natural_query: str) -> Optional[str]:
        """Translate natural language query to structured query.
        
        Args:
            natural_query: Natural language query
            
        Returns:
            Structured query string or None if translation failed
        """
        if not self.ai_engine:
            return None
        
        # Provide information about our ontology to the AI
        ontology_info = json.dumps(self._ontology, indent=2)
        
        prompt = f"""
Translate the following natural language query into a structured graph query.
The knowledge graph has the following entity types and relationships:

{ontology_info}

Natural language query: {natural_query}

Translate this to a structured query that looks like:
MATCH [EntityType] WHERE (conditions) RETURN properties
or
FIND [EntityType]-[RELATIONSHIP]->[OtherType] WHERE (conditions)

Structured query:
"""
        
        # Get translation from AI
        response = self.ai_engine.get_agent_response(
            agent_type="system",
            prompt=prompt
        )
        
        # Extract the query from the response
        match = re.search(r'(MATCH|FIND|GET)[\s\S]+', response)
        if match:
            return match.group(0).strip()
        
        return None
    
    def _execute_structured_query(self, query_str: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a structured graph query.
        
        Args:
            query_str: Structured query string
            parameters: Query parameters
            
        Returns:
            Query results
        """
        # Parse the query
        query_type, entity_type, conditions, relationships, return_spec = self._parse_query(query_str, parameters)
        
        # Initialize results
        results = []
        
        if query_type == "MATCH":
            # Basic entity query with conditions
            entities = self.search_entities(
                entity_type=entity_type,
                filters=conditions,
                limit=parameters.get("limit", 100)
            )
            
            results = entities
            
        elif query_type == "FIND":
            # Relationship query
            source_entities = self.search_entities(
                entity_type=entity_type,
                filters=conditions,
                limit=parameters.get("limit", 100)
            )
            
            # For each source entity, find related entities
            for source in source_entities:
                source_id = source.get("id")
                if not source_id:
                    continue
                
                for rel_info in relationships:
                    rel_type = rel_info.get("type")
                    target_type = rel_info.get("target_type")
                    direction = rel_info.get("direction", "outgoing")
                    
                    # Get connected nodes
                    connected = self._get_connected_entities(
                        source_id, rel_type, target_type, direction
                    )
                    
                    # Add to results with relationship context
                    for target in connected:
                        result_item = {
                            "source": source,
                            "relationship": rel_type,
                            "target": target
                        }
                        results.append(result_item)
        
        # Process return specification if provided
        if return_spec and return_spec != "*":
            # Filter returned properties
            filtered_results = []
            return_props = [p.strip() for p in return_spec.split(",")]
            
            for result in results:
                if isinstance(result, dict):
                    if "source" in result and "target" in result:
                        # Relationship result
                        filtered_result = {
                            "source": self._filter_properties(result["source"], return_props),
                            "relationship": result["relationship"],
                            "target": self._filter_properties(result["target"], return_props)
                        }
                    else:
                        # Entity result
                        filtered_result = self._filter_properties(result, return_props)
                        
                    filtered_results.append(filtered_result)
            
            results = filtered_results
        
        return results
    
    def _parse_query(self, query_str: str, parameters: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], List[Dict[str, Any]], str]:
        """Parse a structured query string.
        
        Args:
            query_str: Structured query string
            parameters: Query parameters
            
        Returns:
            Tuple of (query_type, entity_type, conditions, relationships, return_spec)
        """
        # Basic parsing - in a real implementation this would be more robust
        query_str = query_str.strip()
        
        # Determine query type
        if query_str.startswith("MATCH"):
            query_type = "MATCH"
        elif query_str.startswith("FIND"):
            query_type = "FIND"
        elif query_str.startswith("GET"):
            query_type = "MATCH"  # Treat GET as MATCH
        else:
            raise ValueError(f"Unknown query type in: {query_str}")
        
        # Extract entity type
        entity_match = re.search(r'(MATCH|FIND|GET)\s+\[([^\]]+)\]', query_str)
        entity_type = entity_match.group(2) if entity_match else None
        
        # Extract conditions
        conditions = {}
        where_match = re.search(r'WHERE\s+\(([^)]+)\)', query_str)
        if where_match:
            condition_str = where_match.group(1)
            
            # Parse conditions (basic implementation)
            condition_parts = condition_str.split("AND")
            for part in condition_parts:
                # Handle different operators (=, >, <, >=, <=, !=)
                op_match = re.search(r'([^=<>!]+)\s*(=|>|<|>=|<=|!=)\s*(.+)', part.strip())
                if op_match:
                    prop = op_match.group(1).strip()
                    operator = op_match.group(2)
                    value = op_match.group(3).strip()
                    
                    # Handle parameters
                    if value.startswith('$'):
                        param_name = value[1:]
                        if param_name in parameters:
                            value = parameters[param_name]
                        else:
                            logger.warning(f"Missing parameter: {param_name}")
                            continue
                    else:
                        # Convert value to appropriate type
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif re.match(r'^[0-9]+\.[0-9]+$', value):
                            value = float(value)
                        else:
                            # Remove quotes if present
                            value = value.strip('"\'')
                    
                    # Map operator to filter format
                    if operator == '=':
                        conditions[prop] = value
                    elif operator == '>':
                        conditions[prop] = {"$gt": value}
                    elif operator == '<':
                        conditions[prop] = {"$lt": value}
                    elif operator == '>=':
                        conditions[prop] = {"$gte": value}
                    elif operator == '<=':
                        conditions[prop] = {"$lte": value}
                    elif operator == '!=':
                        conditions[prop] = {"$ne": value}
        
        # Extract relationships for FIND queries
        relationships = []
        if query_type == "FIND":
            rel_match = re.search(r'\[([^\]]+)\]-\[([^\]]+)\]->\[([^\]]+)\]', query_str)
            if rel_match:
                source_type = rel_match.group(1)
                rel_type = rel_match.group(2)
                target_type = rel_match.group(3)
                
                relationships.append({
                    "type": rel_type,
                    "target_type": target_type,
                    "direction": "outgoing"
                })
            
            # Also check for incoming relationships
            rel_match = re.search(r'\[([^\]]+)\]<-\[([^\]]+)\]-\[([^\]]+)\]', query_str)
            if rel_match:
                source_type = rel_match.group(1)
                rel_type = rel_match.group(2)
                target_type = rel_match.group(3)
                
                relationships.append({
                    "type": rel_type,
                    "target_type": target_type,
                    "direction": "incoming"
                })
        
        # Extract return specification
        return_spec = "*"  # Default to all properties
        return_match = re.search(r'RETURN\s+(.+)$', query_str)
        if return_match:
            return_spec = return_match.group(1).strip()
        
        return query_type, entity_type, conditions, relationships, return_spec
    
    def _execute_keyword_search(self, query_str: str) -> List[Dict[str, Any]]:
        """Execute a simple keyword search across all entities.
        
        Args:
            query_str: Keyword query string
            
        Returns:
            Matching entities
        """
        # This is a simplified implementation
        keywords = query_str.lower().split()
        
        # Search across all entity types
        all_results = []
        
        # Get a sample of entities to search
        nodes = self.neural_fabric.query_nodes(limit=1000)
        
        for node in nodes:
            # Check if any property contains the keywords
            match_score = 0
            for prop_name, prop_value in node.properties.items():
                if isinstance(prop_value, str):
                    prop_lower = prop_value.lower()
                    for keyword in keywords:
                        if keyword in prop_lower:
                            match_score += 1
            
            if match_score > 0:
                entity = self._node_to_entity(node)
                entity["match_score"] = match_score
                all_results.append(entity)
        
        # Sort by match score
        all_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        # Return top results
        return all_results[:100]
    
    def _get_connected_entities(self, 
                              entity_id: str, 
                              relation_type: str, 
                              target_type: Optional[str] = None,
                              direction: str = "outgoing") -> List[Dict[str, Any]]:
        """Get entities connected to a specified entity.
        
        Args:
            entity_id: Source entity ID
            relation_type: Relationship type
            target_type: Optional target entity type filter
            direction: Relationship direction ('outgoing' or 'incoming')
            
        Returns:
            List of connected entities
        """
        if direction == "outgoing":
            # Get outgoing connections
            connections = self.neural_fabric.get_connected_nodes(
                node_id=entity_id,
                relation_type=relation_type
            )
            
            connected_nodes = connections.get(relation_type, [])
        else:
            # Get incoming connections
            connections = self.neural_fabric.get_connected_nodes(
                node_id=entity_id,
                relation_type=f"{relation_type}_inverse"
            )
            
            connected_nodes = connections.get(f"{relation_type}_inverse", [])
        
        # Filter by target type if specified
        if target_type:
            target_type = self._normalize_type_name(target_type)
            connected_nodes = [node for node in connected_nodes if node.node_type == target_type]
        
        # Convert to entity representation
        entities = [self._node_to_entity(node) for node in connected_nodes]
        
        return entities
    
def _node_to_entity(self, node) -> Dict[str, Any]:
    """Convert a neural fabric node to an enriched entity representation.
    
    Args:
        node: Neural fabric node
    
    Returns:
        Enriched entity representation
    """
    entity = {
        "id": node.id,
        "type": self._denormalize_type_name(node.node_type),
        "properties": node.properties.copy(),
        "created_at": node.properties.get("created_at"),
        "updated_at": node.properties.get("last_modified")
    }
    
    # Add relationship information
    relationships = {}
    
    # Get outgoing relationships
    outgoing_connections = self.neural_fabric.get_connected_nodes(node_id=node.id)
    if outgoing_connections:
        for relation_type, target_nodes in outgoing_connections.items():
            if relation_type.endswith("_inverse"):
                continue  # Skip inverse relationships
                
            if relation_type not in relationships:
                relationships[relation_type] = []
                
            for target in target_nodes:
                relationships[relation_type].append({
                    "id": target.id,
                    "type": self._denormalize_type_name(target.node_type),
                    "name": target.properties.get("name") or target.properties.get("full_name", ""),
                    "summary": self._create_entity_summary(target)
                })
    
    # Get incoming relationships
    incoming_relationships = {}
    for relation_type in list(relationships.keys()):
        inverse_relation = f"{relation_type}_inverse"
        incoming_connections = self.neural_fabric.get_connected_nodes(
            node_id=node.id,
            relation_type=inverse_relation
        )
        
        if inverse_relation in incoming_connections:
            relation_name = f"incoming_{relation_type}"
            incoming_relationships[relation_name] = []
            
            for source in incoming_connections[inverse_relation]:
                incoming_relationships[relation_name].append({
                    "id": source.id,
                    "type": self._denormalize_type_name(source.node_type),
                    "name": source.properties.get("name") or source.properties.get("full_name", ""),
                    "summary": self._create_entity_summary(source)
                })
    
    # Merge relationships
    relationships.update(incoming_relationships)
    
    # Add relationships to entity if there are any
    if relationships:
        entity["relationships"] = relationships
    
    # Add document attachments if any
    document_connections = self.neural_fabric.get_connected_nodes(
        node_id=node.id,
        relation_type="has_document_inverse"
    )
    
    if document_connections and "has_document_inverse" in document_connections:
        documents = []
        for doc in document_connections["has_document_inverse"]:
            documents.append({
                "id": doc.id,
                "type": doc.properties.get("document_type", "document"),
                "name": doc.properties.get("name", "Unnamed Document"),
                "created_at": doc.properties.get("created_at")
            })
            
        if documents:
            entity["documents"] = documents
    
    # Add ontology information if available
    entity_type = self._denormalize_type_name(node.node_type)
    if entity_type in self._ontology:
        ontology_def = self._ontology[entity_type]
        
        # Add schema information
        entity["_schema"] = {
            "properties": ontology_def.get("properties", []),
            "relationships": list(ontology_def.get("relationships", {}).keys())
        }
    
    return entity

def _create_entity_summary(self, node) -> str:
    """Create a brief summary of an entity.
    
    Args:
        node: Neural fabric node
        
    Returns:
        Brief summary string
    """
    node_type = self._denormalize_type_name(node.node_type)
    
    # Use type-specific logic to create meaningful summaries
    if node_type == "Customer":
        return f"{node.properties.get('name', 'Unknown Customer')} ({node.properties.get('type', 'Unknown Type')})"
    elif node_type == "Order":
        return f"Order #{node.properties.get('order_number', 'Unknown')} - {node.properties.get('status', 'Unknown Status')}"
    elif node_type == "Product":
        return f"{node.properties.get('name', 'Unknown Product')} ({node.properties.get('sku', 'No SKU')})"
    elif node_type == "Invoice":
        return f"Invoice #{node.properties.get('invoice_number', 'Unknown')} - ${node.properties.get('total', 0)}"
    elif node_type == "Employee":
        return f"{node.properties.get('first_name', '')} {node.properties.get('last_name', '')} - {node.properties.get('position', 'Unknown Position')}"
    
    # Generic fallback
    name = node.properties.get('name') or node.properties.get('full_name', '')
    return f"{name} ({node_type})" if name else f"{node_type} #{node.id[:8]}"

def _normalize_type_name(self, entity_type: str) -> str:
    """Convert entity type to normalized node type name.
    
    Args:
        entity_type: Entity type name
        
    Returns:
        Normalized node type name
    """
    # Convert CamelCase to snake_case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', entity_type)
    node_type = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return node_type

def _denormalize_type_name(self, node_type: str) -> str:
    """Convert node type to entity type name.
    
    Args:
        node_type: Node type name
        
    Returns:
        Entity type name
    """
    # Convert snake_case to CamelCase
    return ''.join(word.title() for word in node_type.split('_'))
    