"""
Integration Tests for Workflow Components

This module tests the integration between workflow engine, task scheduler,
and business process templates in the AI-native ERP system.
"""

import unittest
import datetime
import uuid
import json
import os
import sys
import time
from typing import Dict, List, Any
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import system components
from orchestration.workflow_engine import Workflow, Task, AgentTask, TaskStatus
from orchestration.task_scheduler import TaskScheduler, Priority
from orchestration.workflow_templates.onboarding import OnboardingWorkflow
from orchestration.workflow_templates.procurement import ProcurementWorkflow
from security.identity import IdentityManager
from security.compliance import ComplianceMonitor


class TestWorkflowIntegration(unittest.TestCase):
    """Test integration between workflow engine and task scheduler components."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a task scheduler for testing
        self.scheduler = TaskScheduler()
        
        # Create test workflow
        self.workflow = Workflow(
            workflow_id="test-workflow",
            name="Test Workflow",
            description="Test workflow for integration testing"
        )
        self.workflow.register_scheduler(self.scheduler)
    
    def test_task_scheduling_execution(self):
        """Test basic task scheduling and execution."""
        # Create a simple task
        task_executed = False
        
        def task_action():
            nonlocal task_executed
            task_executed = True
            return {"status": "success"}
        
        self.workflow.add_task(
            Task(
                task_id="test-task",
                action=task_action,
                priority=Priority.MEDIUM,
                estimated_duration=datetime.timedelta(seconds=1)
            )
        )
        
        # Start the workflow
        self.workflow.start()
        
        # Allow time for execution
        time.sleep(0.1)
        
        # Check if task was executed
        self.assertTrue(task_executed)
        
        # Verify task status
        task = self.workflow.get_task("test-task")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
    
    def test_task_dependencies(self):
        """Test execution of tasks with dependencies."""
        # Track execution order
        execution_order = []
        
        # Task functions
        def task1_action():
            execution_order.append("task1")
            return {"status": "success"}
        
        def task2_action():
            execution_order.append("task2")
            return {"status": "success"}
        
        def task3_action():
            execution_order.append("task3")
            return {"status": "success"}
        
        # Add tasks with dependencies
        self.workflow.add_task(
            Task(
                task_id="task1",
                action=task1_action,
                priority=Priority.MEDIUM
            )
        )
        
        self.workflow.add_task(
            Task(
                task_id="task2",
                action=task2_action,
                priority=Priority.HIGH,
                depends_on=["task1"]
            )
        )
        
        self.workflow.add_task(
            Task(
                task_id="task3",
                action=task3_action,
                priority=Priority.LOW,
                depends_on=["task2"]
            )
        )
        
        # Start the workflow
        self.workflow.start()
        
        # Allow time for execution
        time.sleep(0.2)
        
        # Verify execution order
        self.assertEqual(execution_order, ["task1", "task2", "task3"])
        
        # Verify all tasks completed
        self.assertEqual(self.workflow.get_task("task1").status, TaskStatus.COMPLETED)
        self.assertEqual(self.workflow.get_task("task2").status, TaskStatus.COMPLETED)
        self.assertEqual(self.workflow.get_task("task3").status, TaskStatus.COMPLETED)
    
    def test_error_handling(self):
        """Test workflow error handling."""
        # Define tasks with an error
        def success_task():
            return {"status": "success"}
        
        def error_task():
            raise ValueError("Test error")
        
        def dependent_task():
            return {"status": "success"}
        
        # Add tasks
        self.workflow.add_task(
            Task(
                task_id="success-task",
                action=success_task,
                priority=Priority.MEDIUM
            )
        )
        
        self.workflow.add_task(
            Task(
                task_id="error-task",
                action=error_task,
                priority=Priority.MEDIUM
            )
        )
        
        self.workflow.add_task(
            Task(
                task_id="dependent-task",
                action=dependent_task,
                priority=Priority.MEDIUM,
                depends_on=["error-task"]
            )
        )
        
        # Mock the error handler
        self.workflow.on_error = MagicMock()
        
        # Start the workflow
        self.workflow.start()
        
        # Allow time for execution
        time.sleep(0.2)
        
        # Verify error handler was called
        self.workflow.on_error.assert_called_once()
        
        # Verify task statuses
        self.assertEqual(self.workflow.get_task("success-task").status, TaskStatus.COMPLETED)
        self.assertEqual(self.workflow.get_task("error-task").status, TaskStatus.FAILED)
        self.assertEqual(self.workflow.get_task("dependent-task").status, TaskStatus.PENDING)


class TestOnboardingWorkflow(unittest.TestCase):
    """Test the employee onboarding workflow template."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a task scheduler
        self.scheduler = TaskScheduler()
        
        # Mock identity manager
        self.identity_manager = IdentityManager()
        
        # Create test employee data
        self.employee_data = {
            "employee_id": "E-1001",
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "role": "Software Engineer",
            "department": "Engineering",
            "start_date": datetime.date.today() + datetime.timedelta(days=14),
            "manager_id": "E-500",
            "special_requirements": {
                "equipment": {
                    "laptop": "MacBook Pro",
                    "monitor": "Dual 27-inch"
                },
                "tech_stack": ["Python", "React", "PostgreSQL"]
            }
        }
    
    def test_onboarding_workflow_creation(self):
        """Test creation of onboarding workflow with correct structure."""
        # Create onboarding workflow
        workflow = OnboardingWorkflow(
            employee_id=self.employee_data["employee_id"],
            role=self.employee_data["role"],
            department=self.employee_data["department"],
            start_date=self.employee_data["start_date"],
            manager_id=self.employee_data["manager_id"],
            special_requirements=self.employee_data["special_requirements"]
        )
        
        # Register scheduler
        workflow.register_scheduler(self.scheduler)
        
        # Verify workflow metadata
        self.assertEqual(workflow.employee_id, self.employee_data["employee_id"])
        self.assertEqual(workflow.role, self.employee_data["role"])
        self.assertEqual(workflow.department, self.employee_data["department"])
        
        # Verify core tasks exist
        core_tasks = [
            "collect_employee_info",
            "prepare_workstation",
            "setup_accounts",
            "prepare_paperwork",
            "first_day_schedule",
            "assign_mentor",
            "training_plan",
            "30_day_check_in",
            "90_day_review_prep",
            "collect_onboarding_feedback"
        ]
        
        for task_id in core_tasks:
            task = workflow.get_task(task_id)
            self.assertIsNotNone(task, f"Task {task_id} not found")
        
        # Verify engineering-specific tasks for department
        engineering_tasks = ["dev_environment_setup", "code_access"]
        for task_id in engineering_tasks:
            task = workflow.get_task(task_id)
            self.assertIsNotNone(task, f"Engineering task {task_id} not found")
    
    def test_onboarding_task_dependencies(self):
        """Test dependencies between onboarding workflow tasks."""
        # Create onboarding workflow
        workflow = OnboardingWorkflow(
            employee_id=self.employee_data["employee_id"],
            role=self.employee_data["role"],
            department=self.employee_data["department"],
            start_date=self.employee_data["start_date"],
            manager_id=self.employee_data["manager_id"],
            special_requirements=self.employee_data["special_requirements"]
        )
        
        # Check dependencies
        
        # setup_accounts depends on collect_employee_info
        setup_accounts_task = workflow.get_task("setup_accounts")
        self.assertIn("collect_employee_info", setup_accounts_task.depends_on)
        
        # prepare_paperwork depends on collect_employee_info
        prepare_paperwork_task = workflow.get_task("prepare_paperwork")
        self.assertIn("collect_employee_info", prepare_paperwork_task.depends_on)
        
        # first_day_schedule depends on prepare_paperwork
        first_day_task = workflow.get_task("first_day_schedule")
        self.assertIn("prepare_paperwork", first_day_task.depends_on)
        
        # Engineering-specific task dependencies
        dev_env_task = workflow.get_task("dev_environment_setup")
        self.assertIn("setup_accounts", dev_env_task.depends_on)
        
        code_access_task = workflow.get_task("code_access")
        self.assertIn("setup_accounts", code_access_task.depends_on)
    
    @patch('orchestration.workflow_templates.onboarding.AgentTask')
    def test_onboarding_adaptive_behavior(self, mock_agent_task):
        """Test adaptive behavior of onboarding workflow."""
        # Create onboarding workflow
        workflow = OnboardingWorkflow(
            employee_id=self.employee_data["employee_id"],
            role=self.employee_data["role"],
            department=self.employee_data["department"],
            start_date=self.employee_data["start_date"],
            manager_id=self.employee_data["manager_id"],
            special_requirements=self.employee_data["special_requirements"]
        )
        
        # Simulate completion of collect_employee_info task with accessibility requirements
        mock_result = {
            "employee_id": self.employee_data["employee_id"],
            "accessibility_requirements": {
                "screen_reader": True,
                "keyboard_adaptation": "ergonomic"
            }
        }
        
        # Mock add_task method to check if accessibility_setup is added
        original_add_task = workflow.add_task
        workflow.add_task = MagicMock()
        
        # Trigger adaptive behavior
        workflow.on_task_completed("collect_employee_info", mock_result)
        
        # Verify that new task was added for accessibility setup
        workflow.add_task.assert_called_once()
        args, kwargs = workflow.add_task.call_args
        task = args[0]
        self.assertEqual(task.task_id, "accessibility_setup")
        self.assertEqual(task.agent_type, "it")
        self.assertEqual(task.parameters["employee_id"], self.employee_data["employee_id"])
        
        # Restore original method
        workflow.add_task = original_add_task
    
    @patch('orchestration.workflow_templates.onboarding.AgentTask')
    def test_onboarding_error_recovery(self, mock_agent_task):
        """Test error recovery in onboarding workflow."""
        # Create onboarding workflow
        workflow = OnboardingWorkflow(
            employee_id=self.employee_data["employee_id"],
            role=self.employee_data["role"],
            department=self.employee_data["department"],
            start_date=self.employee_data["start_date"],
            manager_id=self.employee_data["manager_id"],
            special_requirements=self.employee_data["special_requirements"]
        )
        
        # Mock add_task and reschedule_task methods
        workflow.add_task = MagicMock()
        workflow.reschedule_task = MagicMock()
        
        # Simulate an error in prepare_workstation task
        error = Exception("Equipment unavailable")
        workflow.on_error("prepare_workstation", error)
        
        # Verify recovery actions
        # 1. Should add temporary equipment task
        workflow.add_task.assert_called_once()
        args, kwargs = workflow.add_task.call_args
        temp_task = args[0]
        self.assertEqual(temp_task.task_id, "temporary_equipment")
        self.assertEqual(temp_task.priority, Priority.CRITICAL)
        
        # 2. Should reschedule the original task
        workflow.reschedule_task.assert_called_once()
        args, kwargs = workflow.reschedule_task.call_args
        self.assertEqual(args[0], "prepare_workstation")
        self.assertEqual(kwargs["new_priority"], Priority.CRITICAL)


class TestProcurementWorkflow(unittest.TestCase):
    """Test the procurement workflow template."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a task scheduler
        self.scheduler = TaskScheduler()
        
        # Create test procurement data
        self.procurement_data = {
            "request_id": "REQ-2001",
            "requester_id": "E-751",
            "department": "Marketing",
            "items": [
                {
                    "name": "Marketing Analytics Software",
                    "description": "Enterprise license for marketing analytics platform",
                    "quantity": 1,
                    "estimated_cost": 15000.00
                },
                {
                    "name": "Video Production Services",
                    "description": "Professional video production for product launch",
                    "quantity": 1,
                    "estimated_cost": 8500.00
                }
            ],
            "total_amount": 23500.00,
            "urgency": "high",
            "budget_code": "MKT-2025-Q2",
            "project_id": "P-2025-Launch"
        }
    
    def test_procurement_workflow_creation(self):
        """Test creation of procurement workflow with correct structure."""
        # Create procurement workflow
        workflow = ProcurementWorkflow(
            request_id=self.procurement_data["request_id"],
            requester_id=self.procurement_data["requester_id"],
            department=self.procurement_data["department"],
            items=self.procurement_data["items"],
            total_amount=self.procurement_data["total_amount"],
            urgency=self.procurement_data["urgency"],
            budget_code=self.procurement_data["budget_code"],
            project_id=self.procurement_data["project_id"]
        )
        
        # Register scheduler
        workflow.register_scheduler(self.scheduler)
        
        # Verify workflow metadata
        self.assertEqual(workflow.request_id, self.procurement_data["request_id"])
        self.assertEqual(workflow.requester_id, self.procurement_data["requester_id"])
        self.assertEqual(workflow.department, self.procurement_data["department"])
        
        # Verify core tasks exist
        core_tasks = [
            "validate_request",
            "verify_budget",
            "manager_approval",
            "director_approval",  # Should exist due to amount > $5000
            "final_approval",
            "vendor_selection",
            "create_purchase_order",
            "send_to_vendor",
            "track_order",
            "receive_items",
            "process_invoice",
            "process_payment",
            "notify_requester",
            "evaluate_vendor"
        ]
        
        for task_id in core_tasks:
            task = workflow.get_task(task_id)
            self.assertIsNotNone(task, f"Task {task_id} not found")
    
    def test_procurement_approval_chain(self):
        """Test approval chain based on amount thresholds."""
        # Test with different amounts
        test_cases = [
            {"amount": 2500.00, "expected_approvals": ["manager_approval"]},
            {"amount": 10000.00, "expected_approvals": ["manager_approval", "director_approval"]},
            {"amount": 30000.00, "expected_approvals": ["manager_approval", "director_approval", "vp_approval"]},
            {"amount": 120000.00, "expected_approvals": ["manager_approval", "director_approval", "vp_approval", "cfo_approval"]}
        ]
        
        for case in test_cases:
            # Create a new workflow with the test amount
            data = self.procurement_data.copy()
            data["total_amount"] = case["amount"]
            
            workflow = ProcurementWorkflow(
                request_id=data["request_id"],
                requester_id=data["requester_id"],
                department=data["department"],
                items=data["items"],
                total_amount=data["amount"],
                urgency=data["urgency"],
                budget_code=data["budget_code"],
                project_id=data["project_id"]
            )
            
            # Verify expected approval tasks exist
            for approval in case["expected_approvals"]:
                task = workflow.get_task(approval)
                self.assertIsNotNone(task, f"Approval task {approval} not found for amount {case['amount']}")
            
            # Check final approval depends on the last approval in chain
            final_approval = workflow.get_task("final_approval")
            last_approval = case["expected_approvals"][-1]
            self.assertIn(last_approval, final_approval.depends_on)
    
    @patch('orchestration.workflow_templates.procurement.AgentTask')
    def test_procurement_adaptive_behavior(self, mock_agent_task):
        """Test adaptive behavior of procurement workflow."""
        # Create procurement workflow
        workflow = ProcurementWorkflow(
            request_id=self.procurement_data["request_id"],
            requester_id=self.procurement_data["requester_id"],
            department=self.procurement_data["department"],
            items=self.procurement_data["items"],
            total_amount=self.procurement_data["total_amount"],
            urgency=self.procurement_data["urgency"],
            budget_code=self.procurement_data["budget_code"],
            project_id=self.procurement_data["project_id"]
        )
        
        # Simulate insufficient budget result
        budget_result = {
            "status": "insufficient_funds",
            "shortfall": 5000.00,
            "funding_options": ["budget_transfer", "expense_deferral"]
        }
        
        # Mock add_task method
        original_add_task = workflow.add_task
        workflow.add_task = MagicMock()
        
        # Get original manager_approval task
        manager_approval_task = workflow.get_task("manager_approval")
        
        # Trigger adaptive behavior
        workflow.on_task_completed("verify_budget", budget_result)
        
        # Verify budget exception task was added
        workflow.add_task.assert_called_once()
        args, kwargs = workflow.add_task.call_args
        task = args[0]
        self.assertEqual(task.task_id, "budget_exception")
        self.assertEqual(task.agent_type, "finance")
        self.assertEqual(task.parameters["shortfall"], 5000.00)
        
        # Restore original method
        workflow.add_task = original_add_task
    
    @patch('orchestration.workflow_templates.procurement.AgentTask')
    def test_procurement_vendor_selection_handling(self, mock_agent_task):
        """Test vendor selection handling in procurement workflow."""
        # Create procurement workflow
        workflow = ProcurementWorkflow(
            request_id=self.procurement_data["request_id"],
            requester_id=self.procurement_data["requester_id"],
            department=self.procurement_data["department"],
            items=self.procurement_data["items"],
            total_amount=self.procurement_data["total_amount"],
            urgency=self.procurement_data["urgency"],
            budget_code=self.procurement_data["budget_code"],
            project_id=self.procurement_data["project_id"]
        )
        
        # Simulate vendor selection with multiple vendors
        vendor_result = {
            "selected_vendors": [
                {
                    "vendor_id": "V-101",
                    "name": "Software Solutions Inc.",
                    "items": [self.procurement_data["items"][0]],
                    "total_amount": 15000.00
                },
                {
                    "vendor_id": "V-203",
                    "name": "Creative Media Productions",
                    "items": [self.procurement_data["items"][1]],
                    "total_amount": 8500.00
                }
            ]
        }
        
        # Mock add_task method
        original_add_task = workflow.add_task
        workflow.add_task = MagicMock()
        
        # Trigger adaptive behavior
        workflow.on_task_completed("vendor_selection", vendor_result)
        
        # Verify vendor-specific PO tasks were added
        self.assertEqual(workflow.add_task.call_count, 2)
        
        # Check first vendor PO task
        args1, kwargs1 = workflow.add_task.call_args_list[0]
        task1 = args1[0]
        self.assertEqual(task1.task_id, "vendor_po_1")
        self.assertEqual(task1.parameters["vendor_id"], "V-101")
        self.assertEqual(task1.parameters["total_amount"], 15000.00)
        
        # Check second vendor PO task
        args2, kwargs2 = workflow.add_task.call_args_list[1]
        task2 = args2[0]
        self.assertEqual(task2.task_id, "vendor_po_2")
        self.assertEqual(task2.parameters["vendor_id"], "V-203")
        self.assertEqual(task2.parameters["total_amount"], 8500.00)
        
        # Restore original method
        workflow.add_task = original_add_task
    
    @patch('orchestration.workflow_templates.procurement.AgentTask')
    def test_procurement_quality_issue_handling(self, mock_agent_task):
        """Test quality issue handling in procurement workflow."""
        # Create procurement workflow
        workflow = ProcurementWorkflow(
            request_id=self.procurement_data["request_id"],
            requester_id=self.procurement_data["requester_id"],
            department=self.procurement_data["department"],
            items=self.procurement_data["items"],
            total_amount=self.procurement_data["total_amount"],
            urgency=self.procurement_data["urgency"],
            budget_code=self.procurement_data["budget_code"],
            project_id=self.procurement_data["project_id"]
        )
        
        # Simulate receiving items with quality issues
        receive_result = {
            "status": "partial",
            "quality_issues": True,
            "issue_details": {
                "item_id": 1,
                "description": "Video quality below specified requirements",
                "severity": "high"
            },
            "vendor_id": "V-203"
        }
        
        # Mock add_task method
        original_add_task = workflow.add_task
        workflow.add_task = MagicMock()
        
        # Trigger adaptive behavior
        workflow.on_task_completed("receive_items", receive_result)
        
        # Verify quality issue resolution task was added
        workflow.add_task.assert_called_once()
        args, kwargs = workflow.add_task.call_args
        task = args[0]
        self.assertEqual(task.task_id, "resolve_quality_issues")
        self.assertEqual(task.agent_type, "procurement")
        self.assertEqual(task.parameters["vendor_id"], "V-203")
        
        # Restore original method
        workflow.add_task = original_add_task
    
    def test_procurement_optimization(self):
        """Test procurement workflow optimization based on historical data."""
        # Create procurement workflow
        workflow = ProcurementWorkflow(
            request_id=self.procurement_data["request_id"],
            requester_id=self.procurement_data["requester_id"],
            department=self.procurement_data["department"],
            items=self.procurement_data["items"],
            total_amount=self.procurement_data["total_amount"],
            urgency=self.procurement_data["urgency"],
            budget_code=self.procurement_data["budget_code"],
            project_id=self.procurement_data["project_id"]
        )
        
        # Create historical workflow data
        historical_workflows = [
            {
                "tasks": {
                    "validate_request": {"actual_duration": datetime.timedelta(minutes=25)},
                    "verify_budget": {"actual_duration": datetime.timedelta(minutes=40)},
                    "vendor_selection": {"actual_duration": datetime.timedelta(hours=1, minutes=15)}
                },
                "vendor_evaluation": {
                    "vendor_id": "V-101",
                    "score": 4.2
                }
            },
            {
                "tasks": {
                    "validate_request": {"actual_duration": datetime.timedelta(minutes=30)},
                    "verify_budget": {"actual_duration": datetime.timedelta(minutes=35)},
                    "vendor_selection": {"actual_duration": datetime.timedelta(hours=1, minutes=30)}
                },
                "vendor_evaluation": {
                    "vendor_id": "V-101",
                    "score": 4.5
                }
            },
            {
                "tasks": {
                    "validate_request": {"actual_duration": datetime.timedelta(minutes=20)},
                    "verify_budget": {"actual_duration": datetime.timedelta(minutes=30)},
                    "vendor_selection": {"actual_duration": datetime.timedelta(hours=1, minutes=10)}
                },
                "vendor_evaluation": {
                    "vendor_id": "V-203",
                    "score": 3.8
                }
            }
        ]
        
        # Store original task durations
        original_durations = {}
        for task_id in ["validate_request", "verify_budget", "vendor_selection"]:
            task = workflow.get_task(task_id)
            original_durations[task_id] = task.estimated_duration
        
        # Optimize workflow
        workflow.optimize_from_history(historical_workflows)
        
        # Verify task durations were updated
        for task_id in ["validate_request", "verify_budget", "vendor_selection"]:
            task = workflow.get_task(task_id)
            self.assertNotEqual(task.estimated_duration, original_durations[task_id],
                               f"Duration for {task_id} should have been updated")
        
        # Verify vendor selection was optimized
        vendor_task = workflow.get_task("vendor_selection")
        self.assertIn("V-101", vendor_task.parameters["preferred_vendors"],
                      "High-scoring vendor should be preferred")


if __name__ == '__main__':
    unittest.main()