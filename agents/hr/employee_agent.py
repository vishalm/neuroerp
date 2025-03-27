"""
Employee Agent for NeuroERP.

This agent manages employee data, performance tracking, onboarding/offboarding,
benefits administration, and other employee lifecycle processes.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime, date

from ...core.config import Config
from ...core.event_bus import EventBus
from ...core.neural_fabric import NeuralFabric
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

class EmployeeAgent(BaseAgent):
    """AI Agent for employee management."""
    
    def __init__(self, name: str = "Employee Agent", ai_engine=None, vector_store=None):
        """Initialize the employee agent.
        
        Args:
            name: Name of the agent
            ai_engine: AI engine for advanced processing
            vector_store: Vector store for semantic search
        """
        super().__init__(name=name, agent_type="hr.employee", ai_engine=ai_engine, vector_store=vector_store)
        
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
        self.register_skill("create_employee", self.create_employee)
        self.register_skill("update_employee", self.update_employee)
        self.register_skill("terminate_employee", self.terminate_employee)
        self.register_skill("process_promotion", self.process_promotion)
        self.register_skill("manage_benefits", self.manage_benefits)
        self.register_skill("track_performance", self.track_performance)
        self.register_skill("analyze_workforce", self.analyze_workforce)
        self.register_skill("generate_hr_documents", self.generate_hr_documents)
        self.register_skill("handle_pto_request", self.handle_pto_request)
    
    def _subscribe_to_events(self):
        """Subscribe to relevant system events."""
        self.event_bus.subscribe("employee.onboarding.started", self._handle_onboarding)
        self.event_bus.subscribe("employee.offboarding.started", self._handle_offboarding)
        self.event_bus.subscribe("employee.promotion.approved", self._handle_promotion)
        self.event_bus.subscribe("employee.review.completed", self._handle_review)
        self.event_bus.subscribe("employee.pto.requested", self._handle_pto_request)
    
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
            if action == "create_employee":
                return {"success": True, "result": self.create_employee(**parameters)}
            elif action == "update_employee":
                return {"success": True, "result": self.update_employee(**parameters)}
            elif action == "terminate_employee":
                return {"success": True, "result": self.terminate_employee(**parameters)}
            elif action == "process_promotion":
                return {"success": True, "result": self.process_promotion(**parameters)}
            elif action == "manage_benefits":
                return {"success": True, "result": self.manage_benefits(**parameters)}
            elif action == "track_performance":
                return {"success": True, "result": self.track_performance(**parameters)}
            elif action == "analyze_workforce":
                return {"success": True, "result": self.analyze_workforce(**parameters)}
            elif action == "generate_hr_documents":
                return {"success": True, "result": self.generate_hr_documents(**parameters)}
            elif action == "handle_pto_request":
                return {"success": True, "result": self.handle_pto_request(**parameters)}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [skill["name"] for skill in self.skills]
                }
        except Exception as e:
            logger.error(f"Error processing {action}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def create_employee(self, 
                       first_name: str,
                       last_name: str,
                       position: str,
                       department: str,
                       email: str,
                       hire_date: str,
                       manager_id: Optional[str] = None,
                       salary: Optional[float] = None,
                       additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new employee record.
        
        Args:
            first_name: Employee's first name
            last_name: Employee's last name
            position: Job position/title
            department: Department name
            email: Work email address
            hire_date: Hire date (YYYY-MM-DD)
            manager_id: ID of the employee's manager
            salary: Annual salary
            additional_info: Additional employee information
            
        Returns:
            Employee information including ID
        """
        # Parse hire date
        try:
            hire_date_obj = datetime.strptime(hire_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid hire date format: {hire_date}. Expected YYYY-MM-DD")
        
        # Create base employee properties
        employee_properties = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "position": position,
            "department": department,
            "email": email,
            "hire_date": hire_date,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        if salary is not None:
            employee_properties["salary"] = salary
            
        # Add additional info
        if additional_info:
            for key, value in additional_info.items():
                if key not in employee_properties:
                    employee_properties[key] = value
        
        # Create employee node in neural fabric
        employee_id = self.neural_fabric.create_node(
            node_type="employee",
            properties=employee_properties
        )
        
        # Connect to manager if specified
        if manager_id:
            manager_node = self.neural_fabric.get_node(manager_id)
            if manager_node and manager_node.node_type == "employee":
                self.neural_fabric.connect_nodes(
                    source_id=employee_id,
                    target_id=manager_id,
                    relation_type="reports_to"
                )
        
        # Connect to department
        department_nodes = self.neural_fabric.query_nodes(
            node_type="department",
            filters={"name": department}
        )
        
        if department_nodes:
            department_node = department_nodes[0]
            self.neural_fabric.connect_nodes(
                source_id=employee_id,
                target_id=department_node.id,
                relation_type="belongs_to"
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="employee.created",
            payload={
                "employee_id": employee_id,
                "employee_name": f"{first_name} {last_name}",
                "department": department,
                "position": position
            }
        )
        
        logger.info(f"Created employee: {first_name} {last_name} (ID: {employee_id})")
        
        # Return employee info
        return {
            "employee_id": employee_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "position": position,
            "department": department,
            "hire_date": hire_date,
            "manager_id": manager_id
        }
    
    def update_employee(self,
                       employee_id: str,
                       updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an employee's information.
        
        Args:
            employee_id: ID of the employee to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated employee information
        """
        # Get employee node
        employee_node = self.neural_fabric.get_node(employee_id)
        if not employee_node or employee_node.node_type != "employee":
            raise ValueError(f"Employee not found with ID: {employee_id}")
        
        # Update neural fabric node
        self.neural_fabric.update_node(
            node_id=employee_id,
            properties=updates
        )
        
        # Handle manager change if present
        if "manager_id" in updates:
            new_manager_id = updates["manager_id"]
            
            # Get current manager connections
            connections = self.neural_fabric.get_connected_nodes(
                node_id=employee_id,
                relation_type="reports_to"
            )
            
            # Remove existing manager connections
            if "reports_to" in connections:
                for manager_node in connections["reports_to"]:
                    self.neural_fabric.disconnect_nodes(
                        source_id=employee_id,
                        target_id=manager_node.id,
                        relation_type="reports_to"
                    )
            
            # Add new manager connection if valid
            if new_manager_id:
                manager_node = self.neural_fabric.get_node(new_manager_id)
                if manager_node and manager_node.node_type == "employee":
                    self.neural_fabric.connect_nodes(
                        source_id=employee_id,
                        target_id=new_manager_id,
                        relation_type="reports_to"
                    )
        
        # Handle department change if present
        if "department" in updates:
            new_department = updates["department"]
            
            # Get current department connections
            connections = self.neural_fabric.get_connected_nodes(
                node_id=employee_id,
                relation_type="belongs_to"
            )
            
            # Remove existing department connections
            if "belongs_to" in connections:
                for dept_node in connections["belongs_to"]:
                    if dept_node.node_type == "department":
                        self.neural_fabric.disconnect_nodes(
                            source_id=employee_id,
                            target_id=dept_node.id,
                            relation_type="belongs_to"
                        )
            
            # Add new department connection
            department_nodes = self.neural_fabric.query_nodes(
                node_type="department",
                filters={"name": new_department}
            )
            
            if department_nodes:
                department_node = department_nodes[0]
                self.neural_fabric.connect_nodes(
                    source_id=employee_id,
                    target_id=department_node.id,
                    relation_type="belongs_to"
                )
        
        # Publish event
        self.event_bus.publish(
            event_type="employee.updated",
            payload={
                "employee_id": employee_id,
                "updates": updates
            }
        )
        
        # Get updated employee data
        updated_employee = self.neural_fabric.get_node(employee_id)
        
        logger.info(f"Updated employee ID {employee_id} with {updates}")
        
        # Return updated info
        return {
            "employee_id": employee_id,
            "properties": updated_employee.properties
        }
    
    def terminate_employee(self,
                          employee_id: str,
                          termination_date: str,
                          reason: str,
                          voluntary: bool = True,
                          additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process employee termination.
        
        Args:
            employee_id: ID of the employee to terminate
            termination_date: Termination date (YYYY-MM-DD)
            reason: Reason for termination
            voluntary: Whether termination was voluntary
            additional_info: Additional termination details
            
        Returns:
            Termination details
        """
        # Get employee node
        employee_node = self.neural_fabric.get_node(employee_id)
        if not employee_node or employee_node.node_type != "employee":
            raise ValueError(f"Employee not found with ID: {employee_id}")
        
        # Ensure employee is active
        if employee_node.properties.get("status") != "active":
            raise ValueError(f"Cannot terminate employee with status: {employee_node.properties.get('status')}")
        
        # Parse termination date
        try:
            term_date_obj = datetime.strptime(termination_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid termination date format: {termination_date}. Expected YYYY-MM-DD")
        
        # Create termination record
        termination_properties = {
            "employee_id": employee_id,
            "termination_date": termination_date,
            "reason": reason,
            "voluntary": voluntary,
            "processed_at": datetime.now().isoformat()
        }
        
        # Add additional info
        if additional_info:
            for key, value in additional_info.items():
                if key not in termination_properties:
                    termination_properties[key] = value
        
        # Create termination node
        termination_id = self.neural_fabric.create_node(
            node_type="employee_termination",
            properties=termination_properties
        )
        
        # Connect termination to employee
        self.neural_fabric.connect_nodes(
            source_id=termination_id,
            target_id=employee_id,
            relation_type="terminates"
        )
        
        # Update employee status
        self.neural_fabric.update_node(
            node_id=employee_id,
            properties={
                "status": "terminated",
                "termination_date": termination_date,
                "termination_reason": reason,
                "termination_voluntary": voluntary
            }
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="employee.terminated",
            payload={
                "employee_id": employee_id,
                "termination_id": termination_id,
                "termination_date": termination_date,
                "voluntary": voluntary,
                "employee_name": f"{employee_node.properties.get('first_name')} {employee_node.properties.get('last_name')}"
            }
        )
        
        logger.info(f"Terminated employee ID {employee_id} effective {termination_date}")
        
        # Return termination details
        return {
            "employee_id": employee_id,
            "termination_id": termination_id,
            "termination_date": termination_date,
            "reason": reason,
            "voluntary": voluntary,
            "status": "processed"
        }
    
    def process_promotion(self,
                         employee_id: str,
                         new_position: str,
                         effective_date: str,
                         salary_change: Optional[float] = None,
                         new_manager_id: Optional[str] = None,
                         new_department: Optional[str] = None,
                         additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process an employee promotion.
        
        Args:
            employee_id: ID of the employee to promote
            new_position: New job position/title
            effective_date: Effective date (YYYY-MM-DD)
            salary_change: New salary or amount of increase
            new_manager_id: ID of new manager
            new_department: New department if changing
            additional_info: Additional promotion details
            
        Returns:
            Promotion details
        """
        # Get employee node
        employee_node = self.neural_fabric.get_node(employee_id)
        if not employee_node or employee_node.node_type != "employee":
            raise ValueError(f"Employee not found with ID: {employee_id}")
        
        # Ensure employee is active
        if employee_node.properties.get("status") != "active":
            raise ValueError(f"Cannot promote employee with status: {employee_node.properties.get('status')}")
        
        # Parse effective date
        try:
            effective_date_obj = datetime.strptime(effective_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid effective date format: {effective_date}. Expected YYYY-MM-DD")
        
        # Create promotion record
        promotion_properties = {
            "employee_id": employee_id,
            "previous_position": employee_node.properties.get("position"),
            "new_position": new_position,
            "effective_date": effective_date,
            "processed_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        if salary_change is not None:
            promotion_properties["salary_change"] = salary_change
            
            # Calculate new salary if the current one exists
            current_salary = employee_node.properties.get("salary")
            if current_salary is not None:
                if salary_change > 0 and salary_change < current_salary * 0.5:
                    # Assume this is an increase amount, not new total
                    promotion_properties["previous_salary"] = current_salary
                    promotion_properties["new_salary"] = current_salary + salary_change
                else:
                    # Assume this is the new total salary
                    promotion_properties["previous_salary"] = current_salary
                    promotion_properties["new_salary"] = salary_change
        
        if new_manager_id is not None:
            promotion_properties["new_manager_id"] = new_manager_id
            
        if new_department is not None:
            promotion_properties["new_department"] = new_department
            promotion_properties["previous_department"] = employee_node.properties.get("department")
        
        # Add additional info
        if additional_info:
            for key, value in additional_info.items():
                if key not in promotion_properties:
                    promotion_properties[key] = value
        
        # Create promotion node
        promotion_id = self.neural_fabric.create_node(
            node_type="employee_promotion",
            properties=promotion_properties
        )
        
        # Connect promotion to employee
        self.neural_fabric.connect_nodes(
            source_id=promotion_id,
            target_id=employee_id,
            relation_type="promotes"
        )
        
        # Update employee record
        updates = {
            "position": new_position,
            "previous_position": employee_node.properties.get("position"),
            "last_promotion_date": effective_date
        }
        
        # Update salary if provided
        if "new_salary" in promotion_properties:
            updates["salary"] = promotion_properties["new_salary"]
            updates["previous_salary"] = promotion_properties["previous_salary"]
        
        # Update department if provided
        if new_department:
            updates["department"] = new_department
            updates["previous_department"] = employee_node.properties.get("department")
        
        # Update employee node
        self.neural_fabric.update_node(
            node_id=employee_id,
            properties=updates
        )
        
        # Update manager if provided
        if new_manager_id:
            self.update_employee(
                employee_id=employee_id,
                updates={"manager_id": new_manager_id}
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="employee.promoted",
            payload={
                "employee_id": employee_id,
                "promotion_id": promotion_id,
                "new_position": new_position,
                "effective_date": effective_date,
                "employee_name": f"{employee_node.properties.get('first_name')} {employee_node.properties.get('last_name')}"
            }
        )
        
        logger.info(f"Processed promotion for employee ID {employee_id} to {new_position}")
        
        # Return promotion details
        return {
            "employee_id": employee_id,
            "promotion_id": promotion_id,
            "previous_position": employee_node.properties.get("position"),
            "new_position": new_position,
            "effective_date": effective_date,
            "status": "processed"
        }
    
    def manage_benefits(self,
                       employee_id: str,
                       action: str,
                       benefit_type: str,
                       details: Dict[str, Any]) -> Dict[str, Any]:
        """Manage employee benefits.
        
        Args:
            employee_id: Employee ID
            action: Action to perform (enroll, change, terminate)
            benefit_type: Type of benefit (health, dental, 401k, etc.)
            details: Benefit details
            
        Returns:
            Result of benefit action
        """
        # Get employee node
        employee_node = self.neural_fabric.get_node(employee_id)
        if not employee_node or employee_node.node_type != "employee":
            raise ValueError(f"Employee not found with ID: {employee_id}")
        
        # Ensure employee is active for enrollments
        if action == "enroll" and employee_node.properties.get("status") != "active":
            raise ValueError(f"Cannot enroll inactive employee with status: {employee_node.properties.get('status')}")
        
        # Prepare benefit record
        benefit_properties = {
            "employee_id": employee_id,
            "benefit_type": benefit_type,
            "action": action,
            "processed_at": datetime.now().isoformat()
        }
        
        # Add details
        for key, value in details.items():
            benefit_properties[key] = value
        
        # Create benefit action node
        benefit_id = self.neural_fabric.create_node(
            node_type="employee_benefit",
            properties=benefit_properties
        )
        
        # Connect benefit to employee
        self.neural_fabric.connect_nodes(
            source_id=benefit_id,
            target_id=employee_id,
            relation_type="benefits"
        )
        
        # Update employee's benefits summary
        benefits_summary = employee_node.properties.get("benefits_summary", {})
        
        if action == "enroll":
            if "enrolled_benefits" not in benefits_summary:
                benefits_summary["enrolled_benefits"] = []
            
            benefits_summary["enrolled_benefits"].append({
                "benefit_type": benefit_type,
                "enrollment_date": details.get("effective_date", datetime.now().isoformat()),
                "details": details
            })
            
        elif action == "change":
            if "enrolled_benefits" in benefits_summary:
                # Find and update the existing benefit
                for benefit in benefits_summary["enrolled_benefits"]:
                    if benefit["benefit_type"] == benefit_type:
                        benefit["details"].update(details)
                        benefit["last_updated"] = datetime.now().isoformat()
                        break
        
        elif action == "terminate":
            if "enrolled_benefits" in benefits_summary:
                # Move from enrolled to terminated
                for i, benefit in enumerate(benefits_summary["enrolled_benefits"]):
                    if benefit["benefit_type"] == benefit_type:
                        if "terminated_benefits" not in benefits_summary:
                            benefits_summary["terminated_benefits"] = []
                        
                        terminated_benefit = benefit.copy()
                        terminated_benefit["termination_date"] = details.get("effective_date", datetime.now().isoformat())
                        terminated_benefit["termination_reason"] = details.get("reason", "Not specified")
                        
                        benefits_summary["terminated_benefits"].append(terminated_benefit)
                        benefits_summary["enrolled_benefits"].pop(i)
                        break
        
        # Update employee node with benefits summary
        self.neural_fabric.update_node(
            node_id=employee_id,
            properties={"benefits_summary": benefits_summary}
        )
        
        # Publish event
        self.event_bus.publish(
            event_type=f"employee.benefit.{action}ed",
            payload={
                "employee_id": employee_id,
                "benefit_id": benefit_id,
                "benefit_type": benefit_type,
                "action": action,
                "employee_name": f"{employee_node.properties.get('first_name')} {employee_node.properties.get('last_name')}"
            }
        )
        
        logger.info(f"Processed benefit {action} for employee ID {employee_id}: {benefit_type}")
        
        # Return benefit action details
        return {
            "employee_id": employee_id,
            "benefit_id": benefit_id,
            "benefit_type": benefit_type,
            "action": action,
            "details": details,
            "status": "processed"
        }
    
    def track_performance(self,
                         employee_id: str,
                         review_type: str,
                         review_date: str,
                         ratings: Dict[str, float],
                         comments: Optional[str] = None,
                         goals: Optional[List[Dict[str, Any]]] = None,
                         reviewer_id: Optional[str] = None) -> Dict[str, Any]:
        """Track employee performance reviews.
        
        Args:
            employee_id: Employee ID
            review_type: Type of review (annual, quarterly, etc.)
            review_date: Date of review (YYYY-MM-DD)
            ratings: Performance ratings by category
            comments: Review comments
            goals: New or updated goals
            reviewer_id: ID of the reviewer
            
        Returns:
            Performance review details
        """
        # Get employee node
        employee_node = self.neural_fabric.get_node(employee_id)
        if not employee_node or employee_node.node_type != "employee":
            raise ValueError(f"Employee not found with ID: {employee_id}")
        
        # Parse review date
        try:
            review_date_obj = datetime.strptime(review_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid review date format: {review_date}. Expected YYYY-MM-DD")
        
        # Calculate average rating
        if ratings:
            avg_rating = sum(ratings.values()) / len(ratings)
        else:
            avg_rating = None
        
        # Create performance review record
        review_properties = {
            "employee_id": employee_id,
            "review_type": review_type,
            "review_date": review_date,
            "ratings": ratings,
            "average_rating": avg_rating,
            "processed_at": datetime.now().isoformat()
        }
        
        if comments:
            review_properties["comments"] = comments
            
        if goals:
            review_properties["goals"] = goals
            
        if reviewer_id:
            review_properties["reviewer_id"] = reviewer_id
            
            # Get reviewer name if available
            reviewer_node = self.neural_fabric.get_node(reviewer_id)
            if reviewer_node and reviewer_node.node_type == "employee":
                reviewer_name = f"{reviewer_node.properties.get('first_name')} {reviewer_node.properties.get('last_name')}"
                review_properties["reviewer_name"] = reviewer_name
        
        # Create performance review node
        review_id = self.neural_fabric.create_node(
            node_type="performance_review",
            properties=review_properties
        )
        
        # Connect review to employee
        self.neural_fabric.connect_nodes(
            source_id=review_id,
            target_id=employee_id,
            relation_type="reviews"
        )
        
        # Connect review to reviewer if specified
        if reviewer_id:
            self.neural_fabric.connect_nodes(
                source_id=review_id,
                target_id=reviewer_id,
                relation_type="reviewed_by"
            )
        
        # Update employee's performance history
        performance_history = employee_node.properties.get("performance_history", {})
        
        if "reviews" not in performance_history:
            performance_history["reviews"] = []
            
        performance_history["reviews"].append({
            "review_id": review_id,
            "review_type": review_type,
            "review_date": review_date,
            "average_rating": avg_rating
        })
        
        # Update latest goals if provided
        if goals:
            performance_history["current_goals"] = goals
        
        # Calculate performance trends
        if len(performance_history["reviews"]) > 1:
            reviews = sorted(performance_history["reviews"], key=lambda x: x["review_date"])
            ratings_trend = [r.get("average_rating") for r in reviews if r.get("average_rating") is not None]
            
            if len(ratings_trend) >= 2:
                performance_history["trend"] = {
                    "direction": "improving" if ratings_trend[-1] > ratings_trend[-2] else "declining",
                    "change": ratings_trend[-1] - ratings_trend[-2]
                }
        
        # Update employee node with performance history
        self.neural_fabric.update_node(
            node_id=employee_id,
            properties={"performance_history": performance_history}
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="employee.review.completed",
            payload={
                "employee_id": employee_id,
                "review_id": review_id,
                "review_type": review_type,
                "average_rating": avg_rating,
                "employee_name": f"{employee_node.properties.get('first_name')} {employee_node.properties.get('last_name')}"
            }
        )
        
        logger.info(f"Processed {review_type} review for employee ID {employee_id}")
        
        # Return review details
        return {
            "employee_id": employee_id,
            "review_id": review_id,
            "review_type": review_type,
            "review_date": review_date,
            "average_rating": avg_rating,
            "status": "processed"
        }
    
    def analyze_workforce(self,
                         filters: Optional[Dict[str, Any]] = None,
                         metrics: Optional[List[str]] = None,
                         group_by: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze workforce data.
        
        Args:
            filters: Criteria to filter employees
            metrics: Metrics to calculate
            group_by: Fields to group results by
            
        Returns:
            Analysis results
        """
        # Set default parameters
        if metrics is None:
            metrics = ["headcount", "average_salary", "average_tenure"]
            
        if group_by is None:
            group_by = ["department"]
        
        # Query employees based on filters
        employee_nodes = self.neural_fabric.query_nodes(
            node_type="employee",
            filters=filters,
            limit=1000  # Use a reasonable limit
        )
        
        if not employee_nodes:
            return {
                "count": 0,
                "message": "No employees match the criteria"
            }
        
        # Group employees according to group_by fields
        grouped_data = {}
        
        # Create a nested dictionary structure based on group_by fields
        for employee in employee_nodes:
            # Build the path through the nested dictionary
            current_dict = grouped_data
            group_key_values = []
            
            for group_field in group_by:
                group_value = employee.properties.get(group_field, "Unknown")
                group_key_values.append(group_value)
                
                # Create path in nested dictionary
                if group_value not in current_dict:
                    if group_field == group_by[-1]:  # Last level
                        current_dict[group_value] = []
                    else:
                        current_dict[group_value] = {}
                
                if group_field == group_by[-1]:
                    current_dict[group_value].append(employee)
                else:
                    current_dict = current_dict[group_value]
        
        # Calculate metrics for each group
        results = {
            "total_employees": len(employee_nodes),
            "groups": {},
            "metrics": {}
        }
        
        def calculate_metrics(employees, metrics_list):
            """Calculate requested metrics for a list of employees."""
            result = {}
            
            if "headcount" in metrics_list:
                result["headcount"] = len(employees)
                
            if "average_salary" in metrics_list:
                salaries = [e.properties.get("salary") for e in employees if e.properties.get("salary") is not None]
                result["average_salary"] = sum(salaries) / len(salaries) if salaries else None
                
            if "average_tenure" in metrics_list:
                today = date.today()
                tenures = []
                for e in employees:
                    hire_date_str = e.properties.get("hire_date")
                    if hire_date_str:
                        try:
                            hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
                            tenure_days = (today - hire_date).days
                            tenures.append(tenure_days / 365.0)  # Convert to years
                        except (ValueError, TypeError):
                            pass
                
                result["average_tenure"] = sum(tenures) / len(tenures) if tenures else None
                
            if "turnover_rate" in metrics_list:
                # Calculate turnover based on terminations in the last year
                one_year_ago = (today - datetime.timedelta(days=365)).isoformat()
                
                active_count = sum(1 for e in employees if e.properties.get("status") == "active")
                terminated_count = sum(1 for e in employees 
                                     if e.properties.get("status") == "terminated" 
                                     and e.properties.get("termination_date", "0") >= one_year_ago)
                
                if active_count + terminated_count > 0:
                    result["turnover_rate"] = (terminated_count / (active_count + terminated_count)) * 100
                else:
                    result["turnover_rate"] = 0
                    
            if "gender_diversity" in metrics_list:
                genders = {}
                for e in employees:
                    gender = e.properties.get("gender", "Not Specified")
                    genders[gender] = genders.get(gender, 0) + 1
                
                result["gender_diversity"] = {
                    gender: (count / len(employees)) * 100
                    for gender, count in genders.items()
                }
                
            if "performance_distribution" in metrics_list:
                ratings = []
                for e in employees:
                    history = e.properties.get("performance_history", {})
                    reviews = history.get("reviews", [])
                    if reviews:
                        latest_review = max(reviews, key=lambda r: r.get("review_date", "0"))
                        if "average_rating" in latest_review:
                            ratings.append(latest_review["average_rating"])
                
                if ratings:
                    # Create distribution buckets
                    distribution = {"excellent": 0, "good": 0, "average": 0, "needs_improvement": 0, "poor": 0}
                    
                    for rating in ratings:
                        if rating >= 4.5:
                            distribution["excellent"] += 1
                        elif rating >= 3.5:
                            distribution["good"] += 1
                        elif rating >= 2.5:
                            distribution["average"] += 1
                        elif rating >= 1.5:
                            distribution["needs_improvement"] += 1
                        else:
                            distribution["poor"] += 1
                    
                    # Convert to percentages
                    result["performance_distribution"] = {
                        category: (count / len(ratings)) * 100
                        for category, count in distribution.items()
                    }
                else:
                    result["performance_distribution"] = None
            
            return result
        
        # Calculate overall metrics
        results["metrics"] = calculate_metrics(employee_nodes, metrics)
        
        # Process the grouped data recursively
        def process_groups(data, path=None):
            if path is None:
                path = []
                
            result = {}
            
            for key, value in data.items():
                current_path = path + [key]
                
                if isinstance(value, list):  # Leaf node with employees
                    result[key] = {
                        "metrics": calculate_metrics(value, metrics),
                        "path": current_path
                    }
                else:  # Nested group
                    result[key] = process_groups(value, current_path)
            
            return result
        
        results["groups"] = process_groups(grouped_data)
        
        # Calculate AI-driven insights based on the data
        insights = []
        
        # Simple insights based on department headcount distribution
        if "department" in group_by and "headcount" in metrics:
            departments = []
            for dept, data in results["groups"].items():
                if isinstance(data, dict) and "metrics" in data:
                    departments.append((dept, data["metrics"]["headcount"]))
                
            if departments:
                # Find largest and smallest departments
                departments.sort(key=lambda x: x[1], reverse=True)
                largest_dept, largest_count = departments[0]
                smallest_dept, smallest_count = departments[-1]
                
                # Calculate headcount concentration
                total = sum(count for _, count in departments)
                concentration = (largest_count / total) * 100
                
                if concentration > 50:
                    insights.append(f"Workforce concentration: {largest_dept} department represents {concentration:.1f}% of total headcount")
                
                if largest_count > smallest_count * 5:
                    insights.append(f"Department size disparity: {largest_dept} is {largest_count/smallest_count:.1f}x larger than {smallest_dept}")
        
        # Check for salary disparities between departments
        if "department" in group_by and "average_salary" in metrics:
            dept_salaries = []
            for dept, data in results["groups"].items():
                if isinstance(data, dict) and "metrics" in data:
                    salary = data["metrics"].get("average_salary")
                    if salary is not None:
                        dept_salaries.append((dept, salary))
            
            if len(dept_salaries) >= 2:
                dept_salaries.sort(key=lambda x: x[1], reverse=True)
                highest_dept, highest_salary = dept_salaries[0]
                lowest_dept, lowest_salary = dept_salaries[-1]
                
                salary_gap = ((highest_salary - lowest_salary) / lowest_salary) * 100
                if salary_gap > 30:
                    insights.append(f"Salary disparity: {highest_dept} has {salary_gap:.1f}% higher average salary than {lowest_dept}")
        
        # Add insights to results
        if insights:
            results["insights"] = insights
        
        logger.info(f"Completed workforce analysis with {len(employee_nodes)} employees")
        return results
    
    def generate_hr_documents(self,
                            document_type: str,
                            employee_id: Optional[str] = None,
                            template_id: Optional[str] = None,
                            data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate HR documents using templates and AI.
        
        Args:
            document_type: Type of document to generate
            employee_id: Optional employee ID for personalized documents
            template_id: Optional template ID to use
            data: Additional data for document generation
            
        Returns:
            Generated document information
        """
        if not self.ai_engine:
            raise ValueError("AI engine is required for document generation")
        
        # Initialize document data
        document_data = data.copy() if data else {}
        
        # Add employee data if provided
        if employee_id:
            employee_node = self.neural_fabric.get_node(employee_id)
            if not employee_node or employee_node.node_type != "employee":
                raise ValueError(f"Employee not found with ID: {employee_id}")
            
            # Add employee properties to document data
            document_data["employee"] = employee_node.properties
            
            # Add manager information if available
            connections = self.neural_fabric.get_connected_nodes(
                node_id=employee_id,
                relation_type="reports_to"
            )
            
            if "reports_to" in connections and connections["reports_to"]:
                manager_node = connections["reports_to"][0]
                document_data["manager"] = manager_node.properties
        
        # Fetch template if provided
        template_content = None
        if template_id:
            template_node = self.neural_fabric.get_node(template_id)
            if template_node and template_node.node_type == "document_template":
                template_content = template_node.properties.get("content")
                document_data["template_name"] = template_node.properties.get("name")
        
        # Build prompt for document generation
        prompt = f"Generate a {document_type} document"
        
        if employee_id:
            prompt += f" for employee {document_data['employee'].get('full_name')}"
            
        if template_content:
            prompt += f" using the following template:\n\n{template_content}\n\n"
        
        prompt += "\nUse the following data for document generation:\n"
        prompt += json.dumps(document_data, indent=2)
        
        # Generate document content using AI
        document_content = self.ai_engine.get_agent_response(
            agent_type="hr",
            prompt=prompt,
            context={"document_type": document_type}
        )
        
        # Create document node
        document_properties = {
            "document_type": document_type,
            "content": document_content,
            "created_at": datetime.now().isoformat(),
            "generated_by": self.name
        }
        
        if employee_id:
            document_properties["employee_id"] = employee_id
            
        if template_id:
            document_properties["template_id"] = template_id
        
        # Create document node
        document_id = self.neural_fabric.create_node(
            node_type="hr_document",
            properties=document_properties
        )
        
        # Connect document to employee if specified
        if employee_id:
            self.neural_fabric.connect_nodes(
                source_id=document_id,
                target_id=employee_id,
                relation_type="documents"
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="document.generated",
            payload={
                "document_id": document_id,
                "document_type": document_type,
                "employee_id": employee_id
            }
        )
        
        logger.info(f"Generated {document_type} document (ID: {document_id})")
        
        # Return document information
        return {
            "document_id": document_id,
            "document_type": document_type,
            "employee_id": employee_id,
            "content": document_content
        }
    
    def handle_pto_request(self,
                          employee_id: str,
                          start_date: str,
                          end_date: str,
                          pto_type: str,
                          reason: Optional[str] = None,
                          manager_approval_required: bool = True) -> Dict[str, Any]:
        """Process paid time off (PTO) requests.
        
        Args:
            employee_id: Employee ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            pto_type: Type of PTO (vacation, sick, personal, etc.)
            reason: Optional reason for the request
            manager_approval_required: Whether manager approval is required
            
        Returns:
            PTO request details
        """
        # Get employee node
        employee_node = self.neural_fabric.get_node(employee_id)
        if not employee_node or employee_node.node_type != "employee":
            raise ValueError(f"Employee not found with ID: {employee_id}")
        
        # Ensure employee is active
        if employee_node.properties.get("status") != "active":
            raise ValueError(f"Cannot process PTO for inactive employee with status: {employee_node.properties.get('status')}")
        
        # Parse dates
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD")
        
        # Calculate number of days
        days_requested = (end_date_obj - start_date_obj).days + 1
        
        # Create PTO request record
        pto_properties = {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "days_requested": days_requested,
            "pto_type": pto_type,
            "status": "pending" if manager_approval_required else "approved",
            "submitted_at": datetime.now().isoformat()
        }
        
        if reason:
            pto_properties["reason"] = reason
        
        # Create PTO request node
        pto_id = self.neural_fabric.create_node(
            node_type="pto_request",
            properties=pto_properties
        )
        
        # Connect PTO request to employee
        self.neural_fabric.connect_nodes(
            source_id=pto_id,
            target_id=employee_id,
            relation_type="requested_by"
        )
        
        # Get manager for approval routing
        if manager_approval_required:
            connections = self.neural_fabric.get_connected_nodes(
                node_id=employee_id,
                relation_type="reports_to"
            )
            
            if "reports_to" in connections and connections["reports_to"]:
                manager_node = connections["reports_to"][0]
                
                # Connect PTO request to manager
                self.neural_fabric.connect_nodes(
                    source_id=pto_id,
                    target_id=manager_node.id,
                    relation_type="pending_approval_from"
                )
                
                pto_properties["manager_id"] = manager_node.id
        
        # Update employee's PTO records
        pto_records = employee_node.properties.get("pto_records", {})
        
        if "requests" not in pto_records:
            pto_records["requests"] = []
            
        pto_records["requests"].append({
            "pto_id": pto_id,
            "start_date": start_date,
            "end_date": end_date,
            "days": days_requested,
            "type": pto_type,
            "status": pto_properties["status"]
        })
        
        # Update balances if automatically approved
        if not manager_approval_required:
            if "balances" not in pto_records:
                pto_records["balances"] = {}
                
            if pto_type not in pto_records["balances"]:
                # Initialize with default balance if not present
                pto_records["balances"][pto_type] = 0
                
            # Deduct days from balance
            pto_records["balances"][pto_type] -= days_requested
        
        # Update employee node with PTO records
        self.neural_fabric.update_node(
            node_id=employee_id,
            properties={"pto_records": pto_records}
        )
        
        # Publish event
        event_type = "pto.requested" if manager_approval_required else "pto.approved"
        self.event_bus.publish(
            event_type=event_type,
            payload={
                "employee_id": employee_id,
                "pto_id": pto_id,
                "start_date": start_date,
                "end_date": end_date,
                "days": days_requested,
                "pto_type": pto_type,
                "employee_name": f"{employee_node.properties.get('first_name')} {employee_node.properties.get('last_name')}"
            }
        )
        
        logger.info(f"Processed PTO request for employee ID {employee_id}: {days_requested} days of {pto_type}")
        
        # Return PTO request details
        return {
            "employee_id": employee_id,
            "pto_id": pto_id,
            "start_date": start_date,
            "end_date": end_date,
            "days_requested": days_requested,
            "pto_type": pto_type,
            "status": pto_properties["status"],
            "requires_approval": manager_approval_required
        }
    
    # Event handlers
    def _handle_onboarding(self, event):
        """Handle employee onboarding events."""
        employee_id = event.payload.get("employee_id")
        if not employee_id:
            return
            
        logger.info(f"Handling onboarding for employee ID {employee_id}")
        
        # Generate onboarding documents
        self.generate_hr_documents(
            document_type="onboarding_checklist",
            employee_id=employee_id
        )
        
        # TODO: Add more onboarding automation
    
    def _handle_offboarding(self, event):
        """Handle employee offboarding events."""
        employee_id = event.payload.get("employee_id")
        if not employee_id:
            return
            
        logger.info(f"Handling offboarding for employee ID {employee_id}")
        
        # Generate offboarding documents
        self.generate_hr_documents(
            document_type="offboarding_checklist",
            employee_id=employee_id
        )
        
        # TODO: Add more offboarding automation
    
    def _handle_promotion(self, event):
        """Handle employee promotion events."""
        employee_id = event.payload.get("employee_id")
        if not employee_id:
            return
            
        logger.info(f"Handling promotion for employee ID {employee_id}")
        
        # Generate promotion letter
        self.generate_hr_documents(
            document_type="promotion_letter",
            employee_id=employee_id
        )
    
    def _handle_review(self, event):
        """Handle employee review events."""
        employee_id = event.payload.get("employee_id")
        if not employee_id:
            return
            
        logger.info(f"Handling review completion for employee ID {employee_id}")
        
        # Generate performance summary
        self.generate_hr_documents(
            document_type="performance_summary",
            employee_id=employee_id
        )
    
    def _handle_pto_request(self, event):
        """Handle PTO request events."""
        employee_id = event.payload.get("employee_id")
        if not employee_id:
            return
            
        logger.info(f"Handling PTO request for employee ID {employee_id}")
        
        # Extract additional information from the event payload
        pto_id = event.payload.get("pto_id")
        pto_type = event.payload.get("pto_type")
        start_date = event.payload.get("start_date")
        end_date = event.payload.get("end_date")
        days = event.payload.get("days", 0)
        employee_name = event.payload.get("employee_name", "Unknown Employee")
        
        # Log detailed information about the PTO request
        logger.info(f"PTO request details: {employee_name}, {pto_type}, {days} days ({start_date} to {end_date})")
        
        # Check if this is a special PTO type that can be auto-approved
        auto_approve_types = ["sick", "bereavement"]
        
        if pto_type and pto_type.lower() in auto_approve_types:
            logger.info(f"Auto-approving {pto_type} PTO request for {employee_name}")
            
            # Update PTO request status
            self.neural_fabric.update_node(
                node_id=pto_id,
                properties={"status": "approved", "approved_at": datetime.now().isoformat()}
            )
            
            # Notify employee of auto-approval
            self.event_bus.publish(
                event_type="pto.approved",
                payload={
                    "employee_id": employee_id,
                    "pto_id": pto_id,
                    "pto_type": pto_type,
                    "auto_approved": True
                }
            )
            
            # Generate notification document
            self.generate_hr_documents(
                document_type="pto_approval",
                employee_id=employee_id,
                data={
                    "pto_type": pto_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days,
                    "auto_approved": True
                }
            )
        else:
            # For other PTO types, notify manager for approval
            # Get employee's manager
            connections = self.neural_fabric.get_connected_nodes(
                node_id=employee_id,
                relation_type="reports_to"
            )
            
            if "reports_to" in connections and connections["reports_to"]:
                manager_node = connections["reports_to"][0]
                manager_id = manager_node.id
                
                logger.info(f"Notifying manager (ID: {manager_id}) about PTO request")
                
                # Publish notification event for manager
                self.event_bus.publish(
                    event_type="notification.created",
                    payload={
                        "user_id": manager_id,
                        "type": "pto_approval_request",
                        "title": f"PTO Approval Request: {employee_name}",
                        "message": f"{employee_name} has requested {days} days of {pto_type} leave from {start_date} to {end_date}.",
                        "action_url": f"/pto/approve/{pto_id}",
                        "priority": "normal"
                    }
                )