"""
Inventory Agent for NeuroERP.

This agent manages inventory tracking, demand forecasting, reorder optimization,
stock level monitoring, and intelligent inventory management.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime, date, timedelta
import math
import random
import re

from ...core.config import Config
from ...core.event_bus import EventBus
from ...core.neural_fabric import NeuralFabric
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

class InventoryAgent(BaseAgent):
    """AI Agent for inventory management and optimization."""
    
    def __init__(self, name: str = "Inventory Agent", ai_engine=None, vector_store=None):
        """Initialize the inventory agent.
        
        Args:
            name: Name of the agent
            ai_engine: AI engine for advanced processing
            vector_store: Vector store for semantic search
        """
        super().__init__(name=name, agent_type="supply_chain.inventory", ai_engine=ai_engine, vector_store=vector_store)
        
        self.config = Config()
        self.event_bus = EventBus()
        self.neural_fabric = NeuralFabric()
        
        # Register agent skills
        self._register_skills()
        
        # Subscribe to relevant events
        self._subscribe_to_events()
        
        logger.info(f"Initialized {name}")
    
    def _register_skills(self):
        """Register agent-specific skills."""
        self.register_skill("manage_product", self.manage_product)
        self.register_skill("manage_warehouse", self.manage_warehouse)
        self.register_skill("update_inventory", self.update_inventory)
        self.register_skill("transfer_inventory", self.transfer_inventory)
        self.register_skill("calculate_reorder_points", self.calculate_reorder_points)
        self.register_skill("forecast_demand", self.forecast_demand)
        self.register_skill("optimize_stock_levels", self.optimize_stock_levels)
        self.register_skill("generate_inventory_report", self.generate_inventory_report)
        self.register_skill("analyze_inventory_health", self.analyze_inventory_health)
        self.register_skill("detect_anomalies", self.detect_anomalies)
    
    def _subscribe_to_events(self):
        """Subscribe to relevant system events."""
        self.event_bus.subscribe("product.created", self._handle_product_change)
        self.event_bus.subscribe("product.updated", self._handle_product_change)
        self.event_bus.subscribe("inventory.updated", self._handle_inventory_change)
        self.event_bus.subscribe("inventory.below_threshold", self._handle_low_inventory)
        self.event_bus.subscribe("order.created", self._handle_order)
        self.event_bus.subscribe("order.fulfilled", self._handle_order_fulfillment)
        self.event_bus.subscribe("demand.forecasted", self._handle_new_forecast)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results.
        
        Args:
            input_data: Input data with action and parameters
            
        Returns:
            Processing results
        """
        action = input_data.get("action", "")
        parameters = input_data.get("parameters", {})
        
        # Log the requested action
        logger.info(f"Processing {action} with parameters: {parameters}")
        
        # Dispatch to appropriate skill
        try:
            if action == "manage_product":
                return {"success": True, "result": self.manage_product(**parameters)}
            elif action == "manage_warehouse":
                return {"success": True, "result": self.manage_warehouse(**parameters)}
            elif action == "update_inventory":
                return {"success": True, "result": self.update_inventory(**parameters)}
            elif action == "transfer_inventory":
                return {"success": True, "result": self.transfer_inventory(**parameters)}
            elif action == "calculate_reorder_points":
                return {"success": True, "result": self.calculate_reorder_points(**parameters)}
            elif action == "forecast_demand":
                return {"success": True, "result": self.forecast_demand(**parameters)}
            elif action == "optimize_stock_levels":
                return {"success": True, "result": self.optimize_stock_levels(**parameters)}
            elif action == "generate_inventory_report":
                return {"success": True, "result": self.generate_inventory_report(**parameters)}
            elif action == "analyze_inventory_health":
                return {"success": True, "result": self.analyze_inventory_health(**parameters)}
            elif action == "detect_anomalies":
                return {"success": True, "result": self.detect_anomalies(**parameters)}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [skill["name"] for skill in self.skills]
                }
        except Exception as e:
            logger.error(f"Error processing {action}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def manage_product(self,
                      action: str,
                      product_data: Dict[str, Any],
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage product in the inventory system.
        
        Args:
            action: Action to perform (create, update, deactivate)
            product_data: Product data
            metadata: Additional metadata
            
        Returns:
            Product operation result
        """
        if action == "create":
            # Validate required fields
            required_fields = ["name", "sku", "category"]
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check if SKU already exists
            if "sku" in product_data:
                existing_products = self.neural_fabric.query_nodes(
                    node_type="product",
                    filters={"sku": product_data["sku"]}
                )
                
                if existing_products:
                    raise ValueError(f"Product with SKU {product_data['sku']} already exists")
            
            # Create product properties
            product_properties = {
                "name": product_data["name"],
                "sku": product_data["sku"],
                "category": product_data["category"],
                "active": True,
                "created_at": datetime.now().isoformat()
            }
            
            # Add optional properties
            optional_fields = [
                "description", "unit_of_measure", "unit_price",
                "weight", "dimensions", "reorder_point", "reorder_quantity",
                "lead_time_days", "barcode", "supplier_id", "manufacturer"
            ]
            
            for field in optional_fields:
                if field in product_data:
                    product_properties[field] = product_data[field]
            
            # Add metadata if provided
            if metadata:
                product_properties["metadata"] = metadata
            
            # Create product node
            product_id = self.neural_fabric.create_node(
                node_type="product",
                properties=product_properties
            )
            
            # Connect to supplier if specified
            if "supplier_id" in product_data:
                supplier_id = product_data["supplier_id"]
                supplier_node = self.neural_fabric.get_node(supplier_id)
                
                if supplier_node and supplier_node.node_type == "supplier":
                    self.neural_fabric.connect_nodes(
                        source_id=product_id,
                        target_id=supplier_id,
                        relation_type="supplied_by"
                    )
            
            # Initialize inventory for this product in each warehouse
            warehouse_nodes = self.neural_fabric.query_nodes(
                node_type="warehouse"
            )
            
            for warehouse in warehouse_nodes:
                inventory_properties = {
                    "product_id": product_id,
                    "product_name": product_data["name"],
                    "product_sku": product_data["sku"],
                    "warehouse_id": warehouse.id,
                    "warehouse_name": warehouse.properties.get("name"),
                    "quantity_on_hand": 0,
                    "quantity_allocated": 0,
                    "quantity_available": 0,
                    "last_updated": datetime.now().isoformat()
                }
                
                inventory_id = self.neural_fabric.create_node(
                    node_type="inventory",
                    properties=inventory_properties
                )
                
                # Connect inventory to product and warehouse
                self.neural_fabric.connect_nodes(
                    source_id=inventory_id,
                    target_id=product_id,
                    relation_type="tracks"
                )
                
                self.neural_fabric.connect_nodes(
                    source_id=inventory_id,
                    target_id=warehouse.id,
                    relation_type="stored_at"
                )
            
            # Publish event
            self.event_bus.publish(
                event_type="product.created",
                payload={
                    "product_id": product_id,
                    "name": product_data["name"],
                    "sku": product_data["sku"],
                    "category": product_data["category"]
                }
            )
            
            logger.info(f"Created product: {product_data['name']} (SKU: {product_data['sku']}, ID: {product_id})")
            
            return {
                "action": "create",
                "product_id": product_id,
                "name": product_data["name"],
                "sku": product_data["sku"],
                "category": product_data["category"]
            }
            
        elif action == "update":
            # Validate product ID
            if "product_id" not in product_data:
                raise ValueError("Missing product_id for update")
                
            product_id = product_data["product_id"]
            product = self.neural_fabric.get_node(product_id)
            
            if not product or product.node_type != "product":
                raise ValueError(f"Invalid product ID: {product_id}")
            
            # Prepare update properties
            update_properties = {}
            updatable_fields = [
                "name", "description", "category", "unit_of_measure", "unit_price",
                "weight", "dimensions", "reorder_point", "reorder_quantity",
                "lead_time_days", "barcode", "supplier_id", "manufacturer"
            ]
            
            for field in updatable_fields:
                if field in product_data:
                    update_properties[field] = product_data[field]
            
            # Add metadata if provided
            if metadata:
                update_properties["metadata"] = metadata
                
            # Update last modified
            update_properties["last_modified"] = datetime.now().isoformat()
            
            # Update product node
            self.neural_fabric.update_node(
                node_id=product_id,
                properties=update_properties
            )
            
            # Update supplier relationship if changed
            if "supplier_id" in product_data:
                new_supplier_id = product_data["supplier_id"]
                
                # Remove existing supplier relationships
                supplier_connections = self.neural_fabric.get_connected_nodes(
                    node_id=product_id,
                    relation_type="supplied_by"
                )
                
                if "supplied_by" in supplier_connections:
                    for supplier in supplier_connections["supplied_by"]:
                        self.neural_fabric.disconnect_nodes(
                            source_id=product_id,
                            target_id=supplier.id,
                            relation_type="supplied_by"
                        )
                
                # Add new supplier relationship
                if new_supplier_id:
                    supplier_node = self.neural_fabric.get_node(new_supplier_id)
                    
                    if supplier_node and supplier_node.node_type == "supplier":
                        self.neural_fabric.connect_nodes(
                            source_id=product_id,
                            target_id=new_supplier_id,
                            relation_type="supplied_by"
                        )
            
            # If product name has changed, update all inventory nodes for this product
            if "name" in update_properties:
                inventory_nodes = self.neural_fabric.query_nodes(
                    node_type="inventory",
                    filters={"product_id": product_id}
                )
                
                for inventory in inventory_nodes:
                    self.neural_fabric.update_node(
                        node_id=inventory.id,
                        properties={"product_name": update_properties["name"]}
                    )
            
            # Publish event
            self.event_bus.publish(
                event_type="product.updated",
                payload={
                    "product_id": product_id,
                    "sku": product.properties.get("sku"),
                    "updates": update_properties
                }
            )
            
            logger.info(f"Updated product ID {product_id}: {update_properties}")
            
            return {
                "action": "update",
                "product_id": product_id,
                "sku": product.properties.get("sku"),
                "updates": update_properties
            }
            
        elif action == "deactivate":
            # Validate product ID
            if "product_id" not in product_data:
                raise ValueError("Missing product_id for deactivate")
                
            product_id = product_data["product_id"]
            product = self.neural_fabric.get_node(product_id)
            
            if not product or product.node_type != "product":
                raise ValueError(f"Invalid product ID: {product_id}")
            
            # Check if there is inventory that would need to be dealt with
            inventory_nodes = self.neural_fabric.query_nodes(
                node_type="inventory",
                filters={"product_id": product_id}
            )
            
            total_inventory = sum(node.properties.get("quantity_on_hand", 0) for node in inventory_nodes)
            if total_inventory > 0 and not product_data.get("force_deactivate", False):
                return {
                    "action": "deactivate",
                    "product_id": product_id,
                    "status": "error",
                    "error": f"Product has {total_inventory} units in inventory across {len(inventory_nodes)} locations",
                    "requires_force": True
                }
            
            # Deactivate product
            self.neural_fabric.update_node(
                node_id=product_id,
                properties={
                    "active": False,
                    "deactivated_at": datetime.now().isoformat(),
                    "deactivation_reason": product_data.get("reason", "Not specified")
                }
            )
            
            # Publish event
            self.event_bus.publish(
                event_type="product.deactivated",
                payload={
                    "product_id": product_id,
                    "sku": product.properties.get("sku"),
                    "name": product.properties.get("name"),
                    "reason": product_data.get("reason")
                }
            )
            
            logger.info(f"Deactivated product ID {product_id}")
            
            return {
                "action": "deactivate",
                "product_id": product_id,
                "sku": product.properties.get("sku"),
                "status": "deactivated"
            }
        else:
            raise ValueError(f"Unknown product action: {action}")
    
    def manage_warehouse(self,
                        action: str,
                        warehouse_data: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage warehouse in the inventory system.
        
        Args:
            action: Action to perform (create, update, deactivate)
            warehouse_data: Warehouse data
            metadata: Additional metadata
            
        Returns:
            Warehouse operation result
        """
        if action == "create":
            # Validate required fields
            required_fields = ["name", "code", "location"]
            for field in required_fields:
                if field not in warehouse_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check if code already exists
            if "code" in warehouse_data:
                existing_warehouses = self.neural_fabric.query_nodes(
                    node_type="warehouse",
                    filters={"code": warehouse_data["code"]}
                )
                
                if existing_warehouses:
                    raise ValueError(f"Warehouse with code {warehouse_data['code']} already exists")
            
            # Create warehouse properties
            warehouse_properties = {
                "name": warehouse_data["name"],
                "code": warehouse_data["code"],
                "location": warehouse_data["location"],
                "active": True,
                "created_at": datetime.now().isoformat()
            }
            
            # Add optional properties
            optional_fields = [
                "address", "city", "state", "postal_code", "country",
                "phone", "email", "capacity", "manager_id", "type"
            ]
            
            for field in optional_fields:
                if field in warehouse_data:
                    warehouse_properties[field] = warehouse_data[field]
            
            # Add metadata if provided
            if metadata:
                warehouse_properties["metadata"] = metadata
            
            # Create warehouse node
            warehouse_id = self.neural_fabric.create_node(
                node_type="warehouse",
                properties=warehouse_properties
            )
            
            # Connect to manager if specified
            if "manager_id" in warehouse_data:
                manager_id = warehouse_data["manager_id"]
                manager_node = self.neural_fabric.get_node(manager_id)
                
                if manager_node and manager_node.node_type == "employee":
                    self.neural_fabric.connect_nodes(
                        source_id=warehouse_id,
                        target_id=manager_id,
                        relation_type="managed_by"
                    )
            
            # Initialize inventory for all products in this warehouse
            product_nodes = self.neural_fabric.query_nodes(
                node_type="product",
                filters={"active": True}
            )
            
            for product in product_nodes:
                inventory_properties = {
                    "product_id": product.id,
                    "product_name": product.properties.get("name"),
                    "product_sku": product.properties.get("sku"),
                    "warehouse_id": warehouse_id,
                    "warehouse_name": warehouse_data["name"],
                    "quantity_on_hand": 0,
                    "quantity_allocated": 0,
                    "quantity_available": 0,
                    "last_updated": datetime.now().isoformat()
                }
                
                inventory_id = self.neural_fabric.create_node(
                    node_type="inventory",
                    properties=inventory_properties
                )
                
                # Connect inventory to product and warehouse
                self.neural_fabric.connect_nodes(
                    source_id=inventory_id,
                    target_id=product.id,
                    relation_type="tracks"
                )
                
                self.neural_fabric.connect_nodes(
                    source_id=inventory_id,
                    target_id=warehouse_id,
                    relation_type="stored_at"
                )
            
            # Publish event
            self.event_bus.publish(
                event_type="warehouse.created",
                payload={
                    "warehouse_id": warehouse_id,
                    "name": warehouse_data["name"],
                    "code": warehouse_data["code"],
                    "location": warehouse_data["location"]
                }
            )
            
            logger.info(f"Created warehouse: {warehouse_data['name']} (Code: {warehouse_data['code']}, ID: {warehouse_id})")
            
            return {
                "action": "create",
                "warehouse_id": warehouse_id,
                "name": warehouse_data["name"],
                "code": warehouse_data["code"],
                "location": warehouse_data["location"]
            }
            
        elif action == "update":
            # Validate warehouse ID
            if "warehouse_id" not in warehouse_data:
                raise ValueError("Missing warehouse_id for update")
                
            warehouse_id = warehouse_data["warehouse_id"]
            warehouse = self.neural_fabric.get_node(warehouse_id)
            
            if not warehouse or warehouse.node_type != "warehouse":
                raise ValueError(f"Invalid warehouse ID: {warehouse_id}")
            
            # Prepare update properties
            update_properties = {}
            updatable_fields = [
                "name", "location", "address", "city", "state", "postal_code", 
                "country", "phone", "email", "capacity", "manager_id", "type"
            ]
            
            for field in updatable_fields:
                if field in warehouse_data:
                    update_properties[field] = warehouse_data[field]
            
            # Add metadata if provided
            if metadata:
                update_properties["metadata"] = metadata
                
            # Update last modified
            update_properties["last_modified"] = datetime.now().isoformat()
            
            # Update warehouse node
            self.neural_fabric.update_node(
                node_id=warehouse_id,
                properties=update_properties
            )
            
            # Update manager relationship if changed
            if "manager_id" in warehouse_data:
                new_manager_id = warehouse_data["manager_id"]
                
                # Remove existing manager relationships
                manager_connections = self.neural_fabric.get_connected_nodes(
                    node_id=warehouse_id,
                    relation_type="managed_by"
                )
                
                if "managed_by" in manager_connections:
                    for manager in manager_connections["managed_by"]:
                        self.neural_fabric.disconnect_nodes(
                            source_id=warehouse_id,
                            target_id=manager.id,
                            relation_type="managed_by"
                        )
                
                # Add new manager relationship
                if new_manager_id:
                    manager_node = self.neural_fabric.get_node(new_manager_id)
                    
                    if manager_node and manager_node.node_type == "employee":
                        self.neural_fabric.connect_nodes(
                            source_id=warehouse_id,
                            target_id=new_manager_id,
                            relation_type="managed_by"
                        )
            
            # If warehouse name has changed, update all inventory nodes for this warehouse
            if "name" in update_properties:
                inventory_nodes = self.neural_fabric.query_nodes(
                    node_type="inventory",
                    filters={"warehouse_id": warehouse_id}
                )
                
                for inventory in inventory_nodes:
                    self.neural_fabric.update_node(
                        node_id=inventory.id,
                        properties={"warehouse_name": update_properties["name"]}
                    )
            
            # Publish event
            self.event_bus.publish(
                event_type="warehouse.updated",
                payload={
                    "warehouse_id": warehouse_id,
                    "code": warehouse.properties.get("code"),
                    "updates": update_properties
                }
            )
            
            logger.info(f"Updated warehouse ID {warehouse_id}: {update_properties}")
            
            return {
                "action": "update",
                "warehouse_id": warehouse_id,
                "code": warehouse.properties.get("code"),
                "updates": update_properties
            }
            
        elif action == "deactivate":
            # Validate warehouse ID
            if "warehouse_id" not in warehouse_data:
                raise ValueError("Missing warehouse_id for deactivate")
                
            warehouse_id = warehouse_data["warehouse_id"]
            warehouse = self.neural_fabric.get_node(warehouse_id)
            
            if not warehouse or warehouse.node_type != "warehouse":
                raise ValueError(f"Invalid warehouse ID: {warehouse_id}")
            
            # Check if there is inventory that would need to be dealt with
            inventory_nodes = self.neural_fabric.query_nodes(
                node_type="inventory",
                filters={"warehouse_id": warehouse_id}
            )
            
            total_inventory = sum(node.properties.get("quantity_on_hand", 0) for node in inventory_nodes)
            if total_inventory > 0 and not warehouse_data.get("force_deactivate", False):
                return {
                    "action": "deactivate",
                    "warehouse_id": warehouse_id,
                    "status": "error",
                    "error": f"Warehouse has {total_inventory} units in inventory across {len(inventory_nodes)} products",
                    "requires_force": True
                }
            
            # Deactivate warehouse
            self.neural_fabric.update_node(
                node_id=warehouse_id,
                properties={
                    "active": False,
                    "deactivated_at": datetime.now().isoformat(),
                    "deactivation_reason": warehouse_data.get("reason", "Not specified")
                }
            )
            
            # Publish event
            self.event_bus.publish(
                event_type="warehouse.deactivated",
                payload={
                    "warehouse_id": warehouse_id,
                    "code": warehouse.properties.get("code"),
                    "name": warehouse.properties.get("name"),
                    "reason": warehouse_data.get("reason")
                }
            )
            
            logger.info(f"Deactivated warehouse ID {warehouse_id}")
            
            return {
                "action": "deactivate",
                "warehouse_id": warehouse_id,
                "code": warehouse.properties.get("code"),
                "status": "deactivated"
            }
        else:
            raise ValueError(f"Unknown warehouse action: {action}")
    
    def update_inventory(self,
                        product_id: str,
                        warehouse_id: str,
                        transaction_type: str,
                        quantity: float,
                        reference: Optional[str] = None,
                        note: Optional[str] = None) -> Dict[str, Any]:
        """Update inventory levels.
        
        Args:
            product_id: ID of the product
            warehouse_id: ID of the warehouse
            transaction_type: Type of inventory transaction (receive, issue, adjust, etc.)
            quantity: Quantity to add or remove (positive for add, negative for remove)
            reference: Optional reference number or document
            note: Optional note about the transaction
            
        Returns:
            Updated inventory details
        """
        # Validate product
        product = self.neural_fabric.get_node(product_id)
        if not product or product.node_type != "product":
            raise ValueError(f"Invalid product ID: {product_id}")
        
        # Validate warehouse
        warehouse = self.neural_fabric.get_node(warehouse_id)
        if not warehouse or warehouse.node_type != "warehouse":
            raise ValueError(f"Invalid warehouse ID: {warehouse_id}")
        
        # Validate quantity
        if not isinstance(quantity, (int, float)):
            raise ValueError(f"Invalid quantity: {quantity}. Must be a number.")
        
        # Find the inventory record for this product/warehouse combination
        inventory_nodes = self.neural_fabric.query_nodes(
            node_type="inventory",
            filters={"product_id": product_id, "warehouse_id": warehouse_id}
        )
        
        if not inventory_nodes:
            # Create a new inventory record if one doesn't exist
            inventory_properties = {
                "product_id": product_id,
                "product_name": product.properties.get("name"),
                "product_sku": product.properties.get("sku"),
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse.properties.get("name"),
                "quantity_on_hand": 0,
                "quantity_allocated": 0,
                "quantity_available": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            inventory_id = self.neural_fabric.create_node(
                node_type="inventory",
                properties=inventory_properties
            )
            
            # Connect inventory to product and warehouse
            self.neural_fabric.connect_nodes(
                source_id=inventory_id,
                target_id=product_id,
                relation_type="tracks"
            )
            
            self.neural_fabric.connect_nodes(
                source_id=inventory_id,
                target_id=warehouse_id,
                relation_type="stored_at"
            )
            
            inventory = self.neural_fabric.get_node(inventory_id)
        else:
            inventory = inventory_nodes[0]
        
        # Get current inventory quantities
        current_qty = inventory.properties.get("quantity_on_hand", 0)
        current_allocated = inventory.properties.get("quantity_allocated", 0)
        
        # Calculate new inventory quantities based on transaction type
        new_qty = current_qty
        new_allocated = current_allocated
        
        if transaction_type == "receive":
            # Receiving new inventory
            new_qty = current_qty + quantity
        elif transaction_type == "issue":
            # Issuing inventory (e.g., for sales, production)
            new_qty = current_qty - quantity
            # Reduce allocated quantity if needed
            if quantity <= current_allocated:
                new_allocated = current_allocated - quantity
            else:
                new_allocated = 0
        elif transaction_type == "adjust":
            # Adjustment (e.g., inventory count, damage, loss)
            new_qty = current_qty + quantity  # Could be positive or negative
        elif transaction_type == "allocate":
            # Allocate inventory (e.g., for pending orders)
            new_allocated = current_allocated + quantity
        elif transaction_type == "deallocate":
            # Deallocate inventory (e.g., cancelled orders)
            new_allocated = max(0, current_allocated - quantity)
        else:
            raise ValueError(f"Unknown transaction type: {transaction_type}")
        
        # Ensure quantities are not negative
        if new_qty < 0 and transaction_type != "adjust":
            raise ValueError(f"Insufficient inventory: {current_qty} available, {quantity} requested")
        
        # Calculate available quantity
        new_available = max(0, new_qty - new_allocated)
        
        # Create transaction record
        transaction_properties = {
            "product_id": product_id,
            "product_sku": product.properties.get("sku"),
            "warehouse_id": warehouse_id,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "previous_quantity": current_qty,
            "new_quantity": new_qty,
            "created_at": datetime.now().isoformat()
        }
        
        if reference:
            transaction_properties["reference"] = reference
        
        if note:
            transaction_properties["note"] = note
        
        transaction_id = self.neural_fabric.create_node(
            node_type="inventory_transaction",
            properties=transaction_properties
        )
        
        # Connect transaction to inventory, product, and warehouse
        self.neural_fabric.connect_nodes(
            source_id=transaction_id,
            target_id=inventory.id,
            relation_type="affects"
        )
        
        self.neural_fabric.connect_nodes(
            source_id=transaction_id,
            target_id=product_id,
            relation_type="involves"
        )
        
        self.neural_fabric.connect_nodes(
            source_id=transaction_id,
            target_id=warehouse_id,
            relation_type="at"
        )
        
        # Update inventory record
        self.neural_fabric.update_node(
            node_id=inventory.id,
            properties={
                "quantity_on_hand": new_qty,
                "quantity_allocated": new_allocated,
                "quantity_available": new_available,
                "last_updated": datetime.now().isoformat()
            }
        )