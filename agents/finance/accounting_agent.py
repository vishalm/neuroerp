"accounts": account_data,
            "total": total_balance,
            "grouped": grouped_data if grouping else None
        }
    
    def _calculate_account_group_activity(self, accounts, start_date, end_date, grouping=None):
        """Calculate account activity for a group of accounts in a period."""
        total_activity = 0
        account_data = []
        
        for acct in accounts:
            # Would need to calculate activity from transactions
            # This is simplified - would need to query actual transactions
            balance = acct.properties.get("balance", 0)
            
            account_data.append({
                "account_id": acct.id,
                "number": acct.properties.get("number"),
                "name": acct.properties.get("name"),
                "type": acct.properties.get("type"),
                "subtype": acct.properties.get("subtype"),
                "balance": balance
            })
            total_activity += balance
        
        # Group if needed
        grouped_data = {}
        if grouping:
            for acct in account_data:
                for group_field in grouping:
                    if group_field in acct:
                        group_value = acct[group_field]
                        if group_value not in grouped_data:
                            grouped_data[group_value] = {
                                "accounts": [],
                                "total": 0
                            }
                        grouped_data[group_value]["accounts"].append(acct)
                        grouped_data[group_value]["total"] += acct["balance"]
        
        return {
            "accounts": account_data,
            "total": total_activity,
            "grouped": grouped_data if grouping else None
        }
    
    def detect_anomalies(self,
                        detection_type: str,
                        parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Detect anomalies in financial data.
        
        Args:
            detection_type: Type of anomaly detection
            parameters: Parameters for detection algorithm
            
        Returns:
            Detected anomalies
        """
        if not self.ai_engine:
            raise ValueError("AI engine is required for anomaly detection")
        
        if not parameters:
            parameters = {}
        
        # Choose detection method based on type
        if detection_type == "transaction":
            anomalies = self._detect_transaction_anomalies(parameters)
        elif detection_type == "account_balance":
            anomalies = self._detect_balance_anomalies(parameters)
        elif detection_type == "pattern":
            anomalies = self._detect_pattern_anomalies(parameters)
        else:
            raise ValueError(f"Unknown detection type: {detection_type}")
        
        # Create anomaly detection record
        detection_properties = {
            "detection_type": detection_type,
            "parameters": parameters,
            "anomalies_found": len(anomalies),
            "detected_at": datetime.now().isoformat()
        }
        
        # Create detection node
        detection_id = self.neural_fabric.create_node(
            node_type="anomaly_detection",
            properties=detection_properties
        )
        
        # Create nodes for each anomaly and connect to detection
        for anomaly in anomalies:
            anomaly_id = self.neural_fabric.create_node(
                node_type="anomaly",
                properties=anomaly
            )
            
            self.neural_fabric.connect_nodes(
                source_id=anomaly_id,
                target_id=detection_id,
                relation_type="detected_in"
            )
            
            # Connect anomaly to related transaction if applicable
            if "transaction_id" in anomaly:
                self.neural_fabric.connect_nodes(
                    source_id=anomaly_id,
                    target_id=anomaly["transaction_id"],
                    relation_type="flags"
                )
                
                # Flag the transaction
                self.neural_fabric.update_node(
                    node_id=anomaly["transaction_id"],
                    properties={"flagged": True, "anomaly_id": anomaly_id}
                )
                
                # Publish event
                self.event_bus.publish(
                    event_type="transaction.flagged",
                    payload={
                        "transaction_id": anomaly["transaction_id"],
                        "anomaly_id": anomaly_id,
                        "anomaly_type": anomaly.get("type"),
                        "score": anomaly.get("score")
                    }
                )
        
        logger.info(f"Detected {len(anomalies)} anomalies using {detection_type} detection")
        
        # Return detection results
        return {
            "detection_id": detection_id,
            "detection_type": detection_type,
            "anomalies_found": len(anomalies),
            "anomalies": anomalies
        }
    
    def _detect_transaction_anomalies(self, parameters):
        """Detect anomalies in transactions."""
        # Get recent transactions
        days = parameters.get("days", 30)
        min_amount = parameters.get("min_amount", 0)
        threshold = parameters.get("threshold", 0.9)
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        transactions = self.neural_fabric.query_nodes(
            node_type="transaction",
            limit=1000
        )
        
        # Filter transactions by date and amount
        filtered_transactions = []
        for tx in transactions:
            tx_date = tx.properties.get("date")
            tx_amount = tx.properties.get("amount", 0)
            
            if tx_date and tx_amount >= min_amount:
                try:
                    tx_date_obj = datetime.strptime(tx_date, "%Y-%m-%d").date()
                    if start_date <= tx_date_obj <= end_date:
                        filtered_transactions.append(tx)
                except ValueError:
                    continue
        
        # Use AI to analyze transactions for anomalies
        anomalies = []
        
        # Prepare transaction data for analysis
        tx_data = []
        for tx in filtered_transactions:
            tx_data.append({
                "id": tx.id,
                "date": tx.properties.get("date"),
                "amount": tx.properties.get("amount"),
                "description": tx.properties.get("description"),
                "type": tx.properties.get("transaction_type"),
                "reference": tx.properties.get("reference")
            })
        
        # Use AI to detect anomalies
        prompt = f"""
Analyze the following transactions for potential anomalies.
Look for unusual amounts, patterns, descriptions, or anything that stands out as irregular.
Consider the following as potential anomaly indicators:
- Unusually large transactions
- Round number amounts that might indicate estimates
- Duplicate or very similar transactions
- Unusual transaction descriptions
- Transactions on weekends or holidays
- Transactions with patterns in references or amounts

Transactions:
{json.dumps(tx_data, indent=2)}

Return a JSON array of anomalies found, with each anomaly having:
- transaction_id: ID of the anomalous transaction
- type: Type of anomaly (e.g., "unusual_amount", "duplicate", "suspicious_description")
- description: Description of the anomaly
- score: Confidence score (0.0 to 1.0)
"""
        
        analysis_result = self.ai_engine.get_agent_response(
            agent_type="finance",
            prompt=prompt,
            context={"task": "anomaly_detection"}
        )
        
        # Parse AI response
        try:
            # Extract JSON part from possibly larger text
            json_match = re.search(r'(\[[\s\S]*\])', analysis_result)
            if json_match:
                anomalies = json.loads(json_match.group(1))
            else:
                # Fallback: try to parse the entire text as JSON
                anomalies = json.loads(analysis_result)
                
            # Filter by threshold
            anomalies = [a for a in anomalies if a.get("score", 0) >= threshold]
                
        except json.JSONDecodeError:
            logger.error("Failed to parse AI anomaly detection results")
            anomalies = []
        
        return anomalies
    
    def _detect_balance_anomalies(self, parameters):
        """Detect anomalies in account balances."""
        # Get accounts
        accounts = self.neural_fabric.query_nodes(
            node_type="account",
            limit=1000
        )
        
        # Filter accounts based on parameters
        account_types = parameters.get("account_types", [])
        if account_types:
            accounts = [a for a in accounts if a.properties.get("type") in account_types]
        
        # Prepare account data for analysis
        account_data = []
        for acct in accounts:
            account_data.append({
                "id": acct.id,
                "number": acct.properties.get("number"),
                "name": acct.properties.get("name"),
                "type": acct.properties.get("type"),
                "balance": acct.properties.get("balance", 0)
            })
        
        # Use AI to detect balance anomalies
        prompt = f"""
Analyze the following account balances for potential anomalies.
Look for unusually high or low balances, unexpected negative balances, or other irregular patterns.

Accounts:
{json.dumps(account_data, indent=2)}

Return a JSON array of anomalies found, with each anomaly having:
- account_id: ID of the account with anomalous balance
- type: Type of anomaly (e.g., "high_balance", "negative_balance", "zero_balance")
- description: Description of the anomaly
- score: Confidence score (0.0 to 1.0)
"""
        
        analysis_result = self.ai_engine.get_agent_response(
            agent_type="finance",
            prompt=prompt,
            context={"task": "balance_anomaly_detection"}
        )
        
        # Parse AI response
        threshold = parameters.get("threshold", 0.9)
        anomalies = []
        
        try:
            # Extract JSON part from possibly larger text
            json_match = re.search(r'(\[[\s\S]*\])', analysis_result)
            if json_match:
                anomalies = json.loads(json_match.group(1))
            else:
                # Fallback: try to parse the entire text as JSON
                anomalies = json.loads(analysis_result)
                
            # Filter by threshold
            anomalies = [a for a in anomalies if a.get("score", 0) >= threshold]
                
        except json.JSONDecodeError:
            logger.error("Failed to parse AI anomaly detection results")
        
        return anomalies
    
    def _detect_pattern_anomalies(self, parameters):
        """Detect pattern-based anomalies in financial data."""
        # Pattern anomaly detection would look at time series data and trends
        # This is a more complex analysis that would involve statistical methods
        # Simplified implementation for now
        return []
    
    def manage_account(self,
                      action: str,
                      account_data: Dict[str, Any],
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage account in the chart of accounts.
        
        Args:
            action: Action to perform (create, update, deactivate)
            account_data: Account data
            metadata: Additional metadata
            
        Returns:
            Account operation result
        """
        if action == "create":
            # Validate required fields
            required_fields = ["number", "name", "type"]
            for field in required_fields:
                if field not in account_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check if account number already exists
            existing_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"number": account_data["number"]}
            )
            
            if existing_accounts:
                raise ValueError(f"Account number already exists: {account_data['number']}")
            
            # Create account properties
            account_properties = {
                "number": account_data["number"],
                "name": account_data["name"],
                "type": account_data["type"],
                "full_name": f"{account_data['number']} - {account_data['name']}",
                "active": True,
                "balance": 0.0,
                "created_at": datetime.now().isoformat()
            }
            
            # Add optional properties
            optional_fields = ["subtype", "description", "is_bank_account", "is_contra", "parent_account_id"]
            for field in optional_fields:
                if field in account_data:
                    account_properties[field] = account_data[field]
            
            # Add metadata if provided
            if metadata:
                account_properties["metadata"] = metadata
            
            # Create account node
            account_id = self.neural_fabric.create_node(
                node_type="account",
                properties=account_properties
            )
            
            # If parent account specified, create relationship
            if "parent_account_id" in account_data:
                parent_id = account_data["parent_account_id"]
                parent_node = self.neural_fabric.get_node(parent_id)
                
                if parent_node and parent_node.node_type == "account":
                    self.neural_fabric.connect_nodes(
                        source_id=account_id,
                        target_id=parent_id,
                        relation_type="child_of"
                    )
            
            # Publish event
            self.event_bus.publish(
                event_type="account.created",
                payload={
                    "account_id": account_id,
                    "number": account_data["number"],
                    "name": account_data["name"],
                    "type": account_data["type"]
                }
            )
            
            logger.info(f"Created account: {account_properties['full_name']} (ID: {account_id})")
            
            return {
                "action": "create",
                "account_id": account_id,
                "number": account_data["number"],
                "name": account_data["name"],
                "type": account_data["type"]
            }
            
        elif action == "update":
            # Validate account ID
            if "account_id" not in account_data:
                raise ValueError("Missing account_id for update")
                
            account_id = account_data["account_id"]
            account = self.neural_fabric.get_node(account_id)
            
            if not account or account.node_type != "account":
                raise ValueError(f"Invalid account ID: {account_id}")
            
            # Prepare update properties
            update_properties = {}
            updatable_fields = ["name", "description", "is_bank_account", "is_contra", "parent_account_id"]
            
            for field in updatable_fields:
                if field in account_data:
                    update_properties[field] = account_data[field]
            
            # Update full name if name changed
            if "name" in update_properties:
                update_properties["full_name"] = f"{account.properties.get('number')} - {update_properties['name']}"
            
            # Add metadata if provided
            if metadata:
                update_properties["metadata"] = metadata
                
            # Update last modified
            update_properties["last_modified"] = datetime.now().isoformat()
            
            # Update account node
            self.neural_fabric.update_node(
                node_id=account_id,
                properties=update_properties
            )
            
            # If parent account changed, update relationship
            if "parent_account_id" in account_data:
                new_parent_id = account_data["parent_account_id"]
                
                # Remove existing parent relationships
                parent_connections = self.neural_fabric.get_connected_nodes(
                    node_id=account_id,
                    relation_type="child_of"
                )
                
                if "child_of" in parent_connections:
                    for parent in parent_connections["child_of"]:
                        self.neural_fabric.disconnect_nodes(
                            source_id=account_id,
                            target_id=parent.id,
                            relation_type="child_of"
                        )
                
                # Add new parent relationship
                if new_parent_id:
                    parent_node = self.neural_fabric.get_node(new_parent_id)
                    
                    if parent_node and parent_node.node_type == "account":
                        self.neural_fabric.connect_nodes(
                            source_id=account_id,
                            target_id=new_parent_id,
                            relation_type="child_of"
                        )
            
            # Publish event
            self.event_bus.publish(
                event_type="account.updated",
                payload={
                    "account_id": account_id,
                    "updates": update_properties
                }
            )
            
            logger.info(f"Updated account ID {account_id}: {update_properties}")
            
            return {
                "action": "update",
                "account_id": account_id,
                "updates": update_properties
            }
            
        elif action == "deactivate":
            # Validate account ID
            if "account_id" not in account_data:
                raise ValueError("Missing account_id for deactivate")
                
            account_id = account_data["account_id"]
            account = self.neural_fabric.get_node(account_id)
            
            if not account or account.node_type != "account":
                raise ValueError(f"Invalid account ID: {account_id}")
            
            # Check if account has balance
            balance = account.properties.get("balance", 0)
            if abs(balance) > 0.01:
                raise ValueError(f"Cannot deactivate account with non-zero balance: {balance}")
            
            # Deactivate account
            self.neural_fabric.update_node(
                node_id=account_id,
                properties={
                    "active": False,
                    "deactivated_at": datetime.now().isoformat(),
                    "deactivation_reason": account_data.get("reason", "Not specified")
                }
            )
            
            # Publish event
            self.event_bus.publish(
                event_type="account.deactivated",
                payload={
                    "account_id": account_id,
                    "reason": account_data.get("reason")
                }
            )
            
            logger.info(f"Deactivated account ID {account_id}")
            
            return {
                "action": "deactivate",
                "account_id": account_id,
                "status": "deactivated"
            }
        else:
            raise ValueError(f"Unknown account action: {action}")
    
    def process_expense(self,
                       expense_data: Dict[str, Any],
                       receipt_image: Optional[str] = None) -> Dict[str, Any]:
        """Process an expense.
        
        Args:
            expense_data: Expense data
            receipt_image: Optional receipt image data
            
        Returns:
            Expense processing result
        """
        # Validate required fields
        required_fields = ["date", "amount", "description", "expense_account_id", "payment_account_id"]
        for field in required_fields:
            if field not in expense_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate date
        try:
            expense_date = datetime.strptime(expense_data["date"], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {expense_data['date']}. Expected YYYY-MM-DD")
        
        # Validate accounts
        expense_account = self.neural_fabric.get_node(expense_data["expense_account_id"])
        if not expense_account or expense_account.node_type != "account":
            raise ValueError(f"Invalid expense account ID: {expense_data['expense_account_id']}")
            
        payment_account = self.neural_fabric.get_node(expense_data["payment_account_id"])
        if not payment_account or payment_account.node_type != "account":
            raise ValueError(f"Invalid payment account ID: {expense_data['payment_account_id']}")
        
        # Create expense properties
        expense_number = f"EXP-{datetime.now().strftime('%Y%m%d')}-{str(int(time.time()))[-4:]}"
        
        expense_properties = {
            "expense_number": expense_number,
            "date": expense_data["date"],
            "amount": expense_data["amount"],
            "description": expense_data["description"],
            "expense_account_id": expense_data["expense_account_id"],
            "expense_account_name": expense_account.properties.get("name"),
            "payment_account_id": expense_data["payment_account_id"],
            "payment_account_name": payment_account.properties.get("name"),
            "status": "processed",
            "created_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        optional_fields = ["vendor_id", "vendor_name", "expense_type", "tax_amount", "reference", "notes"]
        for field in optional_fields:
            if field in expense_data:
                expense_properties[field] = expense_data[field]
        
        # If vendor ID is provided but not name, try to get name
        if "vendor_id" in expense_properties and "vendor_name" not in expense_properties:
            vendor_node = self.neural_fabric.get_node(expense_data["vendor_id"])
            if vendor_node and vendor_node.node_type == "vendor":
                expense_properties["vendor_name"] = vendor_node.properties.get("name")
        
        # Calculate tax if not provided but rate is
        if "tax_amount" not in expense_properties and "tax_rate" in expense_data:
            tax_rate = expense_data["tax_rate"]
            tax_amount = expense_data["amount"] * (tax_rate / 100)
            expense_properties["tax_amount"] = tax_amount
            expense_properties["tax_rate"] = tax_rate
        
        # Process receipt if provided
        if receipt_image and self.ai_engine:
            # AI-based receipt processing would go here
            # This would extract data from the receipt image
            expense_properties["has_receipt"] = True
        
        # Create expense node
        expense_id = self.neural_fabric.create_node(
            node_type="expense",
            properties=expense_properties
        )
        
        # Connect to vendor if provided
        if "vendor_id" in expense_properties:
            self.neural_fabric.connect_nodes(
                source_id=expense_id,
                target_id=expense_properties["vendor_id"],
                relation_type="paid_to"
            )
        
        # Record the transaction
        entries = [
            {
                "account_id": expense_data["expense_account_id"],
                "type": "debit",
                "amount": expense_data["amount"]
            },
            {
                "account_id": expense_data["payment_account_id"],
                "type": "credit",
                "amount": expense_data["amount"]
            }
        ]
        
        # Add tax entry if applicable
        if "tax_amount" in expense_properties and expense_properties["tax_amount"] > 0:
            # Find tax expense account
            tax_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"name": "Sales Tax Payable"}
            )
            
            if tax_accounts:
                tax_account = tax_accounts[0]
                entries.append({
                    "account_id": tax_account.id,
                    "type": "debit",
                    "amount": expense_properties["tax_amount"]
                })
                
                # Adjust payment account entry
                entries[1]["amount"] += expense_properties["tax_amount"]
        
        # Record the transaction
        tx_result = self.record_transaction(
            transaction_type="expense",
            date=expense_data["date"],
            amount=expense_data["amount"],
            description=expense_data["description"],
            entries=entries,
            reference=expense_number,
            metadata={"expense_id": expense_id}
        )
        
        # Link transaction to expense
        if tx_result and "transaction_id" in tx_result:
            self.neural_fabric.update_node(
                node_id=expense_id,
                properties={"transaction_id": tx_result["transaction_id"]}
            )
            
            self.neural_fabric.connect_nodes(
                source_id=expense_id,
                target_id=tx_result["transaction_id"],
                relation_type="generated"
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="expense.processed",
            payload={
                "expense_id": expense_id,
                "expense_number": expense_number,
                "amount": expense_data["amount"],
                "date": expense_data["date"]
            }
        )
        
        logger.info(f"Processed expense {expense_number} for {expense_data['amount']}")
        
        # Return expense details
        return {
            "expense_id": expense_id,
            "expense_number": expense_number,
            "amount": expense_data["amount"],
            "date": expense_data["date"],
            "status": "processed"
        }
    
    def close_period(self,
                    period_id: str,
                    closing_entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Close a fiscal period.
        
        Args:
            period_id: ID of the fiscal period to close
            closing_entries: Optional list of closing entries to record
            
        Returns:
            Period closing result
        """
        # Validate period
        period = self.neural_fabric.get_node(period_id)
        if not period or period.node_type != "fiscal_period":
            raise ValueError(f"Invalid fiscal period ID: {period_id}")
        
        # Check if period is already closed
        if period.properties.get("status") == "closed":
            raise ValueError(f"Period is already closed: {period.properties.get('name')}")
        
        # Get end date of period
        end_date = period.properties.get("end_date")
        if not end_date:
            raise ValueError("Period end date not found")
        
        # Record closing entries if provided
        recorded_entries = []
        if closing_entries:
            for entry in closing_entries:
                tx_result = self.record_transaction(
                    transaction_type="closing",
                    date=end_date,
                    amount=entry.get("amount", 0),
                    description=entry.get("description", "Period closing entry"),
                    entries=entry.get("entries", []),
                    reference=f"CLOSE-{period.properties.get('name')}",
                    metadata={"period_id": period_id, "closing_entry": True}
                )
                
                if tx_result and "transaction_id" in tx_result:
                    recorded_entries.append(tx_result["transaction_id"])
        
        # Close the period
        self.neural_fabric.update_node(
            node_id=period_id,
            properties={
                "status": "closed",
                "closed_at": datetime.now().isoformat(),
                "closing_entries": recorded_entries
            }
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="period.closed",
            payload={
                "period_id": period_id,
                "period_name": period.properties.get("name"),
                "end_date": end_date,
                "closing_entries": len(recorded_entries)
            }
        )
        
        logger.info(f"Closed fiscal period: {period.properties.get('name')}")
        
        # Return period closing details
        return {
            "period_id": period_id,
            "period_name": period.properties.get("name"),
            "end_date": end_date,
            "closing_entries": len(recorded_entries),
            "status": "closed"
        }
    
    def forecast_cashflow(self,
                         start_date: str,
                         end_date: str,
                         parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Forecast cash flow for a future period.
        
        Args:
            start_date: Start date for forecast
            end_date: End date for forecast
            parameters: Optional parameters for forecasting
            
        Returns:
            Cash flow forecast
        """
        if not self.ai_engine:
            raise ValueError("AI engine is required for cash flow forecasting")
        
        # Validate dates
        try:
            forecast_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            forecast_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
        
        if forecast_start >= forecast_end:
            raise ValueError("End date must be after start date")
        
        # Get historical cash flow data
        historical_days = parameters.get("historical_days", 90)
        historical_start = forecast_start - timedelta(days=historical_days)
        historical_end = forecast_start - timedelta(days=1)
        
        # Get cash accounts
        cash_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"is_bank_account": True}
        )
        
        if not cash_accounts:
            cash_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"name": "Cash"}
            )
            
        if not cash_accounts:
            raise ValueError("No cash accounts found")
        
        # Get historical transactions for cash accounts
        historical_data = []
        for account in cash_accounts:
            transactions = self.neural_fabric.query_nodes(
                node_type="transaction",
                limit=1000
            )
            
            for tx in transactions:
                tx_date = tx.properties.get("date")
                if tx_date:
                    try:
                        tx_date_obj = datetime.strptime(tx_date, "%Y-%m-%d").date()
                        if historical_start <= tx_date_obj <= historical_end:
                            # Get entries for this transaction that affect this cash account
                            entries = self.neural_fabric.get_connected_nodes(
                                node_id=tx.id,
                                relation_type="part_of_inverse"
                            )
                            
                            if "part_of_inverse" in entries:
                                for entry in entries["part_of_inverse"]:
                                    if entry.properties.get("account_id") == account.id:
                                        historical_data.append({
                                            "date": tx_date,
                                            "amount": entry.properties.get("amount", 0),
                                            "type": entry.properties.get("type"),
                                            "transaction_type": tx.properties.get("transaction_type"),
                                            "description": tx.properties.get("description")
                                        })
                    except ValueError:
                        continue
        
        # Get pending receivables
        pending_receivables = []
        invoices = self.neural_fabric.query_nodes(
            node_type="invoice",
            filters={"status": ["open", "partial"]},
            limit=1000
        )
        
        for inv in invoices:
            due_date = inv.properties.get("due_date")
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                    if forecast_start <= due_date_obj <= forecast_end:"""
Accounting Agent for NeuroERP.

This agent manages financial transactions, general ledger, accounts payable/receivable,
financial reporting, and automated bookkeeping processes.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime, date, timedelta
import re

from ...core.config import Config
from ...core.event_bus import EventBus
from ...core.neural_fabric import NeuralFabric
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AccountingAgent(BaseAgent):
    """AI Agent for accounting and financial processes."""
    
    def __init__(self, name: str = "Accounting Agent", ai_engine=None, vector_store=None):
        """Initialize the accounting agent.
        
        Args:
            name: Name of the agent
            ai_engine: AI engine for advanced processing
            vector_store: Vector store for semantic search
        """
        super().__init__(name=name, agent_type="finance.accounting", ai_engine=ai_engine, vector_store=vector_store)
        
        self.config = Config()
        self.event_bus = EventBus()
        self.neural_fabric = NeuralFabric()
        
        # Register agent skills
        self._register_skills()
        
        # Subscribe to relevant events
        self._subscribe_to_events()
        
        # Load chart of accounts and other configurations
        self._load_configurations()
        
        logger.info(f"Initialized {name}")
    
    def _register_skills(self):
        """Register agent-specific skills."""
        self.register_skill("record_transaction", self.record_transaction)
        self.register_skill("create_invoice", self.create_invoice)
        self.register_skill("process_payment", self.process_payment)
        self.register_skill("reconcile_accounts", self.reconcile_accounts)
        self.register_skill("generate_financial_report", self.generate_financial_report)
        self.register_skill("detect_anomalies", self.detect_anomalies)
        self.register_skill("manage_account", self.manage_account)
        self.register_skill("process_expense", self.process_expense)
        self.register_skill("close_period", self.close_period)
        self.register_skill("forecast_cashflow", self.forecast_cashflow)
    
    def _subscribe_to_events(self):
        """Subscribe to relevant system events."""
        self.event_bus.subscribe("invoice.created", self._handle_invoice)
        self.event_bus.subscribe("payment.received", self._handle_payment)
        self.event_bus.subscribe("expense.submitted", self._handle_expense)
        self.event_bus.subscribe("account.created", self._handle_account)
        self.event_bus.subscribe("transaction.flagged", self._handle_flagged_transaction)
        self.event_bus.subscribe("period.closed", self._handle_period_close)
    
    def _load_configurations(self):
        """Load accounting configurations."""
        # Load chart of accounts
        account_nodes = self.neural_fabric.query_nodes(
            node_type="account",
            limit=1000
        )
        
        if not account_nodes:
            logger.warning("No accounts found. Creating default chart of accounts.")
            self._create_default_chart_of_accounts()
        else:
            logger.info(f"Loaded {len(account_nodes)} accounts")
        
        # Load fiscal periods
        fiscal_period_nodes = self.neural_fabric.query_nodes(
            node_type="fiscal_period",
            limit=100
        )
        
        if not fiscal_period_nodes:
            logger.warning("No fiscal periods found. Creating current period.")
            self._create_current_fiscal_period()
        else:
            logger.info(f"Loaded {len(fiscal_period_nodes)} fiscal periods")
    
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
            if action == "record_transaction":
                return {"success": True, "result": self.record_transaction(**parameters)}
            elif action == "create_invoice":
                return {"success": True, "result": self.create_invoice(**parameters)}
            elif action == "process_payment":
                return {"success": True, "result": self.process_payment(**parameters)}
            elif action == "reconcile_accounts":
                return {"success": True, "result": self.reconcile_accounts(**parameters)}
            elif action == "generate_financial_report":
                return {"success": True, "result": self.generate_financial_report(**parameters)}
            elif action == "detect_anomalies":
                return {"success": True, "result": self.detect_anomalies(**parameters)}
            elif action == "manage_account":
                return {"success": True, "result": self.manage_account(**parameters)}
            elif action == "process_expense":
                return {"success": True, "result": self.process_expense(**parameters)}
            elif action == "close_period":
                return {"success": True, "result": self.close_period(**parameters)}
            elif action == "forecast_cashflow":
                return {"success": True, "result": self.forecast_cashflow(**parameters)}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [skill["name"] for skill in self.skills]
                }
        except Exception as e:
            logger.error(f"Error processing {action}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _create_default_chart_of_accounts(self):
        """Create a default chart of accounts."""
        default_accounts = [
            # Asset accounts (1000-1999)
            {"number": "1000", "name": "Cash", "type": "asset", "subtype": "current", "is_bank_account": True},
            {"number": "1010", "name": "Accounts Receivable", "type": "asset", "subtype": "current"},
            {"number": "1020", "name": "Inventory", "type": "asset", "subtype": "current"},
            {"number": "1100", "name": "Prepaid Expenses", "type": "asset", "subtype": "current"},
            {"number": "1500", "name": "Fixed Assets", "type": "asset", "subtype": "fixed"},
            {"number": "1510", "name": "Accumulated Depreciation", "type": "asset", "subtype": "fixed", "is_contra": True},
            
            # Liability accounts (2000-2999)
            {"number": "2000", "name": "Accounts Payable", "type": "liability", "subtype": "current"},
            {"number": "2010", "name": "Accrued Expenses", "type": "liability", "subtype": "current"},
            {"number": "2100", "name": "Payroll Liabilities", "type": "liability", "subtype": "current"},
            {"number": "2200", "name": "Sales Tax Payable", "type": "liability", "subtype": "current"},
            {"number": "2500", "name": "Long-term Debt", "type": "liability", "subtype": "long-term"},
            
            # Equity accounts (3000-3999)
            {"number": "3000", "name": "Common Stock", "type": "equity"},
            {"number": "3100", "name": "Retained Earnings", "type": "equity"},
            {"number": "3200", "name": "Owner's Equity", "type": "equity"},
            {"number": "3900", "name": "Current Year Earnings", "type": "equity"},
            
            # Revenue accounts (4000-4999)
            {"number": "4000", "name": "Sales Revenue", "type": "revenue"},
            {"number": "4100", "name": "Service Revenue", "type": "revenue"},
            {"number": "4200", "name": "Interest Income", "type": "revenue"},
            {"number": "4900", "name": "Other Income", "type": "revenue"},
            
            # Expense accounts (5000-8999)
            {"number": "5000", "name": "Cost of Goods Sold", "type": "expense", "subtype": "cogs"},
            {"number": "6000", "name": "Salaries and Wages", "type": "expense", "subtype": "operating"},
            {"number": "6100", "name": "Rent Expense", "type": "expense", "subtype": "operating"},
            {"number": "6200", "name": "Utilities Expense", "type": "expense", "subtype": "operating"},
            {"number": "6300", "name": "Office Supplies", "type": "expense", "subtype": "operating"},
            {"number": "6400", "name": "Insurance Expense", "type": "expense", "subtype": "operating"},
            {"number": "7000", "name": "Depreciation Expense", "type": "expense", "subtype": "operating"},
            {"number": "8000", "name": "Interest Expense", "type": "expense", "subtype": "financial"},
            {"number": "8100", "name": "Tax Expense", "type": "expense", "subtype": "financial"},
        ]
        
        # Create account nodes in neural fabric
        for account_data in default_accounts:
            account_props = {
                "number": account_data["number"],
                "name": account_data["name"],
                "type": account_data["type"],
                "full_name": f"{account_data['number']} - {account_data['name']}",
                "active": True,
                "balance": 0.0,
                "created_at": datetime.now().isoformat()
            }
            
            # Add optional properties
            for key in ["subtype", "is_bank_account", "is_contra"]:
                if key in account_data:
                    account_props[key] = account_data[key]
            
            account_id = self.neural_fabric.create_node(
                node_type="account",
                properties=account_props
            )
            
            logger.debug(f"Created account: {account_props['full_name']} (ID: {account_id})")
        
        logger.info(f"Created default chart of accounts with {len(default_accounts)} accounts")
    
    def _create_current_fiscal_period(self):
        """Create the current fiscal period."""
        today = date.today()
        
        # Create monthly period
        period_properties = {
            "name": f"{today.strftime('%B')} {today.year}",
            "start_date": date(today.year, today.month, 1).isoformat(),
            "end_date": (date(today.year, today.month + 1, 1) - timedelta(days=1)).isoformat() if today.month < 12 else date(today.year, 12, 31).isoformat(),
            "type": "month",
            "status": "open",
            "created_at": datetime.now().isoformat()
        }
        
        period_id = self.neural_fabric.create_node(
            node_type="fiscal_period",
            properties=period_properties
        )
        
        logger.info(f"Created fiscal period: {period_properties['name']} (ID: {period_id})")
        
        # Create quarter period if this is the first month of a quarter
        if today.month in [1, 4, 7, 10]:
            quarter = (today.month - 1) // 3 + 1
            quarter_start = date(today.year, (quarter - 1) * 3 + 1, 1)
            quarter_end = date(today.year, quarter * 3, 1) + timedelta(days=31)
            quarter_end = date(quarter_end.year, quarter_end.month, 1) - timedelta(days=1)
            
            quarter_properties = {
                "name": f"Q{quarter} {today.year}",
                "start_date": quarter_start.isoformat(),
                "end_date": quarter_end.isoformat(),
                "type": "quarter",
                "status": "open",
                "created_at": datetime.now().isoformat()
            }
            
            quarter_id = self.neural_fabric.create_node(
                node_type="fiscal_period",
                properties=quarter_properties
            )
            
            logger.info(f"Created fiscal period: {quarter_properties['name']} (ID: {quarter_id})")
        
        # Create year period if this is January
        if today.month == 1:
            year_properties = {
                "name": f"FY {today.year}",
                "start_date": date(today.year, 1, 1).isoformat(),
                "end_date": date(today.year, 12, 31).isoformat(),
                "type": "year",
                "status": "open",
                "created_at": datetime.now().isoformat()
            }
            
            year_id = self.neural_fabric.create_node(
                node_type="fiscal_period",
                properties=year_properties
            )
            
            logger.info(f"Created fiscal period: {year_properties['name']} (ID: {year_id})")
    
    def record_transaction(self,
                          transaction_type: str,
                          date: str,
                          amount: float,
                          description: str,
                          entries: List[Dict[str, Any]],
                          reference: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Record a financial transaction.
        
        Args:
            transaction_type: Type of transaction (journal, payment, invoice, etc.)
            date: Transaction date (YYYY-MM-DD)
            amount: Total transaction amount
            description: Transaction description
            entries: List of transaction entries (debits and credits)
            reference: Optional reference number
            metadata: Additional transaction metadata
            
        Returns:
            Transaction details
        """
        # Validate transaction date
        try:
            transaction_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
        
        # Validate entries
        if not entries:
            raise ValueError("No entries provided for transaction")
        
        # Ensure total debits equal total credits
        total_debits = sum(entry["amount"] for entry in entries if entry["type"] == "debit")
        total_credits = sum(entry["amount"] for entry in entries if entry["type"] == "credit")
        
        if not abs(total_debits - total_credits) < 0.01:  # Allow for small floating point differences
            raise ValueError(f"Debits ({total_debits}) must equal credits ({total_credits})")
        
        # Get current fiscal period
        fiscal_period = self._get_current_fiscal_period()
        if not fiscal_period:
            raise ValueError("No open fiscal period found for transaction date")
        
        # Create transaction ID or reference number if not provided
        if not reference:
            reference = f"TX-{int(time.time())}"
        
        # Create transaction properties
        transaction_properties = {
            "transaction_type": transaction_type,
            "date": date,
            "amount": amount,
            "description": description,
            "reference": reference,
            "status": "posted",
            "fiscal_period_id": fiscal_period.id,
            "fiscal_period_name": fiscal_period.properties.get("name"),
            "created_at": datetime.now().isoformat()
        }
        
        # Add metadata if provided
        if metadata:
            transaction_properties["metadata"] = metadata
        
        # Create transaction node
        transaction_id = self.neural_fabric.create_node(
            node_type="transaction",
            properties=transaction_properties
        )
        
        # Process each entry
        entry_ids = []
        for entry_data in entries:
            # Validate account
            account_number = entry_data.get("account_number")
            account_id = entry_data.get("account_id")
            
            if not account_id and not account_number:
                raise ValueError("Either account_id or account_number must be provided")
            
            # Find account by number if ID not provided
            if not account_id and account_number:
                account_nodes = self.neural_fabric.query_nodes(
                    node_type="account",
                    filters={"number": account_number}
                )
                
                if not account_nodes:
                    raise ValueError(f"Account not found with number: {account_number}")
                
                account_id = account_nodes[0].id
            
            # Get account details
            account = self.neural_fabric.get_node(account_id)
            if not account or account.node_type != "account":
                raise ValueError(f"Invalid account ID: {account_id}")
            
            # Create entry properties
            entry_properties = {
                "transaction_id": transaction_id,
                "account_id": account_id,
                "account_number": account.properties.get("number"),
                "account_name": account.properties.get("name"),
                "type": entry_data["type"],  # debit or credit
                "amount": entry_data["amount"],
                "description": entry_data.get("description", description),
                "date": date
            }
            
            # Create entry node
            entry_id = self.neural_fabric.create_node(
                node_type="transaction_entry",
                properties=entry_properties
            )
            
            # Connect entry to transaction
            self.neural_fabric.connect_nodes(
                source_id=entry_id,
                target_id=transaction_id,
                relation_type="part_of"
            )
            
            # Connect entry to account
            self.neural_fabric.connect_nodes(
                source_id=entry_id,
                target_id=account_id,
                relation_type="affects"
            )
            
            # Update account balance
            current_balance = account.properties.get("balance", 0.0)
            
            # Determine if the entry increases or decreases the account balance
            # based on the account type and entry type
            account_type = account.properties.get("type")
            is_debit_increase = account_type in ["asset", "expense"]
            
            if (entry_data["type"] == "debit" and is_debit_increase) or (entry_data["type"] == "credit" and not is_debit_increase):
                new_balance = current_balance + entry_data["amount"]
            else:
                new_balance = current_balance - entry_data["amount"]
            
            # Update account
            self.neural_fabric.update_node(
                node_id=account_id,
                properties={"balance": new_balance}
            )
            
            entry_ids.append(entry_id)
        
        # Connect transaction to fiscal period
        self.neural_fabric.connect_nodes(
            source_id=transaction_id,
            target_id=fiscal_period.id,
            relation_type="belongs_to"
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="transaction.recorded",
            payload={
                "transaction_id": transaction_id,
                "transaction_type": transaction_type,
                "amount": amount,
                "date": date,
                "reference": reference
            }
        )
        
        logger.info(f"Recorded {transaction_type} transaction: {reference} for {amount}")
        
        # Return transaction details
        return {
            "transaction_id": transaction_id,
            "reference": reference,
            "amount": amount,
            "date": date,
            "entries": len(entry_ids),
            "status": "posted"
        }
    
    def create_invoice(self,
                      customer_id: str,
                      date: str,
                      due_date: str,
                      items: List[Dict[str, Any]],
                      description: Optional[str] = None,
                      terms: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a customer invoice.
        
        Args:
            customer_id: ID of the customer
            date: Invoice date (YYYY-MM-DD)
            due_date: Due date (YYYY-MM-DD)
            items: List of invoice items
            description: Optional invoice description
            terms: Optional payment terms
            metadata: Additional invoice metadata
            
        Returns:
            Invoice details
        """
        # Validate dates
        try:
            invoice_date = datetime.strptime(date, "%Y-%m-%d").date()
            invoice_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD")
        
        # Validate customer
        customer_node = self.neural_fabric.get_node(customer_id)
        if not customer_node or customer_node.node_type != "customer":
            raise ValueError(f"Invalid customer ID: {customer_id}")
        
        # Validate items
        if not items:
            raise ValueError("No items provided for invoice")
        
        # Calculate totals
        subtotal = sum(item["quantity"] * item["price"] for item in items)
        tax_total = sum(item.get("tax_amount", 0) for item in items)
        total = subtotal + tax_total
        
        # Generate invoice number
        today = datetime.now()
        invoice_number = f"INV-{today.strftime('%Y%m%d')}-{str(int(time.time()))[-4:]}"
        
        # Create invoice properties
        invoice_properties = {
            "invoice_number": invoice_number,
            "customer_id": customer_id,
            "customer_name": customer_node.properties.get("name"),
            "date": date,
            "due_date": due_date,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "total": total,
            "status": "open",
            "created_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        if description:
            invoice_properties["description"] = description
            
        if terms:
            invoice_properties["terms"] = terms
            
        if metadata:
            invoice_properties["metadata"] = metadata
        
        # Create invoice node
        invoice_id = self.neural_fabric.create_node(
            node_type="invoice",
            properties=invoice_properties
        )
        
        # Create invoice items
        item_ids = []
        for item_data in items:
            item_properties = {
                "invoice_id": invoice_id,
                "description": item_data.get("description", ""),
                "quantity": item_data["quantity"],
                "price": item_data["price"],
                "amount": item_data["quantity"] * item_data["price"]
            }
            
            # Add tax if present
            if "tax_amount" in item_data:
                item_properties["tax_amount"] = item_data["tax_amount"]
                item_properties["total_amount"] = item_properties["amount"] + item_data["tax_amount"]
            else:
                item_properties["total_amount"] = item_properties["amount"]
            
            # Product reference if provided
            if "product_id" in item_data:
                item_properties["product_id"] = item_data["product_id"]
                
                # Get product details if available
                product_node = self.neural_fabric.get_node(item_data["product_id"])
                if product_node and product_node.node_type == "product":
                    item_properties["product_name"] = product_node.properties.get("name")
                    item_properties["product_code"] = product_node.properties.get("code")
            
            # Create item node
            item_id = self.neural_fabric.create_node(
                node_type="invoice_item",
                properties=item_properties
            )
            
            # Connect item to invoice
            self.neural_fabric.connect_nodes(
                source_id=item_id,
                target_id=invoice_id,
                relation_type="part_of"
            )
            
            item_ids.append(item_id)
        
        # Connect invoice to customer
        self.neural_fabric.connect_nodes(
            source_id=invoice_id,
            target_id=customer_id,
            relation_type="billed_to"
        )
        
        # Record the accounting transaction
        ar_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"name": "Accounts Receivable"}
        )
        
        revenue_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"name": "Sales Revenue"}
        )
        
        tax_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"name": "Sales Tax Payable"}
        )
        
        if ar_accounts and revenue_accounts:
            ar_account = ar_accounts[0]
            revenue_account = revenue_accounts[0]
            
            entries = [
                {
                    "account_id": ar_account.id,
                    "type": "debit",
                    "amount": total
                },
                {
                    "account_id": revenue_account.id,
                    "type": "credit",
                    "amount": subtotal
                }
            ]
            
            # Add tax entry if applicable
            if tax_total > 0 and tax_accounts:
                tax_account = tax_accounts[0]
                entries.append({
                    "account_id": tax_account.id,
                    "type": "credit",
                    "amount": tax_total
                })
            
            # Record the transaction
            tx_result = self.record_transaction(
                transaction_type="invoice",
                date=date,
                amount=total,
                description=f"Invoice {invoice_number} for {customer_node.properties.get('name')}",
                entries=entries,
                reference=invoice_number,
                metadata={"invoice_id": invoice_id}
            )
            
            # Link transaction to invoice
            if tx_result and "transaction_id" in tx_result:
                self.neural_fabric.update_node(
                    node_id=invoice_id,
                    properties={"transaction_id": tx_result["transaction_id"]}
                )
                
                self.neural_fabric.connect_nodes(
                    source_id=invoice_id,
                    target_id=tx_result["transaction_id"],
                    relation_type="generated"
                )
        
        # Publish event
        self.event_bus.publish(
            event_type="invoice.created",
            payload={
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "customer_id": customer_id,
                "total": total,
                "due_date": due_date
            }
        )
        
        logger.info(f"Created invoice {invoice_number} for {customer_node.properties.get('name')} - Amount: {total}")
        
        # Return invoice details
        return {
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "customer_id": customer_id,
            "customer_name": customer_node.properties.get("name"),
            "date": date,
            "due_date": due_date,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "total": total,
            "status": "open"
        }
    
    def process_payment(self,
                       payment_type: str,
                       date: str,
                       amount: float,
                       source_account_id: str,
                       destination_account_id: Optional[str] = None,
                       reference: Optional[str] = None,
                       description: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a payment.
        
        Args:
            payment_type: Type of payment (customer, vendor, transfer, etc.)
            date: Payment date (YYYY-MM-DD)
            amount: Payment amount
            source_account_id: ID of source account
            destination_account_id: ID of destination account (optional)
            reference: Reference number or code
            description: Payment description
            metadata: Additional payment metadata
            
        Returns:
            Payment details
        """
        # Validate date
        try:
            payment_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
        
        # Validate source account
        source_account = self.neural_fabric.get_node(source_account_id)
        if not source_account or source_account.node_type != "account":
            raise ValueError(f"Invalid source account ID: {source_account_id}")
        
        # Validate destination account if provided
        destination_account = None
        if destination_account_id:
            destination_account = self.neural_fabric.get_node(destination_account_id)
            if not destination_account or destination_account.node_type != "account":
                raise ValueError(f"Invalid destination account ID: {destination_account_id}")
        
        # Generate payment number if reference not provided
        if not reference:
            reference = f"PMT-{int(time.time())}"
        
        # Create payment properties
        payment_properties = {
            "payment_type": payment_type,
            "date": date,
            "amount": amount,
            "source_account_id": source_account_id,
            "source_account_name": source_account.properties.get("name"),
            "reference": reference,
            "status": "processed",
            "created_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        if destination_account_id:
            payment_properties["destination_account_id"] = destination_account_id
            payment_properties["destination_account_name"] = destination_account.properties.get("name")
            
        if description:
            payment_properties["description"] = description
        else:
            payment_properties["description"] = f"Payment {reference} from {source_account.properties.get('name')}"
            
        if metadata:
            payment_properties["metadata"] = metadata
        
        # Create payment node
        payment_id = self.neural_fabric.create_node(
            node_type="payment",
            properties=payment_properties
        )
        
        # Connect payment to accounts
        self.neural_fabric.connect_nodes(
            source_id=payment_id,
            target_id=source_account_id,
            relation_type="from_account"
        )
        
        if destination_account_id:
            self.neural_fabric.connect_nodes(
                source_id=payment_id,
                target_id=destination_account_id,
                relation_type="to_account"
            )
        
        # Handle specific payment types
        if payment_type == "customer":
            # Customer payment - handle invoice application if metadata includes invoice_id
            if metadata and "invoice_id" in metadata:
                invoice_id = metadata["invoice_id"]
                invoice_node = self.neural_fabric.get_node(invoice_id)
                
                if invoice_node and invoice_node.node_type == "invoice":
                    # Connect payment to invoice
                    self.neural_fabric.connect_nodes(
                        source_id=payment_id,
                        target_id=invoice_id,
                        relation_type="pays"
                    )
                    
                    # Update invoice status if fully paid
                    invoice_total = invoice_node.properties.get("total", 0)
                    if amount >= invoice_total:
                        self.neural_fabric.update_node(
                            node_id=invoice_id,
                            properties={"status": "paid", "paid_date": date, "payment_id": payment_id}
                        )
                    else:
                        # Mark as partially paid
                        self.neural_fabric.update_node(
                            node_id=invoice_id,
                            properties={"status": "partial", "partial_payment": amount, "payment_id": payment_id}
                        )
                        
        # Record the accounting transaction
        if payment_type == "customer":
            # Customer payment - typically Cash debit, A/R credit
            cash_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"name": "Cash"}
            )
            
            ar_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"name": "Accounts Receivable"}
            )
            
            if cash_accounts and ar_accounts:
                cash_account = cash_accounts[0]
                ar_account = ar_accounts[0]
                
                entries = [
                    {
                        "account_id": cash_account.id,
                        "type": "debit",
                        "amount": amount
                    },
                    {
                        "account_id": ar_account.id,
                        "type": "credit",
                        "amount": amount
                    }
                ]
                
                # Record the transaction
                tx_result = self.record_transaction(
                    transaction_type="payment",
                    date=date,
                    amount=amount,
                    description=payment_properties["description"],
                    entries=entries,
                    reference=reference,
                    metadata={"payment_id": payment_id}
                )
                
                # Link transaction to payment
                if tx_result and "transaction_id" in tx_result:
                    self.neural_fabric.update_node(
                        node_id=payment_id,
                        properties={"transaction_id": tx_result["transaction_id"]}
                    )
                    
                    self.neural_fabric.connect_nodes(
                        source_id=payment_id,
                        target_id=tx_result["transaction_id"],
                        relation_type="generated"
                    )
                    
        elif payment_type == "vendor":
            # Vendor payment - typically A/P debit, Cash credit
            cash_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"name": "Cash"}
            )
            
            ap_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"name": "Accounts Payable"}
            )
            
            if cash_accounts and ap_accounts:
                cash_account = cash_accounts[0]
                ap_account = ap_accounts[0]
                
                entries = [
                    {
                        "account_id": ap_account.id,
                        "type": "debit",
                        "amount": amount
                    },
                    {
                        "account_id": cash_account.id,
                        "type": "credit",
                        "amount": amount
                    }
                ]
                
                # Record the transaction
                tx_result = self.record_transaction(
                    transaction_type="payment",
                    date=date,
                    amount=amount,
                    description=payment_properties["description"],
                    entries=entries,
                    reference=reference,
                    metadata={"payment_id": payment_id}
                )
                
                # Link transaction to payment
                if tx_result and "transaction_id" in tx_result:
                    self.neural_fabric.update_node(
                        node_id=payment_id,
                        properties={"transaction_id": tx_result["transaction_id"]}
                    )
        
        # Publish event
        self.event_bus.publish(
            event_type="payment.processed",
            payload={
                "payment_id": payment_id,
                "payment_type": payment_type,
                "amount": amount,
                "date": date,
                "reference": reference
            }
        )
        
        logger.info(f"Processed {payment_type} payment: {reference} for {amount}")
        
        # Return payment details
        return {
            "payment_id": payment_id,
            "reference": reference,
            "payment_type": payment_type,
            "amount": amount,
            "date": date,
            "status": "processed"
        }
    
    def reconcile_accounts(self,
                          account_id: str,
                          statement_balance: float,
                          statement_date: str,
                          reconciled_transactions: List[str],
                          adjustments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Reconcile an account against a statement.
        
        Args:
            account_id: ID of the account to reconcile
            statement_balance: Ending balance on statement
            statement_date: Date of statement (YYYY-MM-DD)
            reconciled_transactions: List of transaction IDs that have cleared
            adjustments: Optional list of adjustments to book
            
        Returns:
            Reconciliation results
        """
        # Validate account
        account = self.neural_fabric.get_node(account_id)
        if not account or account.node_type != "account":
            raise ValueError(f"Invalid account ID: {account_id}")
        
        # Validate date
        try:
            rec_date = datetime.strptime(statement_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {statement_date}. Expected YYYY-MM-DD")
        
        # Get current system balance for the account
        system_balance = account.properties.get("balance", 0.0)
        
        # Mark transactions as reconciled
        reconciled_amount = 0.0
        for tx_id in reconciled_transactions:
            tx_node = self.neural_fabric.get_node(tx_id)
            if tx_node and tx_node.node_type == "transaction":
                # Mark transaction as reconciled
                self.neural_fabric.update_node(
                    node_id=tx_id,
                    properties={"reconciled": True, "reconciled_date": statement_date}
                )
                
                # Add transaction amount to reconciled total
                # Note: We would need to get the specific entry amount for this account,
                # but for simplicity we're using the transaction total amount
                reconciled_amount += tx_node.properties.get("amount", 0.0)
        
        # Process adjustments if any
        adjustment_ids = []
        if adjustments:
            for adj in adjustments:
                adj_amount = adj.get("amount", 0.0)
                adj_description = adj.get("description", "Reconciliation adjustment")
                
                # Create adjustment transaction
                adj_result = self.record_transaction(
                    transaction_type="adjustment",
                    date=statement_date,
                    amount=abs(adj_amount),
                    description=adj_description,
                    entries=[
                        {
                            "account_id": account_id,
                            "type": "debit" if adj_amount > 0 else "credit",
                            "amount": abs(adj_amount)
                        },
                        {
                            "account_id": adj.get("offset_account_id"),
                            "type": "credit" if adj_amount > 0 else "debit",
                            "amount": abs(adj_amount)
                        }
                    ],
                    reference=f"ADJ-{int(time.time())}",
                    metadata={"adjustment_reason": adj.get("reason")}
                )
                
                if adj_result and "transaction_id" in adj_result:
                    adjustment_ids.append(adj_result["transaction_id"])
        
        # Calculate reconciliation difference
        reconciled_balance = statement_balance
        difference = system_balance - reconciled_balance
        
        # Create reconciliation record
        reconciliation_properties = {
            "account_id": account_id,
            "account_name": account.properties.get("name"),
            "statement_date": statement_date,
            "statement_balance": statement_balance,
            "system_balance": system_balance,
            "difference": difference,
            "reconciled_transactions": len(reconciled_transactions),
            "adjustments": len(adjustment_ids) if adjustment_ids else 0,
            "status": "balanced" if abs(difference) < 0.01 else "unbalanced",
            "created_at": datetime.now().isoformat()
        }
        
        # Create reconciliation node
        reconciliation_id = self.neural_fabric.create_node(
            node_type="account_reconciliation",
            properties=reconciliation_properties
        )
        
        # Connect reconciliation to account
        self.neural_fabric.connect_nodes(
            source_id=reconciliation_id,
            target_id=account_id,
            relation_type="reconciles"
        )
        
        # Update account with last reconciliation info
        self.neural_fabric.update_node(
            node_id=account_id,
            properties={
                "last_reconciliation_date": statement_date,
                "last_reconciliation_id": reconciliation_id,
                "reconciled_balance": statement_balance
            }
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="account.reconciled",
            payload={
                "reconciliation_id": reconciliation_id,
                "account_id": account_id,
                "statement_date": statement_date,
                "difference": difference,
                "status": reconciliation_properties["status"]
            }
        )
        
        logger.info(f"Reconciled account {account.properties.get('name')} as of {statement_date}")
        
        # Return reconciliation details
        return {
            "reconciliation_id": reconciliation_id,
            "account_id": account_id,
            "account_name": account.properties.get("name"),
            "statement_date": statement_date,
            "statement_balance": statement_balance,
            "system_balance": system_balance,
            "difference": difference,
            "reconciled_transactions": len(reconciled_transactions),
            "adjustments": len(adjustment_ids) if adjustment_ids else 0,
            "status": reconciliation_properties["status"]
        }
    
    def generate_financial_report(self,
                                 report_type: str,
                                 start_date: str,
                                 end_date: str,
                                 filters: Optional[Dict[str, Any]] = None,
                                 grouping: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a financial report.
        
        Args:
            report_type: Type of report (income, balance, cash flow, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            filters: Optional filters for report data
            grouping: Optional grouping options
            
        Returns:
            Report data
        """
        # Validate dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
        
        # Choose report generation method based on type
        if report_type == "income_statement":
            report_data = self._generate_income_statement(start_date, end_date, filters, grouping)
        elif report_type == "balance_sheet":
            report_data = self._generate_balance_sheet(end_date, filters, grouping)
        elif report_type == "cash_flow":
            report_data = self._generate_cash_flow_statement(start_date, end_date, filters, grouping)
        elif report_type == "trial_balance":
            report_data = self._generate_trial_balance(end_date, filters)
        elif report_type == "general_ledger":
            report_data = self._generate_general_ledger(start_date, end_date, filters)
        elif report_type == "accounts_receivable_aging":
            report_data = self._generate_ar_aging(end_date, filters)
        elif report_type == "accounts_payable_aging":
            report_data = self._generate_ap_aging(end_date, filters)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Create report record
        report_properties = {
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().isoformat(),
            "report_data": report_data
        }
        
        # Add filters if provided
        if filters:
            report_properties["filters"] = filters
            
        # Add grouping if provided
        if grouping:
            report_properties["grouping"] = grouping
        
        # Create report node
        report_id = self.neural_fabric.create_node(
            node_type="financial_report",
            properties=report_properties
        )
        
        logger.info(f"Generated {report_type} for period {start_date} to {end_date}")
        
        # Return report with data
        return {
            "report_id": report_id,
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "data": report_data
        }
    
    def _generate_income_statement(self, start_date, end_date, filters=None, grouping=None):
        """Generate income statement data."""
        # Get revenue accounts
        revenue_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"type": "revenue"}
        )
        
        # Get expense accounts
        expense_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"type": "expense"}
        )
        
        # Calculate revenue
        revenue_data = self._calculate_account_group_activity(
            revenue_accounts, 
            start_date, 
            end_date,
            grouping
        )
        
        # Calculate expenses
        expense_data = self._calculate_account_group_activity(
            expense_accounts, 
            start_date, 
            end_date,
            grouping
        )
        
        # Calculate net income
        total_revenue = sum(acct["balance"] for acct in revenue_data["accounts"])
        total_expenses = sum(acct["balance"] for acct in expense_data["accounts"])
        net_income = total_revenue - total_expenses
        
        return {
            "revenue": revenue_data,
            "expenses": expense_data,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
    
    def _generate_balance_sheet(self, as_of_date, filters=None, grouping=None):
        """Generate balance sheet data."""
        # Get asset accounts
        asset_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"type": "asset"}
        )
        
        # Get liability accounts
        liability_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"type": "liability"}
        )
        
        # Get equity accounts
        equity_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"type": "equity"}
        )
        
        # Calculate assets
        asset_data = self._calculate_account_group_balances(
            asset_accounts, 
            as_of_date,
            grouping
        )
        
        # Calculate liabilities
        liability_data = self._calculate_account_group_balances(
            liability_accounts, 
            as_of_date,
            grouping
        )
        
        # Calculate equity
        equity_data = self._calculate_account_group_balances(
            equity_accounts, 
            as_of_date,
            grouping
        )
        
        # Calculate totals
        total_assets = sum(acct["balance"] for acct in asset_data["accounts"])
        total_liabilities = sum(acct["balance"] for acct in liability_data["accounts"])
        total_equity = sum(acct["balance"] for acct in equity_data["accounts"])
        
        return {
            "assets": asset_data,
            "liabilities": liability_data,
            "equity": equity_data,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "liabilities_and_equity": total_liabilities + total_equity,
            "as_of_date": as_of_date
        }
    
    def _generate_cash_flow_statement(self, start_date, end_date, filters=None, grouping=None):
        """Generate cash flow statement data."""
        # Basic implementation - in a real system this would be more complex
        # Get cash accounts
        cash_accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters={"name": "Cash"}
        )
        
        if not cash_accounts:
            return {"error": "Cash account not found"}
        
        cash_account = cash_accounts[0]
        
        # Get transactions for the cash account
        cash_entries = []
        transactions = self.neural_fabric.query_nodes(
            node_type="transaction",
            limit=1000
        )
        
        for tx in transactions:
            tx_date = tx.properties.get("date")
            if tx_date and start_date <= tx_date <= end_date:
                # Get entries for this transaction
                entries = self.neural_fabric.get_connected_nodes(
                    node_id=tx.id,
                    relation_type="part_of_inverse"
                )
                
                if "part_of_inverse" in entries:
                    for entry in entries["part_of_inverse"]:
                        if entry.properties.get("account_id") == cash_account.id:
                            cash_entries.append({
                                "transaction_id": tx.id,
                                "date": tx_date,
                                "description": tx.properties.get("description"),
                                "type": entry.properties.get("type"),
                                "amount": entry.properties.get("amount"),
                                "transaction_type": tx.properties.get("transaction_type")
                            })
        
        # Categorize cash flows
        operating_flows = []
        investing_flows = []
        financing_flows = []
        
        for entry in cash_entries:
            tx_type = entry.get("transaction_type", "").lower()
            
            if tx_type in ["invoice", "payment", "expense"]:
                operating_flows.append(entry)
            elif tx_type in ["asset_purchase", "asset_sale", "investment"]:
                investing_flows.append(entry)
            elif tx_type in ["loan", "equity", "dividend"]:
                financing_flows.append(entry)
            else:
                # Default to operating
                operating_flows.append(entry)
        
        # Calculate totals
        def calculate_flow_total(entries):
            total = 0
            for entry in entries:
                if entry.get("type") == "debit":
                    total += entry.get("amount", 0)
                else:
                    total -= entry.get("amount", 0)
            return total
        
        operating_total = calculate_flow_total(operating_flows)
        investing_total = calculate_flow_total(investing_flows)
        financing_total = calculate_flow_total(financing_flows)
        net_change = operating_total + investing_total + financing_total
        
        # Get beginning and ending balances
        beginning_balance = 0  # Would need to calculate from entries before start_date
        ending_balance = beginning_balance + net_change
        
        return {
            "operating_activities": {
                "entries": operating_flows,
                "total": operating_total
            },
            "investing_activities": {
                "entries": investing_flows,
                "total": investing_total
            },
            "financing_activities": {
                "entries": financing_flows,
                "total": financing_total
            },
            "beginning_balance": beginning_balance,
            "net_change": net_change,
            "ending_balance": ending_balance,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
    
    def _generate_trial_balance(self, as_of_date, filters=None):
        """Generate trial balance data."""
        # Get all accounts
        accounts = self.neural_fabric.query_nodes(
            node_type="account",
            limit=1000
        )
        
        # Calculate balances
        debit_accounts = []
        credit_accounts = []
        total_debits = 0
        total_credits = 0
        
        for acct in accounts:
            balance = acct.properties.get("balance", 0)
            account_type = acct.properties.get("type")
            
            # Determine if account has debit or credit balance
            is_debit_balance = account_type in ["asset", "expense"]
            
            if (is_debit_balance and balance > 0) or (not is_debit_balance and balance < 0):
                # Account has debit balance
                debit_amount = abs(balance)
                debit_accounts.append({
                    "account_id": acct.id,
                    "number": acct.properties.get("number"),
                    "name": acct.properties.get("name"),
                    "type": account_type,
                    "balance": debit_amount
                })
                total_debits += debit_amount
            else:
                # Account has credit balance
                credit_amount = abs(balance)
                credit_accounts.append({
                    "account_id": acct.id,
                    "number": acct.properties.get("number"),
                    "name": acct.properties.get("name"),
                    "type": account_type,
                    "balance": credit_amount
                })
                total_credits += credit_amount
        
        # Sort accounts by number
        debit_accounts.sort(key=lambda x: x.get("number", ""))
        credit_accounts.sort(key=lambda x: x.get("number", ""))
        
        return {
            "debit_accounts": debit_accounts,
            "credit_accounts": credit_accounts,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "balanced": abs(total_debits - total_credits) < 0.01,
            "as_of_date": as_of_date
        }
    
    def _generate_general_ledger(self, start_date, end_date, filters=None):
        """Generate general ledger data."""
        # Get accounts with optional filtering
        account_filters = {}
        if filters and "account_type" in filters:
            account_filters["type"] = filters["account_type"]
            
        accounts = self.neural_fabric.query_nodes(
            node_type="account",
            filters=account_filters,
            limit=1000
        )
        
        # Sort accounts by number
        accounts.sort(key=lambda x: x.properties.get("number", ""))
        
        ledger_data = []
        
        for acct in accounts:
            # Get entries for this account
            account_entries = []
            
            # Get transactions for this period
            transactions = self.neural_fabric.query_nodes(
                node_type="transaction",
                limit=1000
            )
            
            for tx in transactions:
                tx_date = tx.properties.get("date")
                if tx_date and start_date <= tx_date <= end_date:
                    # Get entries for this transaction
                    entries = self.neural_fabric.get_connected_nodes(
                        node_id=tx.id,
                        relation_type="part_of_inverse"
                    )
                    
                    if "part_of_inverse" in entries:
                        for entry in entries["part_of_inverse"]:
                            if entry.properties.get("account_id") == acct.id:
                                account_entries.append({
                                    "transaction_id": tx.id,
                                    "date": tx_date,
                                    "description": tx.properties.get("description"),
                                    "reference": tx.properties.get("reference"),
                                    "type": entry.properties.get("type"),
                                    "amount": entry.properties.get("amount"),
                                    "transaction_type": tx.properties.get("transaction_type")
                                })
            
            # Sort entries by date
            account_entries.sort(key=lambda x: x.get("date", ""))
            
            # Calculate beginning and ending balances
            beginning_balance = 0  # Would need to calculate from entries before start_date
            ending_balance = beginning_balance
            
            for entry in account_entries:
                if entry.get("type") == "debit":
                    ending_balance += entry.get("amount", 0)
                else:
                    ending_balance -= entry.get("amount", 0)
            
            # Add account data to ledger
            ledger_data.append({
                "account_id": acct.id,
                "number": acct.properties.get("number"),
                "name": acct.properties.get("name"),
                "type": acct.properties.get("type"),
                "beginning_balance": beginning_balance,
                "ending_balance": ending_balance,
                "entries": account_entries
            })
        
        return {
            "accounts": ledger_data,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
    
    def _generate_ar_aging(self, as_of_date, filters=None):
        """Generate accounts receivable aging report."""
        # Get open invoices
        invoices = self.neural_fabric.query_nodes(
            node_type="invoice",
            filters={"status": ["open", "partial"]},
            limit=1000
        )
        
        # Categorize by age
        current_invoices = []
        days_1_30 = []
        days_31_60 = []
        days_61_90 = []
        days_over_90 = []
        
        as_of = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        
        for inv in invoices:
            due_date = inv.properties.get("due_date")
            if not due_date:
                continue
                
            try:
                due = datetime.strptime(due_date, "%Y-%m-%d").date()
                days_outstanding = (as_of - due).days
                
                # Get outstanding amount
                total = inv.properties.get("total", 0)
                paid = inv.properties.get("partial_payment", 0)
                outstanding = total - paid
                
                invoice_data = {
                    "invoice_id": inv.id,
                    "invoice_number": inv.properties.get("invoice_number"),
                    "customer_id": inv.properties.get("customer_id"),
                    "customer_name": inv.properties.get("customer_name"),
                    "date": inv.properties.get("date"),
                    "due_date": due_date,
                    "total": total,
                    "paid": paid,
                    "outstanding": outstanding,
                    "days_outstanding": days_outstanding
                }
                
                # Categorize by age
                if days_outstanding <= 0:
                    current_invoices.append(invoice_data)
                elif days_outstanding <= 30:
                    days_1_30.append(invoice_data)
                elif days_outstanding <= 60:
                    days_31_60.append(invoice_data)
                elif days_outstanding <= 90:
                    days_61_90.append(invoice_data)
                else:
                    days_over_90.append(invoice_data)
            except ValueError:
                continue
        
        # Calculate totals
        current_total = sum(inv["outstanding"] for inv in current_invoices)
        days_1_30_total = sum(inv["outstanding"] for inv in days_1_30)
        days_31_60_total = sum(inv["outstanding"] for inv in days_31_60)
        days_61_90_total = sum(inv["outstanding"] for inv in days_61_90)
        days_over_90_total = sum(inv["outstanding"] for inv in days_over_90)
        
        grand_total = current_total + days_1_30_total + days_31_60_total + days_61_90_total + days_over_90_total
        
        return {
            "current": {
                "invoices": current_invoices,
                "total": current_total
            },
            "days_1_30": {
                "invoices": days_1_30,
                "total": days_1_30_total
            },
            "days_31_60": {
                "invoices": days_31_60,
                "total": days_31_60_total
            },
            "days_61_90": {
                "invoices": days_61_90,
                "total": days_61_90_total
            },
            "days_over_90": {
                "invoices": days_over_90,
                "total": days_over_90_total
            },
            "total_outstanding": grand_total,
            "as_of_date": as_of_date
        }
    
    def _generate_ap_aging(self, as_of_date, filters=None):
        """Generate accounts payable aging report."""
        # Similar to AR aging but for vendor bills
        # This would be implemented similar to the AR aging report but for vendor bills
        return {"message": "AP aging report not yet implemented"}
    
    def _calculate_account_group_balances(self, accounts, as_of_date, grouping=None):
        """Calculate account balances for a group of accounts."""
        total_balance = 0
        account_data = []
        
        for acct in accounts:
            balance = acct.properties.get("balance", 0)
            account_data.append({
                "account_id": acct.id,
                "number": acct.properties.get("number"),
                "name": acct.properties.get("name"),
                "type": acct.properties.get("type"),
                "subtype": acct.properties.get("subtype"),
                "balance": balance
            })
            total_balance += balance
        
        # Group if needed
        grouped_data = {}
        if grouping:
            for acct in account_data:
                for group_field in grouping:
                    if group_field in acct:
                        group_value = acct[group_field]
                        if group_value not in grouped_data:
                            grouped_data[group_value] = {
                                "accounts": [],
                                "total": 0
                            }
                        grouped_data[group_value]["accounts"].append(acct)
                        grouped_data[group_value]["total"] += acct["balance"]
        
        return {
            "accounts": account_data,   # List of accounts with balances
            "total": total_balance,     # Total balance of all accounts
            "grouped": grouped_data     # Grouped data if requested
        }