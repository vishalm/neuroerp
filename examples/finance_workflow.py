"""
Finance Workflow Example for NeuroERP.

This example demonstrates how to implement common financial workflows using the NeuroERP system:
1. Creating customers and invoices
2. Processing payments
3. Reconciling accounts
4. Generating financial reports
5. Forecasting cash flow
"""

import sys
import os
import json
from datetime import datetime, timedelta
import logging
import uuid
import random

# Add parent directory to path to import from neuroerp package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neuroerp.core.config import Config
from neuroerp.core.event_bus import EventBus
from neuroerp.core.neural_fabric import NeuralFabric
from neuroerp.agents.finance.accounting_agent import AccountingAgent
from neuroerp.agents.finance.forecasting_agent import ForecastingAgent
from neuroerp.data.knowledge_graph import KnowledgeGraph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinanceWorkflowExample:
    """Example implementation of finance workflows in NeuroERP."""
    
    def __init__(self):
        """Initialize the example with necessary components."""
        # Core components
        self.config = Config()
        self.event_bus = EventBus()
        self.neural_fabric = NeuralFabric()
        self.knowledge_graph = KnowledgeGraph(neural_fabric=self.neural_fabric)
        
        # Finance agents
        self.accounting_agent = AccountingAgent()
        self.forecasting_agent = ForecastingAgent()
        
        # Sample data storage
        self.customers = {}
        self.accounts = {}
        self.invoices = {}
        self.payments = {}
        
        # Register event handlers
        self._register_event_handlers()
        
        logger.info("Finance workflow example initialized")
    
    def _register_event_handlers(self):
        """Register event handlers for the example."""
        self.event_bus.subscribe("invoice.created", self._handle_invoice_created)
        self.event_bus.subscribe("payment.processed", self._handle_payment_processed)
        self.event_bus.subscribe("account.reconciled", self._handle_account_reconciled)
        self.event_bus.subscribe("forecast.created", self._handle_forecast_created)
    
    def _handle_invoice_created(self, event):
        """Handle invoice created events."""
        invoice_id = event.payload.get("invoice_id")
        invoice_number = event.payload.get("invoice_number")
        customer_id = event.payload.get("customer_id")
        total = event.payload.get("total")
        
        logger.info(f"New invoice created: #{invoice_number} for customer {customer_id}, amount: ${total}")
        
        # Store in local cache
        self.invoices[invoice_id] = {
            "invoice_number": invoice_number,
            "customer_id": customer_id,
            "total": total,
            "status": "open"
        }
    
    def _handle_payment_processed(self, event):
        """Handle payment processed events."""
        payment_id = event.payload.get("payment_id")
        amount = event.payload.get("amount")
        reference = event.payload.get("reference")
        
        logger.info(f"Payment processed: #{reference}, amount: ${amount}")
        
        # Store in local cache
        self.payments[payment_id] = {
            "reference": reference,
            "amount": amount,
            "date": datetime.now().isoformat()
        }
    
    def _handle_account_reconciled(self, event):
        """Handle account reconciliation events."""
        account_id = event.payload.get("account_id")
        status = event.payload.get("status")
        difference = event.payload.get("difference")
        
        logger.info(f"Account {account_id} reconciled with status: {status}, difference: ${difference:.2f}")
    
    def _handle_forecast_created(self, event):
        """Handle forecast creation events."""
        forecast_id = event.payload.get("forecast_id")
        forecast_type = event.payload.get("forecast_type")
        
        logger.info(f"New {forecast_type} forecast created: {forecast_id}")
    
    def run_complete_workflow(self):
        """Run a complete finance workflow demonstrating the system's capabilities."""
        logger.info("Starting complete finance workflow demonstration")
        
        # Step 1: Create chart of accounts
        self._create_chart_of_accounts()
        
        # Step 2: Create customers
        self._create_customers()
        
        # Step 3: Create and send invoices
        self._create_invoices()
        
        # Step 4: Process payments
        self._process_payments()
        
        # Step 5: Reconcile accounts
        self._reconcile_accounts()
        
        # Step 6: Generate financial reports
        self._generate_financial_reports()
        
        # Step 7: Create forecasts
        self._create_forecasts()
        
        # Step 8: Demonstrate anomaly detection
        self._detect_anomalies()
        
        logger.info("Finance workflow demonstration completed")
    
    def _create_chart_of_accounts(self):
        """Create a sample chart of accounts."""
        logger.info("Creating chart of accounts")
        
        # Get existing accounts
        accounts = self.neural_fabric.query_nodes(
            node_type="account",
            limit=1000
        )
        
        if accounts:
            logger.info(f"Found {len(accounts)} existing accounts")
            self.accounts = {account.id: account.properties for account in accounts}
            return
        
        # Create basic accounts
        accounts_to_create = [
            # Asset accounts
            {"action": "create", "account_data": {"number": "1000", "name": "Cash", "type": "asset", "subtype": "current", "is_bank_account": True}},
            {"action": "create", "account_data": {"number": "1100", "name": "Accounts Receivable", "type": "asset", "subtype": "current"}},
            {"action": "create", "account_data": {"number": "1200", "name": "Inventory", "type": "asset", "subtype": "current"}},
            
            # Liability accounts
            {"action": "create", "account_data": {"number": "2000", "name": "Accounts Payable", "type": "liability", "subtype": "current"}},
            {"action": "create", "account_data": {"number": "2100", "name": "Accrued Expenses", "type": "liability", "subtype": "current"}},
            
            # Equity accounts
            {"action": "create", "account_data": {"number": "3000", "name": "Retained Earnings", "type": "equity"}},
            
            # Revenue accounts
            {"action": "create", "account_data": {"number": "4000", "name": "Sales Revenue", "type": "revenue"}},
            {"action": "create", "account_data": {"number": "4100", "name": "Service Revenue", "type": "revenue"}},
            
            # Expense accounts
            {"action": "create", "account_data": {"number": "5000", "name": "Cost of Goods Sold", "type": "expense", "subtype": "cogs"}},
            {"action": "create", "account_data": {"number": "6000", "name": "Salaries and Wages", "type": "expense", "subtype": "operating"}},
            {"action": "create", "account_data": {"number": "6100", "name": "Rent Expense", "type": "expense", "subtype": "operating"}},
            {"action": "create", "account_data": {"number": "6200", "name": "Utilities Expense", "type": "expense", "subtype": "operating"}},
            {"action": "create", "account_data": {"number": "8000", "name": "Interest Expense", "type": "expense", "subtype": "financial"}},
        ]
        
        for account_info in accounts_to_create:
            result = self.accounting_agent.manage_account(**account_info)
            if result.get("success"):
                account_id = result["result"]["account_id"]
                account_data = account_info["account_data"]
                self.accounts[account_id] = account_data
                logger.info(f"Created account: {account_data['number']} - {account_data['name']}")
            else:
                logger.error(f"Failed to create account: {result.get('error')}")
        
        logger.info(f"Created {len(self.accounts)} accounts")
    
    def _create_customers(self):
        """Create sample customers."""
        logger.info("Creating sample customers")
        
        # Sample customer data
        customers_to_create = [
            {
                "name": "Acme Corporation",
                "email": "accounts@acme.com",
                "phone": "555-123-4567",
                "address": {
                    "street": "123 Main St",
                    "city": "Metropolis",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                },
                "type": "business",
                "status": "active"
            },
            {
                "name": "TechNova Solutions",
                "email": "billing@technova.com",
                "phone": "555-987-6543",
                "address": {
                    "street": "456 Innovation Way",
                    "city": "Silicon Valley",
                    "state": "CA",
                    "postal_code": "94025",
                    "country": "USA"
                },
                "type": "business",
                "status": "active"
            },
            {
                "name": "Global Retail Inc.",
                "email": "accounting@globalretail.com",
                "phone": "555-789-0123",
                "address": {
                    "street": "789 Commerce Blvd",
                    "city": "Chicago",
                    "state": "IL",
                    "postal_code": "60601",
                    "country": "USA"
                },
                "type": "business",
                "status": "active"
            },
        ]
        
        # Create customers using knowledge graph
        for customer_data in customers_to_create:
            customer_id = self.knowledge_graph.create_entity(
                entity_type="Customer",
                properties=customer_data
            )
            
            self.customers[customer_id] = customer_data
            logger.info(f"Created customer: {customer_data['name']} (ID: {customer_id})")
        
        logger.info(f"Created {len(self.customers)} customers")
    
    def _create_invoices(self):
        """Create sample invoices for customers."""
        logger.info("Creating sample invoices")
        
        if not self.customers:
            logger.warning("No customers available to create invoices")
            return
        
        # Create invoices for each customer
        for customer_id, customer_data in self.customers.items():
            # Create 2-3 invoices per customer
            num_invoices = random.randint(2, 3)
            
            for i in range(num_invoices):
                # Generate invoice items
                items = []
                num_items = random.randint(1, 5)
                
                for j in range(num_items):
                    item = {
                        "description": f"Product {j+1}",
                        "quantity": random.randint(1, 10),
                        "price": round(random.uniform(50, 500), 2)
                    }
                    items.append(item)
                
                # Calculate due date (15-30 days from now)
                due_days = random.randint(15, 30)
                today = datetime.now().date()
                due_date = (today + timedelta(days=due_days)).isoformat()
                
                # Create the invoice
                invoice_data = {
                    "customer_id": customer_id,
                    "date": today.isoformat(),
                    "due_date": due_date,
                    "items": items,
                    "terms": "Net 30"
                }
                
                result = self.accounting_agent.create_invoice(**invoice_data)
                if result.get("success"):
                    invoice_id = result["result"]["invoice_id"]
                    invoice_number = result["result"]["invoice_number"]
                    invoice_total = result["result"]["total"]
                    
                    self.invoices[invoice_id] = {
                        "invoice_number": invoice_number,
                        "customer_id": customer_id,
                        "customer_name": customer_data["name"],
                        "date": today.isoformat(),
                        "due_date": due_date,
                        "total": invoice_total,
                        "status": "open"
                    }
                    
                    logger.info(f"Created invoice {invoice_number} for {customer_data['name']}, amount: ${invoice_total:.2f}")
                else:
                    logger.error(f"Failed to create invoice: {result.get('error')}")
        
        logger.info(f"Created {len(self.invoices)} invoices")
    
    def _process_payments(self):
        """Process payments for some of the invoices."""
        logger.info("Processing payments for invoices")
        
        if not self.invoices:
            logger.warning("No invoices available to process payments")
            return
        
        # Find bank account for payments
        cash_account_id = None
        ar_account_id = None
        
        for account_id, account_data in self.accounts.items():
            if account_data["name"] == "Cash":
                cash_account_id = account_id
            elif account_data["name"] == "Accounts Receivable":
                ar_account_id = account_id
        
        if not cash_account_id or not ar_account_id:
            logger.error("Could not find Cash or Accounts Receivable accounts")
            return
        
        # Pay about 70% of invoices
        invoices_to_pay = random.sample(list(self.invoices.items()), int(len(self.invoices) * 0.7))
        
        for invoice_id, invoice_data in invoices_to_pay:
            # Sometimes pay the full amount, sometimes partial
            full_payment = random.random() < 0.8
            
            if full_payment:
                payment_amount = invoice_data["total"]
            else:
                # Pay 25-75% of the invoice
                payment_percent = random.uniform(0.25, 0.75)
                payment_amount = round(invoice_data["total"] * payment_percent, 2)
            
            # Create payment
            payment_data = {
                "payment_type": "customer",
                "date": datetime.now().date().isoformat(),
                "amount": payment_amount,
                "source_account_id": cash_account_id,
                "reference": f"PMT-{invoice_data['invoice_number']}",
                "description": f"Payment for invoice {invoice_data['invoice_number']}",
                "metadata": {
                    "invoice_id": invoice_id,
                    "customer_id": invoice_data["customer_id"]
                }
            }
            
            result = self.accounting_agent.process_payment(**payment_data)
            if result.get("success"):
                payment_id = result["result"]["payment_id"]
                self.payments[payment_id] = {
                    "reference": result["result"]["reference"],
                    "amount": payment_amount,
                    "invoice_id": invoice_id,
                    "customer_id": invoice_data["customer_id"],
                    "date": payment_data["date"]
                }
                
                # Update invoice status in our local cache
                if full_payment:
                    self.invoices[invoice_id]["status"] = "paid"
                else:
                    self.invoices[invoice_id]["status"] = "partial"
                
                logger.info(f"Processed payment of ${payment_amount:.2f} for invoice {invoice_data['invoice_number']}")
            else:
                logger.error(f"Failed to process payment: {result.get('error')}")
        
        logger.info(f"Processed {len(self.payments)} payments")
    
    def _reconcile_accounts(self):
        """Reconcile accounts with simulated statement balances."""
        logger.info("Reconciling accounts")
        
        # Find bank account for reconciliation
        cash_account_id = None
        
        for account_id, account_data in self.accounts.items():
            if account_data["name"] == "Cash":
                cash_account_id = account_id
                break
        
        if not cash_account_id:
            logger.error("Could not find Cash account for reconciliation")
            return
        
        # Get all transactions affecting this account
        cash_account = self.neural_fabric.get_node(cash_account_id)
        if not cash_account:
            logger.error("Could not retrieve Cash account node")
            return
        
        system_balance = cash_account.properties.get("balance", 0)
        
        # Get a list of transactions for this account
        # In a real scenario, we would match these against a bank statement
        transactions = self.neural_fabric.query_nodes(
            node_type="transaction",
            limit=1000
        )
        
        # Filter for transactions affecting cash account
        cash_transactions = []
        for tx in transactions:
            entries = self.neural_fabric.get_connected_nodes(
                node_id=tx.id,
                relation_type="part_of_inverse"
            )
            
            if "part_of_inverse" in entries:
                for entry in entries["part_of_inverse"]:
                    if entry.properties.get("account_id") == cash_account_id:
                        cash_transactions.append(tx.id)
                        break
        
        # Simulate a statement balance (slightly different from system balance)
        statement_balance = system_balance
        
        # Sometimes introduce a small difference to simulate reconciliation issues
        if random.random() < 0.3:
            # Small difference (positive or negative)
            difference = round(random.uniform(-100, 100), 2)
            statement_balance += difference
        
        # Perform reconciliation
        reconciliation_data = {
            "account_id": cash_account_id,
            "statement_balance": statement_balance,
            "statement_date": datetime.now().date().isoformat(),
            "reconciled_transactions": cash_transactions
        }
        
        result = self.accounting_agent.reconcile_accounts(**reconciliation_data)
        if result.get("success"):
            reconciliation_id = result["result"]["reconciliation_id"]
            status = result["result"]["status"]
            difference = result["result"]["difference"]
            
            logger.info(f"Completed account reconciliation (ID: {reconciliation_id})")
            logger.info(f"Status: {status}, Difference: ${difference:.2f}")
            
            # If there's a difference, create adjustment
            if abs(difference) > 0.01 and status == "unbalanced":
                logger.info(f"Creating adjustment for ${difference:.2f}")
                
                # Find an appropriate offset account
                offset_account_id = None
                for account_id, account_data in self.accounts.items():
                    if account_data["name"] == "Retained Earnings":
                        offset_account_id = account_id
                        break
                
                if offset_account_id:
                    adjustment_data = {
                        "adjustments": [
                            {
                                "amount": difference,
                                "description": "Reconciliation adjustment",
                                "reason": "Bank reconciliation difference",
                                "offset_account_id": offset_account_id
                            }
                        ]
                    }
                    
                    # Add adjustments to reconciliation
                    updated_result = self.accounting_agent.reconcile_accounts(
                        **{**reconciliation_data, **adjustment_data}
                    )
                    
                    if updated_result.get("success"):
                        logger.info(f"Adjustment processed, new reconciliation status: {updated_result['result']['status']}")
                    else:
                        logger.error(f"Failed to process adjustment: {updated_result.get('error')}")
        else:
            logger.error(f"Failed to reconcile account: {result.get('error')}")
    
    def _generate_financial_reports(self):
        """Generate financial reports."""
        logger.info("Generating financial reports")
        
        # Set date ranges
        today = datetime.now().date()
        start_of_month = today.replace(day=1).isoformat()
        end_of_month = today.isoformat()
        
        # Generate income statement
        income_statement_data = {
            "report_type": "income_statement",
            "start_date": start_of_month,
            "end_date": end_of_month
        }
        
        result = self.accounting_agent.generate_financial_report(**income_statement_data)
        if result.get("success"):
            report_id = result["result"]["report_id"]
            logger.info(f"Generated income statement (ID: {report_id})")
            
            # Log some basic metrics from the report
            report_data = result["result"]["data"]
            total_revenue = report_data.get("total_revenue", 0)
            total_expenses = report_data.get("total_expenses", 0)
            net_income = report_data.get("net_income", 0)
            
            logger.info(f"Income Statement Summary:")
            logger.info(f"  Total Revenue: ${total_revenue:.2f}")
            logger.info(f"  Total Expenses: ${total_expenses:.2f}")
            logger.info(f"  Net Income: ${net_income:.2f}")
        else:
            logger.error(f"Failed to generate income statement: {result.get('error')}")
        
        # Generate balance sheet
        balance_sheet_data = {
            "report_type": "balance_sheet",
            "end_date": end_of_month
        }
        
        result = self.accounting_agent.generate_financial_report(**balance_sheet_data)
        if result.get("success"):
            report_id = result["result"]["report_id"]
            logger.info(f"Generated balance sheet (ID: {report_id})")
            
            # Log some basic metrics from the report
            report_data = result["result"]["data"]
            total_assets = report_data.get("total_assets", 0)
            total_liabilities = report_data.get("total_liabilities", 0)
            total_equity = report_data.get("total_equity", 0)
            
            logger.info(f"Balance Sheet Summary:")
            logger.info(f"  Total Assets: ${total_assets:.2f}")
            logger.info(f"  Total Liabilities: ${total_liabilities:.2f}")
            logger.info(f"  Total Equity: ${total_equity:.2f}")
        else:
            logger.error(f"Failed to generate balance sheet: {result.get('error')}")
    
    def _create_forecasts(self):
        """Create financial forecasts."""
        logger.info("Creating financial forecasts")
        
        # Set forecast parameters
        today = datetime.now().date()
        forecast_start = today.isoformat()
        forecast_end = (today + timedelta(days=180)).isoformat()  # 6 months
        
        # Create revenue forecast
        revenue_forecast_data = {
            "name": "6-Month Revenue Forecast",
            "start_date": forecast_start,
            "end_date": forecast_end,
            "forecast_type": "revenue",
            "forecast_units": "month",
            "parameters": {
                "method": "seasonal",
                "confidence_interval": 0.95,
                "include_seasonality": True
            }
        }
        
        result = self.forecasting_agent.create_forecast(**revenue_forecast_data)
        if result.get("success"):
            forecast_id = result["result"]["forecast_id"]
            logger.info(f"Created revenue forecast (ID: {forecast_id})")
        else:
            logger.error(f"Failed to create revenue forecast: {result.get('error')}")
        
        # Create cash flow forecast
        cashflow_forecast_data = {
            "name": "6-Month Cash Flow Forecast",
            "start_date": forecast_start,
            "end_date": forecast_end,
            "forecast_type": "cashflow",
            "forecast_units": "month",
            "parameters": {
                "method": "arima",
                "p": 1,
                "d": 0,
                "q": 1
            }
        }
        
        result = self.forecasting_agent.create_forecast(**cashflow_forecast_data)
        if result.get("success"):
            forecast_id = result["result"]["forecast_id"]
            logger.info(f"Created cash flow forecast (ID: {forecast_id})")
        else:
            logger.error(f"Failed to create cash flow forecast: {result.get('error')}")
    
    def _detect_anomalies(self):
        """Demonstrate anomaly detection in financial data."""
        logger.info("Running anomaly detection")
        
        # Detect transaction anomalies
        transaction_anomaly_data = {
            "detection_type": "transaction",
            "parameters": {
                "days": 30,
                "min_amount": 100,
                "threshold": 0.7
            }
        }
        
        result = self.accounting_agent.detect_anomalies(**transaction_anomaly_data)
        if result.get("success"):
            detection_id = result["result"]["detection_id"]
            anomalies_found = result["result"]["anomalies_found"]
            
            logger.info(f"Completed transaction anomaly detection (ID: {detection_id})")
            logger.info(f"Found {anomalies_found} potential anomalies")
            
            # Log anomalies
            if anomalies_found > 0:
                for i, anomaly in enumerate(result["result"]["anomalies"]):
                    logger.info(f"Anomaly {i+1}:")
                    logger.info(f"  Type: {anomaly.get('type')}")
                    logger.info(f"  Description: {anomaly.get('description')}")
                    logger.info(f"  Score: {anomaly.get('score')}")
        else:
            logger.error(f"Failed to detect anomalies: {result.get('error')}")


if __name__ == "__main__":
    # Run the complete finance workflow example
    example = FinanceWorkflowExample()
    example.run_complete_workflow()