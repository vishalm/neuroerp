"""
Logistics Agent for NeuroERP.

This agent manages shipping, delivery optimization, carrier selection,
route planning, and overall logistics operations.
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

class LogisticsAgent(BaseAgent):
    """AI Agent for logistics management and optimization."""
    
    def __init__(self, name: str = "Logistics Agent", ai_engine=None, vector_store=None):
        """Initialize the logistics agent.
        
        Args:
            name: Name of the agent
            ai_engine: AI engine for advanced processing
            vector_store: Vector store for semantic search
        """
        super().__init__(name=name, agent_type="supply_chain.logistics", ai_engine=ai_engine, vector_store=vector_store)
        
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
        self.register_skill("manage_carrier", self.manage_carrier)
        self.register_skill("manage_shipment", self.manage_shipment)
        self.register_skill("create_shipping_plan", self.create_shipping_plan)
        self.register_skill("track_shipment", self.track_shipment)
        self.register_skill("optimize_routes", self.optimize_routes)
        self.register_skill("calculate_shipping_costs", self.calculate_shipping_costs)
        self.register_skill("assign_carrier", self.assign_carrier)
        self.register_skill("generate_shipping_documents", self.generate_shipping_documents)
        self.register_skill("analyze_logistics_performance", self.analyze_logistics_performance)
        self.register_skill("forecast_shipping_needs", self.forecast_shipping_needs)
    
    def _subscribe_to_events(self):
        """Subscribe to relevant system events."""
        self.event_bus.subscribe("order.created", self._handle_new_order)
        self.event_bus.subscribe("shipment.created", self._handle_new_shipment)
        self.event_bus.subscribe("shipment.updated", self._handle_shipment_update)
        self.event_bus.subscribe("shipment.delivered", self._handle_shipment_delivery)
        self.event_bus.subscribe("carrier.updated", self._handle_carrier_update)
        self.event_bus.subscribe("route.optimized", self._handle_route_optimization)
    
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
            if action == "manage_carrier":
                return {"success": True, "result": self.manage_carrier(**parameters)}
            elif action == "manage_shipment":
                return {"success": True, "result": self.manage_shipment(**parameters)}
            elif action == "create_shipping_plan":
                return {"success": True, "result": self.create_shipping_plan(**parameters)}
            elif action == "track_shipment":
                return {"success": True, "result": self.track_shipment(**parameters)}
            elif action == "optimize_routes":
                return {"success": True, "result": self.optimize_routes(**parameters)}
            elif action == "calculate_shipping_costs":
                return {"success": True, "result": self.calculate_shipping_costs(**parameters)}
            elif action == "assign_carrier":
                return {"success": True, "result": self.assign_carrier(**parameters)}
            elif action == "generate_shipping_documents":
                return {"success": True, "result": self.generate_shipping_documents(**parameters)}
            elif action == "analyze_logistics_performance":
                return {"success": True, "result": self.analyze_logistics_performance(**parameters)}
            elif action == "forecast_shipping_needs":
                return {"success": True, "result": self.forecast_shipping_needs(**parameters)}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [skill["name"] for skill in self.skills]
                }
        except Exception as e:
            logger.error(f"Error processing {action}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def manage_carrier(self,
                      action: str,
                      carrier_data: Dict[str, Any],
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage shipping carrier in the logistics system.
        
        Args:
            action: Action to perform (create, update, deactivate)
            carrier_data: Carrier data
            metadata: Additional metadata
            
        Returns:
            Carrier operation result
        """
        if action == "create":
            # Validate required fields
            required_fields = ["name", "code", "type", "contact_info"]
            for field in required_fields:
                if field not in carrier_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check if code already exists
            if "code" in carrier_data:
                existing_carriers = self.neural_fabric.query_nodes(
                    node_type="carrier",
                    filters={"code": carrier_data["code"]}
                )
                
                if existing_carriers:
                    raise ValueError(f"Carrier with code {carrier_data['code']} already exists")
            
            # Create carrier properties
            carrier_properties = {
                "name": carrier_data["name"],
                "code": carrier_data["code"],
                "type": carrier_data["type"],
                "contact_info": carrier_data["contact_info"],
                "active": True,
                "created_at": datetime.now().isoformat()
            }
            
            # Add optional properties
            optional_fields = [
                "description", "website", "api_key", "account_number", 
                "service_levels", "tracking_url", "transit_times", "rates"
            ]
            
            for field in optional_fields:
                if field in carrier_data:
                    carrier_properties[field] = carrier_data[field]
            
            # Add metadata if provided
            if metadata:
                carrier_properties["metadata"] = metadata
            
            # Create carrier node
            carrier_id = self.neural_fabric.create_node(
                node_type="carrier",
                properties=carrier_properties
            )
            
            # Publish event
            self.event_bus.publish(
                event_type="carrier.created",
                payload={
                    "carrier_id": carrier_id,
                    "name": carrier_data["name"],
                    "code": carrier_data["code"],
                    "type": carrier_data["type"]
                }
            )
            
            logger.info(f"Created carrier: {carrier_data['name']} (Code: {carrier_data['code']}, ID: {carrier_id})")
            
            return {
                "action": "create",
                "carrier_id": carrier_id,
                "name": carrier_data["name"],
                "code": carrier_data["code"],
                "type": carrier_data["type"]
            }
            
        elif action == "update":
            # Validate carrier ID
            if "carrier_id" not in carrier_data:
                raise ValueError("Missing carrier_id for update")
                
            carrier_id = carrier_data["carrier_id"]
            carrier = self.neural_fabric.get_node(carrier_id)
            
            if not carrier or carrier.node_type != "carrier":
                raise ValueError(f"Invalid carrier ID: {carrier_id}")
            
            # Prepare update properties
            update_properties = {}
            updatable_fields = [
                "name", "description", "contact_info", "website", "api_key", 
                "account_number", "service_levels", "tracking_url", 
                "transit_times", "rates"
            ]
            
            for field in updatable_fields:
                if field in carrier_data:
                    update_properties[field] = carrier_data[field]
            
            # Add metadata if provided
            if metadata:
                update_properties["metadata"] = metadata
                
            # Update last modified
            update_properties["last_modified"] = datetime.now().isoformat()
            
            # Update carrier node
            self.neural_fabric.update_node(
                node_id=carrier_id,
                properties=update_properties
            )
            
            # Publish event
            self.event_bus.publish(
                event_type="carrier.updated",
                payload={
                    "carrier_id": carrier_id,
                    "code": carrier.properties.get("code"),
                    "updates": update_properties
                }
            )
            
            logger.info(f"Updated carrier ID {carrier_id}: {update_properties}")
            
            return {
                "action": "update",
                "carrier_id": carrier_id,
                "code": carrier.properties.get("code"),
                "updates": update_properties
            }
            
        elif action == "deactivate":
            # Validate carrier ID
            if "carrier_id" not in carrier_data:
                raise ValueError("Missing carrier_id for deactivate")
                
            carrier_id = carrier_data["carrier_id"]
            carrier = self.neural_fabric.get_node(carrier_id)
            
            if not carrier or carrier.node_type != "carrier":
                raise ValueError(f"Invalid carrier ID: {carrier_id}")
            
            # Check if there are active shipments with this carrier
            active_shipments = self.neural_fabric.query_nodes(
                node_type="shipment",
                filters={
                    "carrier_id": carrier_id,
                    "status": ["created", "processed", "in_transit"]
                }
            )
            
            if active_shipments and not carrier_data.get("force_deactivate", False):
                return {
                    "action": "deactivate",
                    "carrier_id": carrier_id,
                    "status": "error",
                    "error": f"Carrier has {len(active_shipments)} active shipments",
                    "requires_force": True
                }
            
            # Deactivate carrier
            self.neural_fabric.update_node(
                node_id=carrier_id,
                properties={
                    "active": False,
                    "deactivated_at": datetime.now().isoformat(),
                    "deactivation_reason": carrier_data.get("reason", "Not specified")
                }
            )
            
            # Publish event
            self.event_bus.publish(
                event_type="carrier.deactivated",
                payload={
                    "carrier_id": carrier_id,
                    "code": carrier.properties.get("code"),
                    "name": carrier.properties.get("name"),
                    "reason": carrier_data.get("reason")
                }
            )
            
            logger.info(f"Deactivated carrier ID {carrier_id}")
            
            return {
                "action": "deactivate",
                "carrier_id": carrier_id,
                "code": carrier.properties.get("code"),
                "status": "deactivated"
            }
        else:
            raise ValueError(f"Unknown carrier action: {action}")
    
    def manage_shipment(self,
                       action: str,
                       shipment_data: Dict[str, Any],
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage shipment in the logistics system.
        
        Args:
            action: Action to perform (create, update, cancel)
            shipment_data: Shipment data
            metadata: Additional metadata
            
        Returns:
            Shipment operation result
        """
        if action == "create":
            # Validate required fields
            required_fields = ["origin", "destination", "ship_date", "items"]
            for field in required_fields:
                if field not in shipment_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate ship date
            try:
                ship_date = datetime.strptime(shipment_data["ship_date"], "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid ship date format: {shipment_data['ship_date']}. Expected YYYY-MM-DD.")
            
            # Generate shipment number
            today = datetime.now()
            shipment_number = f"SHP-{today.strftime('%Y%m%d')}-{str(int(time.time()))[-4:]}"
            
            # Validate items
            if not shipment_data["items"] or not isinstance(shipment_data["items"], list):
                raise ValueError("Items must be a non-empty list")
            
            # Calculate total weight and volume
            total_weight = 0
            total_volume = 0
            for item in shipment_data["items"]:
                if "quantity" not in item or "product_id" not in item:
                    raise ValueError(f"Item missing required fields: {item}")
                
                # Get product details
                product = self.neural_fabric.get_node(item["product_id"])
                if not product or product.node_type != "product":
                    raise ValueError(f"Invalid product ID: {item['product_id']}")
                
                # Add product details to item
                item["product_name"] = product.properties.get("name")
                item["product_sku"] = product.properties.get("sku")
                
                # Calculate weight if available
                if "weight" in product.properties:
                    item_weight = product.properties["weight"] * item["quantity"]
                    item["weight"] = item_weight
                    total_weight += item_weight
                
                # Calculate volume if dimensions available
                if "dimensions" in product.properties:
                    dims = product.properties["dimensions"]
                    if isinstance(dims, dict) and "length" in dims and "width" in dims and "height" in dims:
                        item_volume = dims["length"] * dims["width"] * dims["height"] * item["quantity"]
                        item["volume"] = item_volume
                        total_volume += item_volume
            
            # Assign carrier if provided
            carrier_id = shipment_data.get("carrier_id")
            carrier_name = None
            if carrier_id:
                carrier = self.neural_fabric.get_node(carrier_id)
                if not carrier or carrier.node_type != "carrier":
                    raise ValueError(f"Invalid carrier ID: {carrier_id}")
                carrier_name = carrier.properties.get("name")
            
            # Create shipment properties
            shipment_properties = {
                "shipment_number": shipment_number,
                "origin": shipment_data["origin"],
                "destination": shipment_data["destination"],
                "ship_date": shipment_data["ship_date"],
                "items": shipment_data["items"],
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "total_weight": total_weight,
                "total_volume": total_volume,
                "package_count": len(shipment_data["items"])
            }
            
            # Add optional properties
            optional_fields = [
                "carrier_id", "service_level", "tracking_number", 
                "estimated_delivery_date", "shipping_cost", "insurance_value",
                "special_instructions", "reference_number", "customer_id"
            ]
            
            for field in optional_fields:
                if field in shipment_data:
                    shipment_properties[field] = shipment_data[field]
            
            if carrier_name:
                shipment_properties["carrier_name"] = carrier_name
            
            # Add metadata if provided
            if metadata:
                shipment_properties["metadata"] = metadata
            
            # Create shipment node
            shipment_id = self.neural_fabric.create_node(
                node_type="shipment",
                properties=shipment_properties
            )
            
            # Connect to carrier if specified
            if carrier_id:
                self.neural_fabric.connect_nodes(
                    source_id=shipment_id,
                    target_id=carrier_id,
                    relation_type="shipped_by"
                )
            
            # Connect to products
            for item in shipment_data["items"]:
                self.neural_fabric.connect_nodes(
                    source_id=shipment_id,
                    target_id=item["product_id"],
                    relation_type="contains"
                )
            
            # Connect to customer if specified
            if "customer_id" in shipment_data:
                customer_id = shipment_data["customer_id"]
                customer = self.neural_fabric.get_node(customer_id)
                if customer and customer.node_type == "customer":
                    self.neural_fabric.connect_nodes(
                        source_id=shipment_id,
                        target_id=customer_id,
                        relation_type="ships_to"
                    )
            
            # Connect to order if specified
            if "order_id" in shipment_data:
                order_id = shipment_data["order_id"]
                order = self.neural_fabric.get_node(order_id)
                if order and order.node_type == "order":
                    self.neural_fabric.connect_nodes(
                        source_id=shipment_id,
                        target_id=order_id,
                        relation_type="fulfills"
                    )
            
            # Publish event
            self.event_bus.publish(
                event_type="shipment.created",
                payload={
                    "shipment_id": shipment_id,
                    "shipment_number": shipment_number,
                    "origin": shipment_data["origin"],
                    "destination": shipment_data["destination"],
                    "ship_date": shipment_data["ship_date"],
                    "carrier_id": carrier_id
                }
            )
            
            logger.info(f"Created shipment: {shipment_number} (ID: {shipment_id})")
            
            return {
                "action": "create",
                "shipment_id": shipment_id,
                "shipment_number": shipment_number,
                "status": "created"
            }
            
        elif action == "update":
            # Validate shipment ID
            if "shipment_id" not in shipment_data:
                raise ValueError("Missing shipment_id for update")
                
            shipment_id = shipment_data["shipment_id"]
            shipment = self.neural_fabric.get_node(shipment_id)
            
            if not shipment or shipment.node_type != "shipment":
                raise ValueError(f"Invalid shipment ID: {shipment_id}")
            
            # Check if shipment can be updated
            current_status = shipment.properties.get("status")
            if current_status in ["delivered", "cancelled"]:
                raise ValueError(f"Cannot update shipment with status: {current_status}")
            
            # Prepare update properties
            update_properties = {}
            updatable_fields = [
                "carrier_id", "service_level", "tracking_number", 
                "estimated_delivery_date", "shipping_cost", "special_instructions",
                "status", "actual_delivery_date", "proof_of_delivery"
            ]
            
            for field in updatable_fields:
                if field in shipment_data:
                    update_properties[field] = shipment_data[field]
            
            # Update carrier name if carrier_id changed
            if "carrier_id" in update_properties:
                carrier_id = update_properties["carrier_id"]
                carrier = self.neural_fabric.get_node(carrier_id)
                if carrier and carrier.node_type == "carrier":
                    update_properties["carrier_name"] = carrier.properties.get("name")
                    
                    # Update carrier relationship
                    carrier_connections = self.neural_fabric.get_connected_nodes(
                        node_id=shipment_id,
                        relation_type="shipped_by"
                    )
                    
                    if "shipped_by" in carrier_connections:
                        for old_carrier in carrier_connections["shipped_by"]:
                            self.neural_fabric.disconnect_nodes(
                                source_id=shipment_id,
                                target_id=old_carrier.id,
                                relation_type="shipped_by"
                            )
                    
                    self.neural_fabric.connect_nodes(
                        source_id=shipment_id,
                        target_id=carrier_id,
                        relation_type="shipped_by"
                    )
            
            # Add metadata if provided
            if metadata:
                update_properties["metadata"] = metadata
                
            # Update last modified
            update_properties["last_modified"] = datetime.now().isoformat()
            
            # Update shipment node
            self.neural_fabric.update_node(
                node_id=shipment_id,
                properties=update_properties
            )
            
            # If status changed to delivered, update relevant data
            if "status" in update_properties and update_properties["status"] == "delivered":
                if "actual_delivery_date" not in update_properties:
                    update_properties["actual_delivery_date"] = datetime.now().date().isoformat()
                    self.neural_fabric.update_node(
                        node_id=shipment_id,
                        properties={"actual_delivery_date": update_properties["actual_delivery_date"]}
                    )
                
                # Publish delivery event
                self.event_bus.publish(
                    event_type="shipment.delivered",
                    payload={
                        "shipment_id": shipment_id,
                        "shipment_number": shipment.properties.get("shipment_number"),
                        "actual_delivery_date": update_properties.get("actual_delivery_date"),
                        "proof_of_delivery": update_properties.get("proof_of_delivery")
                    }
                )
            
            # Publish update event
            self.event_bus.publish(
                event_type="shipment.updated",
                payload={
                    "shipment_id": shipment_id,
                    "shipment_number": shipment.properties.get("shipment_number"),
                    "updates": update_properties
                }
            )
            
            logger.info(f"Updated shipment ID {shipment_id}: {update_properties}")
            
            return {
                "action": "update",
                "shipment_id": shipment_id,
                "shipment_number": shipment.properties.get("shipment_number"),
                "updates": update_properties
            }
            
        elif action == "cancel":
            # Validate shipment ID
            if "shipment_id" not in shipment_data:
                raise ValueError("Missing shipment_id for cancel")
                
            shipment_id = shipment_data["shipment_id"]
            shipment = self.neural_fabric.get_node(shipment_id)
            
            if not shipment or shipment.node_type != "shipment":
                raise ValueError(f"Invalid shipment ID: {shipment_id}")
            
            # Check if shipment can be cancelled
            current_status = shipment.properties.get("status")
            if current_status in ["delivered", "cancelled"]:
                raise ValueError(f"Cannot cancel shipment with status: {current_status}")
            
            # Cancel shipment
            cancel_properties = {
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat(),
                "cancellation_reason": shipment_data.get("reason", "Not specified")
            }
            
            # Update shipment node
            self.neural_fabric.update_node(
                node_id=shipment_id,
                properties=cancel_properties
            )
            
            # Publish event
            self.event_bus.publish(
                event_type="shipment.cancelled",
                payload={
                    "shipment_id": shipment_id,
                    "shipment_number": shipment.properties.get("shipment_number"),
                    "reason": shipment_data.get("reason")
                }
            )
            
            logger.info(f"Cancelled shipment ID {shipment_id}")
            
            return {
                "action": "cancel",
                "shipment_id": shipment_id,
                "shipment_number": shipment.properties.get("shipment_number"),
                "status": "cancelled"
            }
        else:
            raise ValueError(f"Unknown shipment action: {action}")
    
    def create_shipping_plan(self,
                           order_ids: List[str],
                           optimization_criteria: Optional[List[str]] = None,
                           constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an optimized shipping plan for orders.
        
        Args:
            order_ids: List of order IDs to plan shipments for
            optimization_criteria: Optional list of criteria to optimize for
            constraints: Optional shipping constraints
            
        Returns:
            Shipping plan details
        """
        # Set default optimization criteria
        if not optimization_criteria:
            optimization_criteria = ["cost", "delivery_time"]
        
        # Set default constraints
        if not constraints:
            constraints = {}
        
        # Validate orders
        validated_orders = []
        for order_id in order_ids:
            order = self.neural_fabric.get_node(order_id)
            if not order or order.node_type != "order":
                logger.warning(f"Invalid order ID: {order_id}")
                continue
            
            # Check if order is eligible for shipping
            order_status = order.properties.get("status")
            if order_status not in ["confirmed", "processing", "ready_to_ship"]:
                logger.warning(f"Order {order_id} has status {order_status}, not eligible for shipping")
                continue
            
            validated_orders.append(order)
        
        if not validated_orders:
            raise ValueError("No valid orders found for shipping plan")
        
        # Group orders by destination location for optimization
        location_groups = {}
        for order in validated_orders:
            # Extract shipping address key (simplified for example)
            shipping_address = order.properties.get("shipping_address", {})
            if isinstance(shipping_address, dict):
                location_key = (
                    shipping_address.get("postal_code", "") + 
                    shipping_address.get("city", "") + 
                    shipping_address.get("country", "")
                )
            else:
                location_key = str(shipping_address)
            
            if location_key not in location_groups:
                location_groups[location_key] = []
            
            location_groups[location_key].append(order)
        
        # Create shipping plan
        shipping_plan = []
        
        for location_key, location_orders in location_groups.items():
            # Determine if orders can be consolidated
            can_consolidate = all(
                order.properties.get("allow_partial_shipment", True) for order in location_orders
            )
            
            if can_consolidate and len(location_orders) > 1 and "consolidate" in optimization_criteria:
                # Create a consolidated shipment plan
                consolidated_items = []
                customer_ids = set()
                order_refs = []
                
                for order in location_orders:
                    order_items = order.properties.get("items", [])
                    customer_id = order.properties.get("customer_id")
                    order_number = order.properties.get("order_number")
                    
                    if customer_id:
                        customer_ids.add(customer_id)
                    
                    order_refs.append({
                        "order_id": order.id,
                        "order_number": order_number
                    })
                    
                    # Consolidate items
                    for item in order_items:
                        product_id = item.get("product_id")
                        quantity = item.get("quantity", 0)
                        
                        # Find if item already exists in consolidated list
                        existing_item = next(
                            (i for i in consolidated_items if i.get("product_id") == product_id),
                            None
                        )
                        
                        if existing_item:
                            existing_item["quantity"] += quantity
                            existing_item["orders"].append(order.id)
                        else:
                            consolidated_items.append({
                                "product_id": product_id,
                                "quantity": quantity,
                                "orders": [order.id]
                            })
                
                # Determine origin warehouse (simplified)
                origin_warehouse = self._determine_best_warehouse(consolidated_items, location_key)
                
                # Add consolidated shipment to plan
                shipping_plan.append({
                    "type": "consolidated",
                    "origin": {
                        "warehouse_id": origin_warehouse.get("id") if origin_warehouse else None,
                        "warehouse_name": origin_warehouse.get("name") if origin_warehouse else "Unknown"
                    },
                    "destination": location_orders[0].properties.get("shipping_address"),
                    "customer_ids": list(customer_ids),
                    "orders": order_refs,
                    "items": consolidated_items,
                    "consolidation_factor": len(location_orders)
                })
            else:
                # Create individual shipment plans
                for order in location_orders:
                    order_items = order.properties.get("items", [])
                    customer_id = order.properties.get("customer_id")
                    order_number = order.properties.get("order_number")
                    
                    # Convert order items to shipping items format
                    shipping_items = []
                    for item in order_items:
                        product_id = item.get("product_id")
                        quantity = item.get("quantity", 0)
                        
                        shipping_items.append({
                            "product_id": product_id,
                            "quantity": quantity,
                            "orders": [order.id]
                        })
                    
                    # Determine origin warehouse
                    origin_warehouse = self._determine_best_warehouse(shipping_items, location_key)
                    
                    # Add individual shipment to plan
                    shipping_plan.append({
                        "type": "individual",
                        "origin": {
                            "warehouse_id": origin_warehouse.get("id") if origin_warehouse else None,
                            "warehouse_name": origin_warehouse.get("name") if origin_warehouse else "Unknown"
                        },
                        "destination": order.properties.get("shipping_address"),
                        "customer_id": customer_id,
                        "order": {
                            "order_id": order.id,
                            "order_number": order_number
                        },
                        "items": shipping_items
                    })
        
        # Optimize carrier selection and delivery options
        for shipment_plan in shipping_plan:
            carrier_options = self._get_carrier_options(
                shipment_plan,
                optimization_criteria,
                constraints
            )
            
            shipment_plan["carrier_options"] = carrier_options
            
            # Select the best carrier option
            if carrier_options:
                best_option = carrier_options[0]
                shipment_plan["carrier"] = best_option["carrier"]
                shipment_plan["shipping_cost"] = best_option["cost"]
                shipment_plan["delivery_time"] = best_option["delivery_time"]
            else:
                shipment_plan["carrier"] = None
                shipment_plan["shipping_cost"] = None
                shipment_plan["delivery_time"] = None       