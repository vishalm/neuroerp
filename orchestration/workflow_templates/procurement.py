"""
Procurement Workflow Template for AI-Native ERP System

This module defines an autonomous, self-optimizing workflow for procurement processes
that coordinates multiple AI agents, adapts to different purchase types, and
continuously improves based on historical data and outcomes.
"""

import datetime
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

from orchestration.workflow_engine import Workflow, Task, Condition, AgentTask
from orchestration.task_scheduler import Priority


class ProcurementWorkflow(Workflow):
    """
    Adaptive procurement workflow that coordinates requisition, approval, vendor selection,
    purchase order management, and receipt processing with autonomous optimization.
    """

    def __init__(
        self,
        request_id: str,
        requester_id: str,
        department: str,
        items: List[Dict[str, Any]],
        total_amount: Union[float, Decimal],
        urgency: str = "normal",
        budget_code: Optional[str] = None,
        project_id: Optional[str] = None,
        preferred_vendors: Optional[List[str]] = None
    ):
        """
        Initialize the procurement workflow with request details.

        Args:
            request_id: Unique identifier for the purchase request
            requester_id: Employee ID of the person making the request
            department: Department making the request
            items: List of items to be purchased with details
            total_amount: Total estimated cost of the purchase
            urgency: Priority of the request (critical, high, normal, low)
            budget_code: Budget code to charge the purchase against
            project_id: Related project identifier if applicable
            preferred_vendors: List of preferred vendor IDs if any
        """
        super().__init__(
            workflow_id=f"procurement-{request_id}",
            name=f"Procurement Request {request_id}",
            description=f"Procurement workflow for request {request_id} from {department}"
        )
        
        self.request_id = request_id
        self.requester_id = requester_id
        self.department = department
        self.items = items
        self.total_amount = Decimal(str(total_amount)) if isinstance(total_amount, float) else total_amount
        self.urgency = urgency.lower()
        self.budget_code = budget_code
        self.project_id = project_id
        self.preferred_vendors = preferred_vendors or []
        
        # Set workflow metadata for analytics and optimization
        self.metadata.update({
            "workflow_type": "procurement",
            "department": department,
            "total_amount": str(self.total_amount),
            "item_count": len(items),
            "urgency": urgency
        })
        
        # Define the procurement workflow tasks and structure
        self._create_workflow_structure()
    
    def _create_workflow_structure(self):
        """Define the tasks, dependencies, and conditions for the procurement workflow."""
        
        # Set priority based on urgency
        priority_map = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "normal": Priority.MEDIUM,
            "low": Priority.LOW
        }
        request_priority = priority_map.get(self.urgency, Priority.MEDIUM)
        
        # Initial validation task
        self.add_task(
            AgentTask(
                task_id="validate_request",
                agent_type="procurement",
                action="validate_purchase_request",
                parameters={
                    "request_id": self.request_id,
                    "requester_id": self.requester_id,
                    "items": self.items,
                    "department": self.department,
                    "budget_code": self.budget_code
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=1)
            )
        )
        
        # Budget verification
        self.add_task(
            AgentTask(
                task_id="verify_budget",
                agent_type="finance",
                action="verify_available_budget",
                parameters={
                    "department": self.department,
                    "budget_code": self.budget_code,
                    "amount": str(self.total_amount),
                    "project_id": self.project_id
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=2),
                depends_on=["validate_request"]
            )
        )
        
        # Approval tasks - dynamically created based on amount
        self._add_approval_tasks()
        
        # Vendor selection
        self.add_task(
            AgentTask(
                task_id="vendor_selection",
                agent_type="procurement",
                action="select_optimal_vendors",
                parameters={
                    "items": self.items,
                    "preferred_vendors": self.preferred_vendors,
                    "total_amount": str(self.total_amount),
                    "urgency": self.urgency
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=3),
                depends_on=["final_approval"]
            )
        )
        
        # Create purchase order
        self.add_task(
            AgentTask(
                task_id="create_purchase_order",
                agent_type="procurement",
                action="generate_purchase_order",
                parameters={
                    "request_id": self.request_id,
                    "items": self.items,
                    "department": self.department,
                    "budget_code": self.budget_code,
                    "project_id": self.project_id
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=2),
                depends_on=["vendor_selection"]
            )
        )
        
        # Send to vendor
        self.add_task(
            AgentTask(
                task_id="send_to_vendor",
                agent_type="procurement",
                action="submit_purchase_order",
                parameters={
                    "request_id": self.request_id
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=1),
                depends_on=["create_purchase_order"]
            )
        )
        
        # Order tracking
        self.add_task(
            AgentTask(
                task_id="track_order",
                agent_type="procurement",
                action="monitor_order_status",
                parameters={
                    "request_id": self.request_id,
                    "expected_delivery": None  # Will be updated when PO is sent
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(days=1),
                depends_on=["send_to_vendor"]
            )
        )
        
        # Receive items
        self.add_task(
            AgentTask(
                task_id="receive_items",
                agent_type="warehouse",
                action="process_item_receipt",
                parameters={
                    "request_id": self.request_id,
                    "expected_items": self.items
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=2),
                depends_on=["track_order"]
            )
        )
        
        # Process invoice
        self.add_task(
            AgentTask(
                task_id="process_invoice",
                agent_type="finance",
                action="match_and_process_invoice",
                parameters={
                    "request_id": self.request_id,
                    "purchase_order_id": None  # Will be updated when PO is created
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=2),
                depends_on=["receive_items"]
            )
        )
        
        # Process payment
        self.add_task(
            AgentTask(
                task_id="process_payment",
                agent_type="finance",
                action="issue_payment",
                parameters={
                    "request_id": self.request_id,
                    "invoice_id": None  # Will be updated when invoice is processed
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(hours=2),
                depends_on=["process_invoice"]
            )
        )
        
        # Requester notification
        self.add_task(
            AgentTask(
                task_id="notify_requester",
                agent_type="communications",
                action="send_completion_notification",
                parameters={
                    "request_id": self.request_id,
                    "requester_id": self.requester_id,
                    "notification_type": "procurement_complete"
                },
                priority=request_priority,
                estimated_duration=datetime.timedelta(minutes=30),
                depends_on=["receive_items"]
            )
        )
        
        # Vendor evaluation
        self.add_task(
            AgentTask(
                task_id="evaluate_vendor",
                agent_type="procurement",
                action="collect_vendor_performance",
                parameters={
                    "request_id": self.request_id,
                    "evaluation_criteria": ["delivery_time", "quality", "price_accuracy", "communication"]
                },
                priority=Priority.LOW,
                estimated_duration=datetime.timedelta(hours=1),
                depends_on=["receive_items", "process_payment"],
                scheduled_time=datetime.datetime.now() + datetime.timedelta(days=7)
            )
        )
    
    def _add_approval_tasks(self):
        """Add approval tasks based on amount thresholds and department policies."""
        
        # Define approval task dependencies
        previous_approval = "verify_budget"
        
        # Manager approval for all purchases
        self.add_task(
            AgentTask(
                task_id="manager_approval",
                agent_type="approvals",
                action="request_manager_approval",
                parameters={
                    "request_id": self.request_id,
                    "requester_id": self.requester_id,
                    "amount": str(self.total_amount),
                    "items": self.items
                },
                priority=self._get_approval_priority(),
                estimated_duration=datetime.timedelta(hours=4),
                depends_on=[previous_approval]
            )
        )
        previous_approval = "manager_approval"
        
        # Director approval for purchases over $5,000
        if self.total_amount >= 5000:
            self.add_task(
                AgentTask(
                    task_id="director_approval",
                    agent_type="approvals",
                    action="request_director_approval",
                    parameters={
                        "request_id": self.request_id,
                        "department": self.department,
                        "amount": str(self.total_amount),
                        "items_summary": [{"name": item["name"], "cost": item.get("estimated_cost", "N/A")} 
                                           for item in self.items]
                    },
                    priority=self._get_approval_priority(),
                    estimated_duration=datetime.timedelta(hours=8),
                    depends_on=[previous_approval]
                )
            )
            previous_approval = "director_approval"
        
        # VP approval for purchases over $25,000
        if self.total_amount >= 25000:
            self.add_task(
                AgentTask(
                    task_id="vp_approval",
                    agent_type="approvals",
                    action="request_vp_approval",
                    parameters={
                        "request_id": self.request_id,
                        "department": self.department,
                        "amount": str(self.total_amount),
                        "business_justification": self._extract_business_justification()
                    },
                    priority=self._get_approval_priority(),
                    estimated_duration=datetime.timedelta(days=2),
                    depends_on=[previous_approval]
                )
            )
            previous_approval = "vp_approval"
        
        # CFO approval for purchases over $100,000
        if self.total_amount >= 100000:
            self.add_task(
                AgentTask(
                    task_id="cfo_approval",
                    agent_type="approvals",
                    action="request_cfo_approval",
                    parameters={
                        "request_id": self.request_id,
                        "department": self.department,
                        "amount": str(self.total_amount),
                        "items": self.items,
                        "budget_impact_analysis": None  # Will be updated from budget verification
                    },
                    priority=self._get_approval_priority(),
                    estimated_duration=datetime.timedelta(days=3),
                    depends_on=[previous_approval]
                )
            )
            previous_approval = "cfo_approval"
        
        # Final approval task (marks the end of approval chain)
        self.add_task(
            Task(
                task_id="final_approval",
                action=lambda: {"status": "approved", "timestamp": datetime.datetime.now().isoformat()},
                depends_on=[previous_approval]
            )
        )
    
    def _get_approval_priority(self) -> Priority:
        """Determine approval priority based on urgency and amount."""
        if self.urgency == "critical":
            return Priority.CRITICAL
        elif self.urgency == "high":
            return Priority.HIGH
        elif self.total_amount > 50000:
            return Priority.HIGH
        else:
            return Priority.MEDIUM
    
    def _extract_business_justification(self) -> str:
        """Extract business justification from items metadata."""
        # In a real implementation, this would extract from the request data
        # For now, return a placeholder
        return "Business justification will be extracted from request details"
    
    def on_task_completed(self, task_id: str, result: Dict[str, Any]):
        """Handle task completion events and adapt workflow if needed."""
        super().on_task_completed(task_id, result)
        
        # Update PO number when created
        if task_id == "create_purchase_order" and "purchase_order_id" in result:
            po_id = result["purchase_order_id"]
            
            # Update dependent tasks with PO information
            process_invoice_task = self.get_task("process_invoice")
            if process_invoice_task:
                process_invoice_task.parameters["purchase_order_id"] = po_id
            
            # Update expected delivery date if available
            if "expected_delivery" in result:
                track_order_task = self.get_task("track_order")
                if track_order_task:
                    track_order_task.parameters["expected_delivery"] = result["expected_delivery"]
        
        # Update invoice ID when processed
        if task_id == "process_invoice" and "invoice_id" in result:
            invoice_id = result["invoice_id"]
            
            # Update payment task with invoice information
            payment_task = self.get_task("process_payment")
            if payment_task:
                payment_task.parameters["invoice_id"] = invoice_id
        
        # Handle budget verification results
        if task_id == "verify_budget":
            # If budget is insufficient, add a budget exception task
            if result.get("status") == "insufficient_funds":
                self.add_task(
                    AgentTask(
                        task_id="budget_exception",
                        agent_type="finance",
                        action="process_budget_exception",
                        parameters={
                            "request_id": self.request_id,
                            "department": self.department,
                            "budget_code": self.budget_code,
                            "shortfall": result.get("shortfall"),
                            "options": result.get("funding_options", [])
                        },
                        priority=Priority.HIGH,
                        estimated_duration=datetime.timedelta(hours=4),
                        depends_on=["verify_budget"]
                    )
                )
                
                # Update the dependencies for manager approval
                manager_approval_task = self.get_task("manager_approval")
                if manager_approval_task:
                    manager_approval_task.depends_on.append("budget_exception")
            
            # If high-value purchase, update CFO approval with budget impact
            if self.total_amount >= 100000:
                cfo_approval_task = self.get_task("cfo_approval")
                if cfo_approval_task:
                    cfo_approval_task.parameters["budget_impact_analysis"] = result.get("budget_impact")
        
        # Process vendor selection results
        if task_id == "vendor_selection":
            selected_vendors = result.get("selected_vendors", [])
            
            # If multiple vendors selected, create sub-workflows for each
            if len(selected_vendors) > 1:
                for i, vendor in enumerate(selected_vendors):
                    vendor_items = vendor.get("items", [])
                    vendor_amount = vendor.get("total_amount", 0)
                    vendor_id = vendor.get("vendor_id")
                    
                    # Create a sub-workflow for this vendor
                    self.add_task(
                        AgentTask(
                            task_id=f"vendor_po_{i+1}",
                            agent_type="procurement",
                            action="create_vendor_specific_po",
                            parameters={
                                "request_id": self.request_id,
                                "vendor_id": vendor_id,
                                "items": vendor_items,
                                "total_amount": vendor_amount,
                                "is_split_order": True
                            },
                            priority=self._get_approval_priority(),
                            estimated_duration=datetime.timedelta(hours=2),
                            depends_on=["create_purchase_order"]
                        )
                    )
        
        # If items received with quality issues
        if task_id == "receive_items" and result.get("quality_issues", False):
            issues = result.get("issue_details", {})
            
            # Add quality issue resolution task
            self.add_task(
                AgentTask(
                    task_id="resolve_quality_issues",
                    agent_type="procurement",
                    action="handle_quality_issues",
                    parameters={
                        "request_id": self.request_id,
                        "issues": issues,
                        "vendor_id": result.get("vendor_id")
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(days=1),
                    depends_on=["receive_items"]
                )
            )
            
            # Update dependencies to wait for issue resolution
            notify_task = self.get_task("notify_requester")
            if notify_task:
                notify_task.depends_on.append("resolve_quality_issues")
    
    def on_error(self, task_id: str, error: Exception):
        """Handle task failures and implement recovery strategies."""
        super().on_error(task_id, error)
        
        # Handle vendor selection failures
        if task_id == "vendor_selection":
            # Add a manual intervention task
            self.add_task(
                AgentTask(
                    task_id="manual_vendor_selection",
                    agent_type="procurement",
                    action="request_manual_vendor_selection",
                    parameters={
                        "request_id": self.request_id,
                        "items": self.items,
                        "error_details": str(error)
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=4)
                )
            )
            
            # Update dependencies
            create_po_task = self.get_task("create_purchase_order")
            if create_po_task:
                create_po_task.depends_on = ["manual_vendor_selection"]
        
        # Handle approval errors
        elif "approval" in task_id:
            # Add an escalation task
            self.add_task(
                AgentTask(
                    task_id=f"{task_id}_escalation",
                    agent_type="approvals",
                    action="escalate_approval_request",
                    parameters={
                        "request_id": self.request_id,
                        "original_approval": task_id,
                        "error_details": str(error)
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=2)
                )
            )
            
        # Handle payment processing errors
        elif task_id == "process_payment":
            # Add a payment exception task
            self.add_task(
                AgentTask(
                    task_id="payment_exception",
                    agent_type="finance",
                    action="handle_payment_exception",
                    parameters={
                        "request_id": self.request_id,
                        "error_details": str(error)
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=3)
                )
            )
    
    def optimize_from_history(self, similar_workflows: List[Dict[str, Any]]):
        """Optimize workflow based on historical data from similar procurement requests."""
        if not similar_workflows:
            return
        
        # Calculate average durations for common tasks
        task_durations = {}
        for workflow in similar_workflows:
            tasks = workflow.get("tasks", {})
            for task_id, task_data in tasks.items():
                if "actual_duration" in task_data and task_id in self.tasks:
                    if task_id not in task_durations:
                        task_durations[task_id] = []
                    task_durations[task_id].append(task_data["actual_duration"])
        
        # Update estimated durations based on historical data
        for task_id, durations in task_durations.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                task = self.get_task(task_id)
                if task:
                    task.estimated_duration = avg_duration
        
        # Identify optimal vendors based on historical performance
        vendor_performances = {}
        for workflow in similar_workflows:
            vendor_eval = workflow.get("vendor_evaluation", {})
            vendor_id = vendor_eval.get("vendor_id")
            if vendor_id and "score" in vendor_eval:
                if vendor_id not in vendor_performances:
                    vendor_performances[vendor_id] = []
                vendor_performances[vendor_id].append(vendor_eval["score"])
        
        # Sort vendors by average performance score
        avg_performances = {
            vendor_id: sum(scores) / len(scores) 
            for vendor_id, scores in vendor_performances.items()
        }
        
        optimal_vendors = sorted(
            avg_performances.keys(),
            key=lambda v: avg_performances[v],
            reverse=True
        )
        
        # Update preferred vendors with historically optimal ones
        if optimal_vendors:
            vendor_task = self.get_task("vendor_selection")
            if vendor_task:
                # Combine historical best vendors with explicitly preferred ones
                historical_best = optimal_vendors[:3]  # Top 3 historical vendors
                combined_preferred = list(set(self.preferred_vendors + historical_best))
                vendor_task.parameters["preferred_vendors"] = combined_preferred