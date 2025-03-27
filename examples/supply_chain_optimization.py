"""
Supply Chain Optimization Example for NeuroERP.

This example demonstrates how to implement supply chain optimization workflows using the NeuroERP system:
1. Managing products and warehouses
2. Optimizing inventory levels
3. Forecasting demand and planning procurement
4. Route optimization for shipping
5. AI-driven supply chain insights
"""

import sys
import os
import json
from datetime import datetime, timedelta
import logging
import uuid
import random
import math

# Add parent directory to path to import from neuroerp package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neuroerp.core.config import Config
from neuroerp.core.event_bus import EventBus
from neuroerp.core.neural_fabric import NeuralFabric
from neuroerp.agents.supply_chain.inventory_agent import InventoryAgent
from neuroerp.agents.supply_chain.logistics_agent import LogisticsAgent
from neuroerp.data.knowledge_graph import KnowledgeGraph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupplyChainOptimizationExample:
    """Example implementation of supply chain optimization in NeuroERP."""
    
    def __init__(self):
        """Initialize the example with necessary components."""
        # Core components
        self.config = Config()
        self.event_bus = EventBus()
        self.neural_fabric = NeuralFabric()
        self.knowledge_graph = KnowledgeGraph(neural_fabric=self.neural_fabric)
        
        # Supply chain agents
        self.inventory_agent = InventoryAgent()
        self.logistics_agent = LogisticsAgent()
        
        # Sample data storage
        self.products = {}
        self.warehouses = {}
        self.suppliers = {}
        self.carriers = {}
        self.inventory = {}
        self.shipments = {}
        
        # Register event handlers
        self._register_event_handlers()
        
        logger.info("Supply chain optimization example initialized")
    
    def _register_event_handlers(self):
        """Register event handlers for the example."""
        self.event_bus.subscribe("product.created", self._handle_product_created)
        self.event_bus.subscribe("warehouse.created", self._handle_warehouse_created)
        self.event_bus.subscribe("inventory.updated", self._handle_inventory_updated)
        self.event_bus.subscribe("inventory.below_threshold", self._handle_low_inventory)
        self.event_bus.subscribe("shipment.created", self._handle_shipment_created)
        self.event_bus.subscribe("shipment.delivered", self._handle_shipment_delivered)
        self.event_bus.subscribe("demand.forecasted", self._handle_demand_forecasted)
    
    def _handle_product_created(self, event):
        """Handle product creation events."""
        product_id = event.payload.get("product_id")
        name = event.payload.get("name")
        sku = event.payload.get("sku")
        category = event.payload.get("category")
        
        logger.info(f"New product created: {name} (SKU: {sku}, Category: {category})")
        
        # Store in local cache
        self.products[product_id] = {
            "name": name,
            "sku": sku,
            "category": category
        }
    
    def _handle_warehouse_created(self, event):
        """Handle warehouse creation events."""
        warehouse_id = event.payload.get("warehouse_id")
        name = event.payload.get("name")
        code = event.payload.get("code")
        location = event.payload.get("location")
        
        logger.info(f"New warehouse created: {name} (Code: {code}, Location: {location})")
        
        # Store in local cache
        self.warehouses[warehouse_id] = {
            "name": name,
            "code": code,
            "location": location
        }
    
    def _handle_inventory_updated(self, event):
        """Handle inventory update events."""
        product_id = event.payload.get("product_id")
        warehouse_id = event.payload.get("warehouse_id")
        quantity = event.payload.get("new_quantity")
        
        if product_id in self.products and warehouse_id in self.warehouses:
            product_name = self.products[product_id]["name"]
            warehouse_name = self.warehouses[warehouse_id]["name"]
            
            logger.info(f"Inventory updated for {product_name} at {warehouse_name}: {quantity} units")
            
            # Update local cache
            inventory_key = f"{product_id}:{warehouse_id}"
            self.inventory[inventory_key] = {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": quantity
            }
    
    def _handle_low_inventory(self, event):
        """Handle low inventory threshold events."""
        product_id = event.payload.get("product_id")
        warehouse_id = event.payload.get("warehouse_id")
        current_qty = event.payload.get("current_quantity")
        threshold = event.payload.get("threshold")
        
        if product_id in self.products and warehouse_id in self.warehouses:
            product_name = self.products[product_id]["name"]
            warehouse_name = self.warehouses[warehouse_id]["name"]
            
            logger.info(f"Low inventory alert! {product_name} at {warehouse_name}: {current_qty} units (Threshold: {threshold})")
            
            # Trigger reorder process
            self._trigger_reorder_process(product_id, warehouse_id)
    
    def _handle_shipment_created(self, event):
        """Handle shipment creation events."""
        shipment_id = event.payload.get("shipment_id")
        shipment_number = event.payload.get("shipment_number")
        origin = event.payload.get("origin")
        destination = event.payload.get("destination")
        
        logger.info(f"New shipment created: {shipment_number} ({origin} to {destination})")
        
        # Store in local cache
        self.shipments[shipment_id] = {
            "shipment_number": shipment_number,
            "origin": origin,
            "destination": destination,
            "status": "created"
        }
    
    def _handle_shipment_delivered(self, event):
        """Handle shipment delivery events."""
        shipment_id = event.payload.get("shipment_id")
        shipment_number = event.payload.get("shipment_number")
        
        if shipment_id in self.shipments:
            logger.info(f"Shipment delivered: {shipment_number}")
            
            # Update status in local cache
            self.shipments[shipment_id]["status"] = "delivered"
            self.shipments[shipment_id]["delivery_date"] = datetime.now().isoformat()
    
    def _handle_demand_forecasted(self, event):
        """Handle demand forecast events."""
        forecast_id = event.payload.get("forecast_id")
        product_id = event.payload.get("product_id")
        
        if product_id in self.products:
            product_name = self.products[product_id]["name"]
            logger.info(f"Demand forecast updated for {product_name} (Forecast ID: {forecast_id})")
    
    def _trigger_reorder_process(self, product_id, warehouse_id):
        """Trigger the reorder process for a product at a warehouse."""
        if product_id not in self.products or warehouse_id not in self.warehouses:
            return
            
        product_name = self.products[product_id]["name"]
        warehouse_name = self.warehouses[warehouse_id]["name"]
        
        logger.info(f"Triggering reorder process for {product_name} at {warehouse_name}")
        
        # In a real implementation, this would create a purchase order or transfer request
        # For this example, we'll just log the action
        logger.info(f"Reorder initiated for {product_name}")
    
    def run_complete_workflow(self):
        """Run a complete supply chain optimization workflow demonstrating the system's capabilities."""
        logger.info("Starting complete supply chain optimization workflow demonstration")
        
        # Step 1: Create suppliers
        self._create_suppliers()
        
        # Step 2: Create products
        self._create_products()
        
        # Step 3: Create warehouses
        self._create_warehouses()
        
        # Step 4: Create carriers
        self._create_carriers()
        
        # Step 5: Initialize inventory
        self._initialize_inventory()
        
        # Step 6: Optimize inventory levels
        self._optimize_inventory_levels()
        
        # Step 7: Forecast product demand
        self._forecast_product_demand()
        
        # Step 8: Create shipping plans
        self._create_shipping_plans()
        
        # Step 9: Optimize shipping routes
        self._optimize_shipping_routes()
        
        # Step 10: Generate supply chain insights
        self._generate_supply_chain_insights()
        
        logger.info("Supply chain optimization workflow demonstration completed")
    
    def _create_suppliers(self):
        """Create sample suppliers."""
        logger.info("Creating sample suppliers")
        
        # Sample supplier data
        suppliers_to_create = [
            {
                "name": "GlobalTech Manufacturing",
                "code": "GTM",
                "contact": {
                    "name": "John Smith",
                    "email": "john.smith@globaltech.com",
                    "phone": "555-123-4567"
                },
                "address": {
                    "street": "123 Industry Blvd",
                    "city": "Chicago",
                    "state": "IL",
                    "postal_code": "60601",
                    "country": "USA"
                },
                "lead_time_days": 14,
                "status": "active"
            },
            {
                "name": "EcoFriendly Packaging",
                "code": "ECO",
                "contact": {
                    "name": "Sarah Johnson",
                    "email": "sarah@ecofriendly.com",
                    "phone": "555-987-6543"
                },
                "address": {
                    "street": "456 Green Way",
                    "city": "Portland",
                    "state": "OR",
                    "postal_code": "97201",
                    "country": "USA"
                },
                "lead_time_days": 7,
                "status": "active"
            },
            {
                "name": "Asian Electronics Co.",
                "code": "AEC",
                "contact": {
                    "name": "Li Wei",
                    "email": "liwei@asianelectronics.com",
                    "phone": "86-10-5555-1234"
                },
                "address": {
                    "street": "789 Manufacturing Road",
                    "city": "Shenzhen",
                    "state": "Guangdong",
                    "postal_code": "518000",
                    "country": "China"
                },
                "lead_time_days": 21,
                "status": "active"
            },
            {
                "name": "European Quality Parts",
                "code": "EQP",
                "contact": {
                    "name": "Hans Mueller",
                    "email": "mueller@eqparts.eu",
                    "phone": "49-30-5555-9876"
                },
                "address": {
                    "street": "10 Precision Street",
                    "city": "Berlin",
                    "state": "Berlin",
                    "postal_code": "10115",
                    "country": "Germany"
                },
                "lead_time_days": 18,
                "status": "active"
            }
        ]
        
        # Create suppliers using knowledge graph
        for supplier_data in suppliers_to_create:
            supplier_id = self.knowledge_graph.create_entity(
                entity_type="Supplier",
                properties=supplier_data
            )
            
            self.suppliers[supplier_id] = supplier_data
            logger.info(f"Created supplier: {supplier_data['name']} (ID: {supplier_id})")
        
        logger.info(f"Created {len(self.suppliers)} suppliers")
    
    def _create_products(self):
        """Create sample products."""
        logger.info("Creating sample products")
        
        # Product categories
        categories = {
            "Electronics": ["Smartphone", "Laptop", "Tablet", "Smartwatch", "Headphones"],
            "Clothing": ["T-Shirt", "Jeans", "Dress", "Jacket", "Sweater"],
            "Home Goods": ["Couch", "Dining Table", "Bed Frame", "Desk Chair", "Lamp"],
            "Sporting Goods": ["Tennis Racket", "Basketball", "Yoga Mat", "Dumbbells", "Running Shoes"]
        }
        
        # Get supplier IDs for assignment
        supplier_ids = list(self.suppliers.keys())
        if not supplier_ids:
            logger.warning("No suppliers available to assign to products")
            return
        
        # Create products for each category
        product_count = 0
        for category_name, product_types in categories.items():
            for i, product_type in enumerate(product_types):
                # Generate product variants
                variants = 2  # Number of variants per product type
                for j in range(variants):
                    # Generate product data
                    variant_name = f"{random.choice(['Standard', 'Premium', 'Deluxe', 'Basic', 'Pro'])} {product_type}"
                    sku = f"{category_name[0:3]}-{product_type[0:3]}-{j+1:03d}".upper()
                    
                    product_data = {
                        "action": "create",
                        "product_data": {
                            "name": variant_name,
                            "sku": sku,
                            "category": category_name,
                            "description": f"{variant_name} - {category_name} product, Variant {j+1}",
                            "unit_price": round(random.uniform(10, 1000), 2),
                            "unit_of_measure": "EA",
                            "weight": round(random.uniform(0.1, 20), 2),
                            "dimensions": {
                                "length": round(random.uniform(5, 100), 2),
                                "width": round(random.uniform(5, 100), 2),
                                "height": round(random.uniform(1, 50), 2)
                            },
                            "supplier_id": random.choice(supplier_ids),
                            "lead_time_days": random.randint(3, 30),
                            "reorder_point": random.randint(10, 50),
                            "reorder_quantity": random.randint(50, 200)
                        }
                    }
                    
                    # Create product
                    result = self.inventory_agent.manage_product(**product_data)
                    if result.get("success"):
                        product_id = result["result"]["product_id"]
                        product_count += 1
                        
                        # Store in products cache
                        self.products[product_id] = {
                            "name": variant_name,
                            "sku": sku,
                            "category": category_name,
                            "unit_price": product_data["product_data"]["unit_price"],
                            "supplier_id": product_data["product_data"]["supplier_id"]
                        }
                        
                        logger.info(f"Created product: {variant_name} (SKU: {sku}, ID: {product_id})")
                    else:
                        logger.error(f"Failed to create product: {result.get('error')}")
        
        logger.info(f"Created {product_count} products in {len(categories)} categories")
    
    def _create_warehouses(self):
        """Create sample warehouses."""
        logger.info("Creating sample warehouses")
        
        # Sample warehouse locations
        warehouse_locations = [
            {
                "name": "East Coast Distribution Center",
                "code": "ECDC",
                "location": "Eastern US",
                "address": {
                    "street": "123 Fulfillment Ave",
                    "city": "Newark",
                    "state": "NJ",
                    "postal_code": "07101",
                    "country": "USA"
                },
                "capacity": 500000,
                "type": "distribution"
            },
            {
                "name": "West Coast Fulfillment Center",
                "code": "WCFC",
                "location": "Western US",
                "address": {
                    "street": "456 Shipping Blvd",
                    "city": "Oakland",
                    "state": "CA",
                    "postal_code": "94607",
                    "country": "USA"
                },
                "capacity": 450000,
                "type": "fulfillment"
            },
            {
                "name": "Central Regional Warehouse",
                "code": "CRW",
                "location": "Central US",
                "address": {
                    "street": "789 Logistics Pkwy",
                    "city": "Dallas",
                    "state": "TX",
                    "postal_code": "75201",
                    "country": "USA"
                },
                "capacity": 350000,
                "type": "regional"
            },
            {
                "name": "European Distribution Hub",
                "code": "EDH",
                "location": "Europe",
                "address": {
                    "street": "10 Warehouse Street",
                    "city": "Rotterdam",
                    "state": "South Holland",
                    "postal_code": "3011",
                    "country": "Netherlands"
                },
                "capacity": 400000,
                "type": "international"
            },
            {
                "name": "Asian Logistics Center",
                "code": "ALC",
                "location": "Asia",
                "address": {
                    "street": "42 Supply Chain Road",
                    "city": "Singapore",
                    "state": "Singapore",
                    "postal_code": "609961",
                    "country": "Singapore"
                },
                "capacity": 300000,
                "type": "international"
            }
        ]
        
        # Create warehouses
        for warehouse_data in warehouse_locations:
            management_data = {
                "action": "create",
                "warehouse_data": warehouse_data
            }
            
            result = self.inventory_agent.manage_warehouse(**management_data)
            if result.get("success"):
                warehouse_id = result["result"]["warehouse_id"]
                
                # Store in warehouses cache
                self.warehouses[warehouse_id] = {
                    "name": warehouse_data["name"],
                    "code": warehouse_data["code"],
                    "location": warehouse_data["location"],
                    "type": warehouse_data["type"]
                }
                
                logger.info(f"Created warehouse: {warehouse_data['name']} (Code: {warehouse_data['code']}, ID: {warehouse_id})")
            else:
                logger.error(f"Failed to create warehouse: {result.get('error')}")
        
        logger.info(f"Created {len(self.warehouses)} warehouses")
    
    def _create_carriers(self):
        """Create sample shipping carriers."""
        logger.info("Creating sample shipping carriers")
        
        # Sample carrier data
        carriers_to_create = [
            {
                "name": "FastShip Express",
                "code": "FSE",
                "type": "express",
                "contact_info": {
                    "name": "Customer Service",
                    "email": "service@fastship.com",
                    "phone": "800-555-1212"
                },
                "service_levels": ["Next Day", "2-Day", "Ground"],
                "tracking_url": "https://track.fastship.com/{tracking_number}"
            },
            {
                "name": "Global Logistics Co.",
                "code": "GLC",
                "type": "international",
                "contact_info": {
                    "name": "Shipping Department",
                    "email": "shipping@globallogistics.com",
                    "phone": "800-555-9876"
                },
                "service_levels": ["International Express", "International Economy", "Freight"],
                "tracking_url": "https://globallogistics.com/track/{tracking_number}"
            },
            {
                "name": "Value Parcel Service",
                "code": "VPS",
                "type": "economy",
                "contact_info": {
                    "name": "Support Team",
                    "email": "support@valueparcel.com",
                    "phone": "800-555-4321"
                },
                "service_levels": ["Standard Ground", "Economy"],
                "tracking_url": "https://valueparcel.com/track?num={tracking_number}"
            }
        ]
        
        # Create carriers
        for carrier_data in carriers_to_create:
            management_data = {
                "action": "create",
                "carrier_data": carrier_data
            }
            
            result = self.logistics_agent.manage_carrier(**management_data)
            if result.get("success"):
                carrier_id = result["result"]["carrier_id"]
                
                # Store in carriers cache
                self.carriers[carrier_id] = {
                    "name": carrier_data["name"],
                    "code": carrier_data["code"],
                    "type": carrier_data["type"],
                    "service_levels": carrier_data["service_levels"]
                }
                
                logger.info(f"Created carrier: {carrier_data['name']} (Code: {carrier_data['code']}, ID: {carrier_id})")
            else:
                logger.error(f"Failed to create carrier: {result.get('error')}")
        
        logger.info(f"Created {len(self.carriers)} carriers")
    
    def _initialize_inventory(self):
        """Initialize inventory levels for products across warehouses."""
        logger.info("Initializing inventory levels")
        
        if not self.products or not self.warehouses:
            logger.warning("No products or warehouses available for inventory initialization")
            return
        
        # Initialize inventory for each product in each warehouse
        inventory_count = 0
        for product_id, product_data in self.products.items():
            for warehouse_id, warehouse_data in self.warehouses.items():
                # Generate random inventory level
                initial_quantity = random.randint(20, 200)
                
                # Update inventory
                inventory_data = {
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "transaction_type": "receive",
                    "quantity": initial_quantity,
                    "reference": f"INIT-{product_data['sku']}",
                    "note": "Initial inventory setup"
                }
                
                result = self.inventory_agent.update_inventory(**inventory_data)
                if result.get("success"):
                    inventory_count += 1
                    
                    # Store in inventory cache
                    inventory_key = f"{product_id}:{warehouse_id}"
                    self.inventory[inventory_key] = {
                        "product_id": product_id,
                        "warehouse_id": warehouse_id,
                        "quantity": initial_quantity,
                        "product_name": product_data["name"],
                        "warehouse_name": warehouse_data["name"]
                    }
                    
                    logger.debug(f"Initialized inventory: {product_data['name']} at {warehouse_data['name']}: {initial_quantity} units")
                else:
                    logger.error(f"Failed to initialize inventory: {result.get('error')}")
        
        logger.info(f"Initialized {inventory_count} inventory records")
    
    def _optimize_inventory_levels(self):
        """Optimize inventory levels for products."""
        logger.info("Optimizing inventory levels")
        
        if not self.products or not self.warehouses or not self.inventory:
            logger.warning("No inventory available for optimization")
            return
        
        # Get high-value products for optimization
        product_ids = []
        for product_id, product_data in self.products.items():
            if product_data.get("unit_price", 0) > 100:  # Focus on high-value items
                product_ids.append(product_id)
        
        if not product_ids:
            product_ids = list(self.products.keys())[:5]  # Use first 5 products as fallback
        
        # Optimize inventory levels
        optimization_data = {
            "product_ids": product_ids,
            "parameters": {
                "method": "economic_order_quantity",
                "holding_cost_percentage": 0.25,  # 25% annual holding cost
                "order_cost": 50,  # $50 per order
                "service_level": 0.95  # 95% service level
            }
        }
        
        result = self.inventory_agent.optimize_stock_levels(**optimization_data)
        if result.get("success"):
            optimization_id = result["result"]["optimization_id"]
            logger.info(f"Completed inventory optimization (ID: {optimization_id})")
            
            # Log optimization results
            optimizations = result["result"].get("optimizations", [])
            
            for opt in optimizations:
                product_id = opt.get("product_id")
                product_name = self.products.get(product_id, {}).get("name", "Unknown Product")
                
                logger.info(f"Optimization for {product_name}:")
                logger.info(f"  Recommended Reorder Point: {opt.get('reorder_point')}")
                logger.info(f"  Recommended Order Quantity: {opt.get('order_quantity')}")
                logger.info(f"  Safety Stock: {opt.get('safety_stock')}")
                
                # Update product with optimized values
                product_update_data = {
                    "action": "update",
                    "product_data": {
                        "product_id": product_id,
                        "reorder_point": opt.get("reorder_point"),
                        "reorder_quantity": opt.get("order_quantity")
                    }
                }
                
                update_result = self.inventory_agent.manage_product(**product_update_data)
                if update_result.get("success"):
                    logger.info(f"Updated inventory parameters for {product_name}")
                else:
                    logger.error(f"Failed to update inventory parameters: {update_result.get('error')}")
        else:
            logger.error(f"Failed to optimize inventory levels: {result.get('error')}")
    
    def _forecast_product_demand(self):
        """Forecast product demand for planning."""
        logger.info("Forecasting product demand")
        
        if not self.products:
            logger.warning("No products available for demand forecasting")
            return
        
        # Select products for forecasting (for the example, we'll just use 5 random products)
        product_ids = random.sample(list(self.products.keys()), min(5, len(self.products)))
        
        # Build forecast parameters
        today = datetime.now().date()
        start_date = today.isoformat()
        end_date = (today + timedelta(days=90)).isoformat()  # Forecast 90 days
        
        # Create demand forecasts for each product
        for product_id in product_ids:
            product_data = self.products.get(product_id, {})
            
            forecast_data = {
                "product_id": product_id,
                "start_date": start_date,
                "end_date": end_date,
                "forecast_units": "day",
                "parameters": {
                    "method": "time_series",
                    "include_seasonality": True,
                    "confidence_level": 0.95
                }
            }
            
            result = self.inventory_agent.forecast_demand(**forecast_data)
            if result.get("success"):
                forecast_id = result["result"]["forecast_id"]
                logger.info(f"Generated demand forecast for {product_data.get('name')} (ID: {forecast_id})")
                
                # Log forecast summary
                forecast_summary = result["result"].get("summary", {})
                logger.info(f"  Average Daily Demand: {forecast_summary.get('avg_daily_demand')}")
                logger.info(f"  Peak Demand: {forecast_summary.get('peak_demand')} on {forecast_summary.get('peak_date')}")
                logger.info(f"  Total Forecast Quantity: {forecast_summary.get('total_quantity')}")
            else:
                logger.error(f"Failed to forecast demand: {result.get('error')}")
    
    def _create_shipping_plans(self):
        """Create shipping plans for order fulfillment."""
        logger.info("Creating shipping plans")
        
        if not self.products or not self.warehouses:
            logger.warning("No products or warehouses available for shipping plans")
            return
        
        # Create mock orders
        mock_orders = []
        for i in range(5):
            # Generate random destination
            destination = {
                "name": f"Customer {i+1}",
                "address": {
                    "street": f"{random.randint(100, 999)} Main St",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "postal_code": f"{random.randint(10000, 99999)}",
                    "country": "USA"
                }
            }
            
            # Generate random order items (1-5 items per order)
            items = []
            product_sample = random.sample(list(self.products.items()), random.randint(1, 5))
            
            for product_id, product_data in product_sample:
                items.append({
                    "product_id": product_id,
                    "quantity": random.randint(1, 10)
                })
            
            # Create order
            order = {
                "id": str(uuid.uuid4()),
                "customer_name": destination["name"],
                "shipping_address": destination["address"],
                "items": items
            }
            
            mock_orders.append(order)
        
        # Create shipping plan for orders
        shipping_plan_data = {
            "order_ids": [order["id"] for order in mock_orders],
            "optimization_criteria": ["cost", "delivery_time", "consolidate"],
            "constraints": {
                "max_transit_days": 5,
                "delivery_by": (datetime.now() + timedelta(days=7)).isoformat()
            }
        }
        
        result = self.logistics_agent.create_shipping_plan(**shipping_plan_data)
        if result.get("success"):
            plan_id = result["result"]["plan_id"]
            logger.info(f"Created shipping plan (ID: {plan_id})")
            
            # Log shipping plan details
            shipments = result["result"].get("shipments", [])
            
            for shipment in shipments:
                logger.info(f"Shipment Plan: {shipment.get('type')} from {shipment.get('origin', {}).get('warehouse_name')}")
                logger.info(f"  Destination: {shipment.get('destination', {}).get('name')}")
                logger.info(f"  Shipping Cost: {shipment.get('shipping_cost')}")
                logger.info(f"  Estimated Delivery: {shipment.get('estimated_delivery')}")