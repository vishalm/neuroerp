"""
Employee Onboarding Workflow Template for AI-Native ERP System

This module defines an autonomous, self-optimizing workflow for employee onboarding
that coordinates multiple AI agents, adapts to different departments and roles,
and continuously improves based on feedback and outcomes.
"""

import datetime
from typing import Dict, List, Optional, Any

from orchestration.workflow_engine import Workflow, Task, Condition, AgentTask
from orchestration.task_scheduler import Priority


class OnboardingWorkflow(Workflow):
    """
    Adaptive employee onboarding workflow that coordinates HR, IT, Finance, and department-specific
    processes for seamless employee integration.
    """

    def __init__(
        self, 
        employee_id: str, 
        role: str, 
        department: str,
        start_date: datetime.date,
        manager_id: str,
        special_requirements: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the onboarding workflow with employee details.

        Args:
            employee_id: Unique identifier for the new employee
            role: Employee's job title/role
            department: Employee's department
            start_date: Employee's first day
            manager_id: ID of the employee's manager
            special_requirements: Any special equipment, access, or accommodations needed
        """
        super().__init__(
            workflow_id=f"onboarding-{employee_id}",
            name=f"Employee Onboarding - {employee_id}",
            description=f"Onboarding workflow for new {role} in {department}"
        )
        
        self.employee_id = employee_id
        self.role = role
        self.department = department
        self.start_date = start_date
        self.manager_id = manager_id
        self.special_requirements = special_requirements or {}
        
        # Workflow metadata for analytics and optimization
        self.metadata.update({
            "workflow_type": "onboarding",
            "employee_role": role,
            "employee_department": department,
            "time_to_start": (start_date - datetime.date.today()).days
        })
        
        # Define the onboarding workflow tasks and structure
        self._create_workflow_structure()
    
    def _create_workflow_structure(self):
        """Define the tasks, dependencies, and conditions for the onboarding workflow."""
        
        # Pre-onboarding phase (before employee starts)
        self.add_task(
            AgentTask(
                task_id="collect_employee_info",
                agent_type="hr",
                action="collect_employee_information",
                parameters={"employee_id": self.employee_id},
                priority=Priority.HIGH,
                estimated_duration=datetime.timedelta(hours=2)
            )
        )
        
        self.add_task(
            AgentTask(
                task_id="prepare_workstation",
                agent_type="it",
                action="provision_employee_workstation",
                parameters={
                    "employee_id": self.employee_id,
                    "role": self.role,
                    "special_requirements": self.special_requirements.get("equipment", {})
                },
                priority=Priority.HIGH,
                estimated_duration=datetime.timedelta(days=3)
            )
        )
        
        self.add_task(
            AgentTask(
                task_id="setup_accounts",
                agent_type="it",
                action="create_employee_accounts",
                parameters={
                    "employee_id": self.employee_id,
                    "department": self.department,
                    "role": self.role,
                    "manager_id": self.manager_id
                },
                priority=Priority.HIGH,
                estimated_duration=datetime.timedelta(hours=4),
                depends_on=["collect_employee_info"]
            )
        )
        
        self.add_task(
            AgentTask(
                task_id="prepare_paperwork",
                agent_type="hr",
                action="prepare_onboarding_documents",
                parameters={
                    "employee_id": self.employee_id,
                    "role": self.role,
                    "department": self.department,
                    "start_date": self.start_date.isoformat()
                },
                priority=Priority.MEDIUM,
                estimated_duration=datetime.timedelta(hours=3),
                depends_on=["collect_employee_info"]
            )
        )
        
        # Add department-specific onboarding tasks
        self._add_department_specific_tasks()
        
        # First day tasks
        self.add_task(
            AgentTask(
                task_id="first_day_schedule",
                agent_type="hr",
                action="create_first_day_schedule",
                parameters={
                    "employee_id": self.employee_id,
                    "department": self.department,
                    "manager_id": self.manager_id
                },
                priority=Priority.MEDIUM,
                estimated_duration=datetime.timedelta(hours=1),
                depends_on=["prepare_paperwork"]
            )
        )
        
        self.add_task(
            AgentTask(
                task_id="assign_mentor",
                agent_type="hr",
                action="assign_onboarding_mentor",
                parameters={
                    "employee_id": self.employee_id,
                    "department": self.department,
                    "role": self.role
                },
                priority=Priority.MEDIUM,
                estimated_duration=datetime.timedelta(hours=1),
                depends_on=["collect_employee_info"]
            )
        )
        
        # Post first-day tasks
        self.add_task(
            AgentTask(
                task_id="training_plan",
                agent_type="hr",
                action="create_training_plan",
                parameters={
                    "employee_id": self.employee_id,
                    "role": self.role,
                    "department": self.department
                },
                priority=Priority.MEDIUM,
                estimated_duration=datetime.timedelta(hours=3),
                depends_on=["first_day_schedule"]
            )
        )
        
        self.add_task(
            AgentTask(
                task_id="30_day_check_in",
                agent_type="hr",
                action="schedule_check_in",
                parameters={
                    "employee_id": self.employee_id,
                    "manager_id": self.manager_id,
                    "days_after_start": 30,
                    "check_in_type": "30_day_review"
                },
                priority=Priority.LOW,
                estimated_duration=datetime.timedelta(hours=1),
                depends_on=["first_day_schedule"],
                scheduled_time=self.start_date + datetime.timedelta(days=25)
            )
        )
        
        self.add_task(
            AgentTask(
                task_id="90_day_review_prep",
                agent_type="hr",
                action="prepare_performance_review",
                parameters={
                    "employee_id": self.employee_id,
                    "manager_id": self.manager_id,
                    "review_type": "90_day",
                    "role": self.role
                },
                priority=Priority.LOW,
                estimated_duration=datetime.timedelta(hours=2),
                depends_on=["30_day_check_in"],
                scheduled_time=self.start_date + datetime.timedelta(days=80)
            )
        )
        
        # Set up feedback collection for workflow optimization
        self.add_task(
            AgentTask(
                task_id="collect_onboarding_feedback",
                agent_type="hr",
                action="send_onboarding_survey",
                parameters={
                    "employee_id": self.employee_id,
                    "survey_type": "onboarding_experience"
                },
                priority=Priority.LOW,
                estimated_duration=datetime.timedelta(hours=1),
                depends_on=["training_plan"],
                scheduled_time=self.start_date + datetime.timedelta(days=14)
            )
        )
    
    def _add_department_specific_tasks(self):
        """Add tasks specific to the employee's department."""
        
        # Engineering department
        if self.department.lower() in ["engineering", "development", "it", "product"]:
            self.add_task(
                AgentTask(
                    task_id="dev_environment_setup",
                    agent_type="it",
                    action="setup_development_environment",
                    parameters={
                        "employee_id": self.employee_id,
                        "role": self.role,
                        "tech_stack": self.special_requirements.get("tech_stack", [])
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=4),
                    depends_on=["setup_accounts"]
                )
            )
            
            self.add_task(
                AgentTask(
                    task_id="code_access",
                    agent_type="it",
                    action="grant_repository_access",
                    parameters={
                        "employee_id": self.employee_id,
                        "role": self.role,
                        "team": self.special_requirements.get("team", "")
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=1),
                    depends_on=["setup_accounts"]
                )
            )
        
        # Sales department
        elif self.department.lower() in ["sales", "business development"]:
            self.add_task(
                AgentTask(
                    task_id="crm_access",
                    agent_type="it",
                    action="setup_crm_account",
                    parameters={
                        "employee_id": self.employee_id,
                        "role": self.role,
                        "territory": self.special_requirements.get("territory", "")
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=2),
                    depends_on=["setup_accounts"]
                )
            )
            
            self.add_task(
                AgentTask(
                    task_id="sales_materials",
                    agent_type="sales",
                    action="prepare_sales_materials",
                    parameters={
                        "employee_id": self.employee_id,
                        "products": self.special_requirements.get("products", [])
                    },
                    priority=Priority.MEDIUM,
                    estimated_duration=datetime.timedelta(hours=3),
                    depends_on=["collect_employee_info"]
                )
            )
        
        # Finance department
        elif self.department.lower() in ["finance", "accounting"]:
            self.add_task(
                AgentTask(
                    task_id="financial_systems_access",
                    agent_type="it",
                    action="grant_financial_systems_access",
                    parameters={
                        "employee_id": self.employee_id,
                        "role": self.role,
                        "access_level": self.special_requirements.get("access_level", "standard")
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=2),
                    depends_on=["setup_accounts"]
                )
            )
            
            self.add_task(
                AgentTask(
                    task_id="compliance_training",
                    agent_type="finance",
                    action="schedule_compliance_training",
                    parameters={
                        "employee_id": self.employee_id,
                        "training_modules": ["financial_ethics", "data_security", "regulatory_compliance"]
                    },
                    priority=Priority.HIGH,
                    estimated_duration=datetime.timedelta(hours=1),
                    depends_on=["collect_employee_info"]
                )
            )
    
    def on_task_completed(self, task_id: str, result: Dict[str, Any]):
        """Handle task completion events and adapt workflow if needed."""
        super().on_task_completed(task_id, result)
        
        # Example of dynamic workflow adjustment
        if task_id == "collect_employee_info":
            # If employee has accessibility requirements, add additional setup task
            if result.get("accessibility_requirements"):
                self.add_task(
                    AgentTask(
                        task_id="accessibility_setup",
                        agent_type="it",
                        action="configure_accessibility_tools",
                        parameters={
                            "employee_id": self.employee_id,
                            "requirements": result.get("accessibility_requirements")
                        },
                        priority=Priority.HIGH,
                        estimated_duration=datetime.timedelta(hours=3),
                        depends_on=["prepare_workstation"]
                    )
                )
        
        # Update workflow metrics for optimization
        if task_id == "collect_onboarding_feedback":
            satisfaction_score = result.get("satisfaction_score", 0)
            self.metadata["satisfaction_score"] = satisfaction_score
            
            # Suggest workflow improvements based on feedback
            if satisfaction_score < 7:
                improvement_areas = result.get("improvement_areas", [])
                self.add_task(
                    AgentTask(
                        task_id="workflow_improvement",
                        agent_type="process_optimization",
                        action="suggest_workflow_improvements",
                        parameters={
                            "workflow_id": self.workflow_id,
                            "feedback": result,
                            "improvement_areas": improvement_areas
                        },
                        priority=Priority.LOW,
                        estimated_duration=datetime.timedelta(hours=2)
                    )
                )
    
    def on_error(self, task_id: str, error: Exception):
        """Handle task failures and implement recovery strategies."""
        super().on_error(task_id, error)
        
        # Example error recovery
        if task_id == "prepare_workstation":
            # Add an alternative task to provide temporary equipment
            self.add_task(
                AgentTask(
                    task_id="temporary_equipment",
                    agent_type="it",
                    action="arrange_temporary_equipment",
                    parameters={
                        "employee_id": self.employee_id,
                        "original_error": str(error)
                    },
                    priority=Priority.CRITICAL,
                    estimated_duration=datetime.timedelta(hours=2)
                )
            )
            
            # Reschedule the original task with higher priority
            self.reschedule_task(
                task_id="prepare_workstation",
                new_priority=Priority.CRITICAL,
                delay=datetime.timedelta(days=1)
            )