"""
Unit Tests for AI Agents

This module tests individual AI agent implementations, including finance,
HR, and supply chain agents, focusing on their core reasoning capabilities.
"""

import unittest
import os
import sys
import json
import datetime
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import agent components
from models.agent_factory import AgentFactory
from models.agent_base import AgentBase, AgentResponse, AgentCapability
from models.prompt_templates import PromptTemplateManager


class TestAgentBase(unittest.TestCase):
    """Test the base agent implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock template manager
        self.template_manager = MagicMock()
        self.template_manager.get_template.return_value = "Template for {action}"
        
        # Create a base agent
        self.agent = AgentBase(
            agent_id="test-agent",
            model_name="test-model",
            template_manager=self.template_manager
        )
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.agent_id, "test-agent")
        self.assertEqual(self.agent.model_name, "test-model")
        self.assertEqual(self.agent.capabilities, set())
    
    def test_register_capability(self):
        """Test capability registration."""
        # Define a capability
        capability = AgentCapability(
            name="test_capability",
            description="Test capability",
            parameters={"param1": "string", "param2": "integer"}
        )
        
        # Register the capability
        self.agent.register_capability(capability)
        
        # Verify it was registered
        self.assertIn(capability, self.agent.capabilities)
        
        # Check by name
        self.assertTrue(self.agent.has_capability("test_capability"))
        self.assertFalse(self.agent.has_capability("nonexistent_capability"))
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_execute_action(self, mock_call_model):
        """Test action execution."""
        # Set up the mock to return a response
        mock_call_model.return_value = {"result": "Success"}
        
        # Register a test capability
        capability = AgentCapability(
            name="test_action",
            description="Test action",
            parameters={"param1": "string", "param2": "integer"}
        )
        self.agent.register_capability(capability)
        
        # Execute the action
        response = self.agent.execute_action(
            "test_action",
            {"param1": "value", "param2": 42}
        )
        
        # Verify the template was retrieved
        self.template_manager.get_template.assert_called_once_with("test_action")
        
        # Verify the model was called
        mock_call_model.assert_called_once()
        
        # Verify the response
        self.assertIsInstance(response, AgentResponse)
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["result"], "Success")
    
    def test_execute_invalid_action(self):
        """Test execution of an invalid action."""
        # Try to execute an unregistered action
        with self.assertRaises(ValueError):
            self.agent.execute_action("invalid_action", {})
    
    def test_validate_parameters(self):
        """Test parameter validation."""
        # Register a test capability
        capability = AgentCapability(
            name="validate_test",
            description="Test validation",
            parameters={
                "required_param": "string",
                "optional_param": {"type": "integer", "required": False}
            }
        )
        self.agent.register_capability(capability)
        
        # Test valid parameters
        valid_params = {"required_param": "value", "optional_param": 42}
        self.assertTrue(self.agent._validate_parameters("validate_test", valid_params))
        
        # Test missing required parameter
        invalid_params = {"optional_param": 42}
        with self.assertRaises(ValueError):
            self.agent._validate_parameters("validate_test", invalid_params)
        
        # Test invalid parameter type
        invalid_type_params = {"required_param": "value", "optional_param": "not-an-integer"}
        with self.assertRaises(TypeError):
            self.agent._validate_parameters("validate_test", invalid_type_params)


class TestFinanceAgent(unittest.TestCase):
    """Test the finance agent implementation."""
    
    @patch('models.model_registry.ModelRegistry')
    def setUp(self, mock_model_registry):
        """Set up test fixtures."""
        # Create a mock model registry
        self.model_registry = mock_model_registry()
        self.model_registry.get_model.return_value = MagicMock()
        
        # Create a mock template manager
        self.template_manager = MagicMock()
        
        # Create an agent factory
        self.agent_factory = AgentFactory(self.model_registry)
        
        # Mock the finance agent capabilities
        self.finance_capabilities = [
            AgentCapability(
                name="analyze_invoice",
                description="Analyze and extract information from invoices",
                parameters={
                    "invoice_text": "string",
                    "extract_line_items": {"type": "boolean", "required": False}
                }
            ),
            AgentCapability(
                name="forecast_cash_flow",
                description="Forecast cash flow based on historical data",
                parameters={
                    "historical_data": "array",
                    "forecast_period": "integer",
                    "include_confidence": {"type": "boolean", "required": False}
                }
            ),
            AgentCapability(
                name="detect_anomalies",
                description="Detect anomalies in financial transactions",
                parameters={
                    "transactions": "array",
                    "sensitivity": {"type": "float", "required": False}
                }
            )
        ]
        
        # Create a finance agent with mocked components
        with patch('models.finance_agent.FinanceAgent.register_capabilities') as mock_register:
            self.finance_agent = self.agent_factory.create_agent(
                agent_type="finance",
                agent_id="finance-test",
                template_manager=self.template_manager
            )
            
            # Manually set capabilities since we've mocked the registration
            self.finance_agent.capabilities = set(self.finance_capabilities)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_analyze_invoice(self, mock_call_model):
        """Test invoice analysis capability."""
        # Mock invoice analysis result
        mock_result = {
            "vendor": "Acme Corp",
            "invoice_number": "INV-12345",
            "date": "2025-03-15",
            "total_amount": 1250.75,
            "currency": "USD",
            "line_items": [
                {"description": "Product A", "quantity": 5, "unit_price": 150.00, "total": 750.00},
                {"description": "Service B", "quantity": 2, "unit_price": 250.00, "total": 500.00}
            ],
            "confidence_score": 0.95
        }
        mock_call_model.return_value = mock_result
        
        # Create test invoice text
        invoice_text = """
        INVOICE
        
        Acme Corp
        123 Business St
        Business City, BC 12345
        
        Invoice Number: INV-12345
        Date: March 15, 2025
        
        Bill To:
        XYZ Company
        
        Items:
        5 x Product A @ $150.00 each = $750.00
        2 x Service B @ $250.00 each = $500.00
        
        Total: $1,250.75
        """
        
        # Execute the action
        response = self.finance_agent.execute_action(
            "analyze_invoice",
            {"invoice_text": invoice_text, "extract_line_items": True}
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["vendor"], "Acme Corp")
        self.assertEqual(response.data["invoice_number"], "INV-12345")
        self.assertEqual(response.data["total_amount"], 1250.75)
        self.assertEqual(len(response.data["line_items"]), 2)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_forecast_cash_flow(self, mock_call_model):
        """Test cash flow forecasting capability."""
        # Mock forecast result
        mock_result = {
            "forecast": [
                {"month": "2025-04", "amount": 125000, "confidence_low": 120000, "confidence_high": 130000},
                {"month": "2025-05", "amount": 130000, "confidence_low": 125000, "confidence_high": 135000},
                {"month": "2025-06", "amount": 135000, "confidence_low": 128000, "confidence_high": 142000}
            ],
            "trend": "increasing",
            "seasonality_factors": [1.0, 1.05, 1.08],
            "confidence_score": 0.85
        }
        mock_call_model.return_value = mock_result
        
        # Create test historical data
        historical_data = [
            {"month": "2025-01", "amount": 115000},
            {"month": "2025-02", "amount": 118000},
            {"month": "2025-03", "amount": 122000}
        ]
        
        # Execute the action
        response = self.finance_agent.execute_action(
            "forecast_cash_flow",
            {
                "historical_data": historical_data,
                "forecast_period": 3,
                "include_confidence": True
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(len(response.data["forecast"]), 3)
        self.assertEqual(response.data["trend"], "increasing")
        self.assertGreater(response.data["confidence_score"], 0.8)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_detect_anomalies(self, mock_call_model):
        """Test anomaly detection capability."""
        # Mock anomaly detection result
        mock_result = {
            "anomalies": [
                {
                    "transaction_id": "T-1042",
                    "amount": 15275.00,
                    "reason": "Unusually large amount for vendor",
                    "confidence": 0.92,
                    "severity": "high"
                },
                {
                    "transaction_id": "T-1053",
                    "amount": 450.00,
                    "reason": "Duplicate transaction",
                    "confidence": 0.95,
                    "severity": "medium"
                }
            ],
            "total_anomalies": 2,
            "false_positive_risk": "low"
        }
        mock_call_model.return_value = mock_result
        
        # Create test transaction data
        transactions = [
            {"id": "T-1040", "date": "2025-03-10", "vendor": "ABC Supplies", "amount": 5250.00},
            {"id": "T-1041", "date": "2025-03-11", "vendor": "Office Depot", "amount": 782.50},
            {"id": "T-1042", "date": "2025-03-12", "vendor": "XYZ Services", "amount": 15275.00},
            {"id": "T-1043", "date": "2025-03-13", "vendor": "City Power", "amount": 1450.00},
            {"id": "T-1044", "date": "2025-03-14", "vendor": "Office Depot", "amount": 325.75},
            {"id": "T-1053", "date": "2025-03-14", "vendor": "Office Depot", "amount": 450.00},
        ]
        
        # Execute the action
        response = self.finance_agent.execute_action(
            "detect_anomalies",
            {
                "transactions": transactions,
                "sensitivity": 0.8
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(len(response.data["anomalies"]), 2)
        self.assertEqual(response.data["anomalies"][0]["transaction_id"], "T-1042")
        self.assertEqual(response.data["total_anomalies"], 2)


class TestHRAgent(unittest.TestCase):
    """Test the HR agent implementation."""
    
    @patch('models.model_registry.ModelRegistry')
    def setUp(self, mock_model_registry):
        """Set up test fixtures."""
        # Create a mock model registry
        self.model_registry = mock_model_registry()
        self.model_registry.get_model.return_value = MagicMock()
        
        # Create a mock template manager
        self.template_manager = MagicMock()
        
        # Create an agent factory
        self.agent_factory = AgentFactory(self.model_registry)
        
        # Mock the HR agent capabilities
        self.hr_capabilities = [
            AgentCapability(
                name="evaluate_candidate",
                description="Evaluate job candidate based on resume and job requirements",
                parameters={
                    "resume_text": "string",
                    "job_requirements": "string",
                    "include_feedback": {"type": "boolean", "required": False}
                }
            ),
            AgentCapability(
                name="analyze_attrition",
                description="Analyze employee attrition patterns",
                parameters={
                    "employee_data": "array",
                    "time_period": {"type": "string", "required": False},
                    "department": {"type": "string", "required": False}
                }
            ),
            AgentCapability(
                name="generate_training_plan",
                description="Generate personalized training plan for employee",
                parameters={
                    "employee_id": "string",
                    "skills_assessment": "object",
                    "career_goals": "string",
                    "duration_months": {"type": "integer", "required": False}
                }
            )
        ]
        
        # Create an HR agent with mocked components
        with patch('models.hr_agent.HRAgent.register_capabilities') as mock_register:
            self.hr_agent = self.agent_factory.create_agent(
                agent_type="hr",
                agent_id="hr-test",
                template_manager=self.template_manager
            )
            
            # Manually set capabilities since we've mocked the registration
            self.hr_agent.capabilities = set(self.hr_capabilities)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_evaluate_candidate(self, mock_call_model):
        """Test candidate evaluation capability."""
        # Mock evaluation result
        mock_result = {
            "match_score": 85,
            "strengths": [
                "5+ years of Python development experience",
                "Strong background in machine learning",
                "Experience with cloud infrastructure"
            ],
            "gaps": [
                "Limited experience with React framework",
                "No formal project management experience"
            ],
            "recommendation": "Interview - Strong technical match",
            "feedback": "Candidate shows strong technical skills that align well with requirements. "
                       "Technical interview should focus on front-end development experience.",
            "confidence_score": 0.92
        }
        mock_call_model.return_value = mock_result
        
        # Create test resume and job requirements
        resume_text = """
        John Smith
        Software Engineer
        
        Experience:
        - Senior Developer at Tech Company (2020-Present)
          * Lead developer for machine learning applications
          * Python, TensorFlow, AWS
        
        - Developer at Startup Inc (2017-2020)
          * Full-stack development
          * Python, Django, JavaScript
        
        Education:
        - MS Computer Science, University, 2017
        """
        
        job_requirements = """
        Requirements:
        - 5+ years of experience in software development
        - Strong knowledge of Python and machine learning frameworks
        - Experience with React and front-end development
        - Experience with cloud infrastructure (AWS/Azure)
        """
        
        # Execute the action
        response = self.hr_agent.execute_action(
            "evaluate_candidate",
            {
                "resume_text": resume_text,
                "job_requirements": job_requirements,
                "include_feedback": True
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["match_score"], 85)
        self.assertGreaterEqual(len(response.data["strengths"]), 2)
        self.assertGreaterEqual(len(response.data["gaps"]), 1)
        self.assertIn("recommendation", response.data)
        self.assertIn("feedback", response.data)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_analyze_attrition(self, mock_call_model):
        """Test attrition analysis capability."""
        # Mock attrition analysis result
        mock_result = {
            "attrition_rate": 12.5,
            "departmental_breakdown": [
                {"department": "Engineering", "rate": 8.3, "risk": "low"},
                {"department": "Sales", "rate": 18.7, "risk": "high"},
                {"department": "Support", "rate": 14.2, "risk": "medium"}
            ],
            "key_factors": [
                {"factor": "Compensation", "impact_score": 7.8},
                {"factor": "Work-Life Balance", "impact_score": 6.5},
                {"factor": "Career Growth", "impact_score": 8.2}
            ],
            "high_risk_employees": [
                {"id": "E-1042", "risk_score": 0.85, "factors": ["tenure", "performance", "compensation"]},
                {"id": "E-1053", "risk_score": 0.78, "factors": ["role changes", "team changes", "compensation"]}
            ],
            "recommendations": [
                "Review compensation structure for Sales team",
                "Implement career development programs",
                "Improve manager training for retention strategies"
            ],
            "confidence_score": 0.87
        }
        mock_call_model.return_value = mock_result
        
        # Create test employee data
        employee_data = [
            {"id": "E-1001", "department": "Engineering", "tenure": 3.5, "performance": 4.2, "satisfaction": 4.0, "status": "active"},
            {"id": "E-1042", "department": "Sales", "tenure": 1.2, "performance": 3.8, "satisfaction": 2.5, "status": "active"},
            {"id": "E-1053", "department": "Sales", "tenure": 0.8, "performance": 4.0, "satisfaction": 3.0, "status": "active"},
            {"id": "E-1022", "department": "Engineering", "tenure": 2.0, "performance": 3.5, "satisfaction": 3.2, "status": "terminated"},
            {"id": "E-1035", "department": "Support", "tenure": 1.5, "performance": 3.7, "satisfaction": 3.5, "status": "terminated"}
        ]
        
        # Execute the action
        response = self.hr_agent.execute_action(
            "analyze_attrition",
            {
                "employee_data": employee_data,
                "time_period": "last_12_months",
                "department": None  # All departments
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertIn("attrition_rate", response.data)
        self.assertGreaterEqual(len(response.data["departmental_breakdown"]), 2)
        self.assertGreaterEqual(len(response.data["key_factors"]), 2)
        self.assertGreaterEqual(len(response.data["high_risk_employees"]), 1)
        self.assertGreaterEqual(len(response.data["recommendations"]), 2)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_generate_training_plan(self, mock_call_model):
        """Test training plan generation capability."""
        # Mock training plan result
        mock_result = {
            "employee_id": "E-1001",
            "plan_start_date": "2025-04-01",
            "plan_duration_months": 6,
            "development_areas": [
                {"skill": "Machine Learning", "current_level": 3, "target_level": 4},
                {"skill": "Cloud Architecture", "current_level": 2, "target_level": 4},
                {"skill": "Team Leadership", "current_level": 2, "target_level": 3}
            ],
            "recommended_activities": [
                {
                    "type": "Course",
                    "name": "Advanced Machine Learning Specialization",
                    "provider": "Coursera",
                    "duration": "8 weeks",
                    "priority": "high"
                },
                {
                    "type": "Project",
                    "name": "Cloud Migration Initiative",
                    "description": "Shadow cloud architect on upcoming migration project",
                    "duration": "3 months",
                    "priority": "medium"
                },
                {
                    "type": "Training",
                    "name": "Leadership Fundamentals Workshop",
                    "provider": "Internal",
                    "duration": "2 days",
                    "priority": "medium"
                }
            ],
            "milestones": [
                {"date": "2025-06-01", "description": "Complete ML course and apply to current project"},
                {"date": "2025-08-01", "description": "Lead team meeting for cloud migration planning"},
                {"date": "2025-10-01", "description": "Full development plan review"}
            ],
            "estimated_budget": 2500,
            "confidence_score": 0.91
        }
        mock_call_model.return_value = mock_result
        
        # Create test input data
        skills_assessment = {
            "technical": {
                "python": 4,
                "machine_learning": 3,
                "cloud_infrastructure": 2
            },
            "soft_skills": {
                "communication": 4,
                "leadership": 2,
                "problem_solving": 4
            }
        }
        
        career_goals = """
        I want to transition into a role that combines machine learning engineering with 
        technical leadership. I'd like to lead ML projects and eventually manage a team of ML engineers.
        """
        
        # Execute the action
        response = self.hr_agent.execute_action(
            "generate_training_plan",
            {
                "employee_id": "E-1001",
                "skills_assessment": skills_assessment,
                "career_goals": career_goals,
                "duration_months": 6
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["employee_id"], "E-1001")
        self.assertEqual(response.data["plan_duration_months"], 6)
        self.assertGreaterEqual(len(response.data["development_areas"]), 2)
        self.assertGreaterEqual(len(response.data["recommended_activities"]), 2)
        self.assertGreaterEqual(len(response.data["milestones"]), 1)
        self.assertIn("estimated_budget", response.data)


class TestSupplyChainAgent(unittest.TestCase):
    """Test the supply chain agent implementation."""
    
    @patch('models.model_registry.ModelRegistry')
    def setUp(self, mock_model_registry):
        """Set up test fixtures."""
        # Create a mock model registry
        self.model_registry = mock_model_registry()
        self.model_registry.get_model.return_value = MagicMock()
        
        # Create a mock template manager
        self.template_manager = MagicMock()
        
        # Create an agent factory
        self.agent_factory = AgentFactory(self.model_registry)
        
        # Mock the supply chain agent capabilities
        self.supply_chain_capabilities = [
            AgentCapability(
                name="optimize_inventory",
                description="Optimize inventory levels based on demand forecast",
                parameters={
                    "product_id": "string",
                    "historical_demand": "array",
                    "lead_time": {"type": "integer", "required": False},
                    "holding_cost": {"type": "float", "required": False},
                    "stockout_cost": {"type": "float", "required": False}
                }
            ),
            AgentCapability(
                name="forecast_demand",
                description="Forecast future demand based on historical data",
                parameters={
                    "product_id": "string",
                    "historical_data": "array",
                    "forecast_horizon": "integer",
                    "include_seasonality": {"type": "boolean", "required": False}
                }
            ),
            AgentCapability(
                name="evaluate_supplier",
                description="Evaluate supplier performance based on historical data",
                parameters={
                    "supplier_id": "string",
                    "performance_data": "array",
                    "evaluation_criteria": {"type": "array", "required": False}
                }
            )
        ]
        
        # Create a supply chain agent with mocked components
        with patch('models.supply_chain_agent.SupplyChainAgent.register_capabilities') as mock_register:
            self.supply_chain_agent = self.agent_factory.create_agent(
                agent_type="supply_chain",
                agent_id="supply-chain-test",
                template_manager=self.template_manager
            )
            
            # Manually set capabilities since we've mocked the registration
            self.supply_chain_agent.capabilities = set(self.supply_chain_capabilities)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_optimize_inventory(self, mock_call_model):
        """Test inventory optimization capability."""
        # Mock optimization result
        mock_result = {
            "product_id": "P-1001",
            "optimal_inventory": 250,
            "reorder_point": 75,
            "order_quantity": 200,
            "safety_stock": 50,
            "service_level": 0.95,
            "estimated_savings": 12500.00,
            "stockout_probability": 0.03,
            "confidence_score": 0.89
        }
        mock_call_model.return_value = mock_result
        
        # Create test historical demand data
        historical_demand = [
            {"month": "2024-09", "demand": 180},
            {"month": "2024-10", "demand": 210},
            {"month": "2024-11", "demand": 250},
            {"month": "2024-12", "demand": 320},
            {"month": "2025-01", "demand": 220},
            {"month": "2025-02", "demand": 190}
        ]
        
        # Execute the action
        response = self.supply_chain_agent.execute_action(
            "optimize_inventory",
            {
                "product_id": "P-1001",
                "historical_demand": historical_demand,
                "lead_time": 14,
                "holding_cost": 0.2,
                "stockout_cost": 10.5
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["product_id"], "P-1001")
        self.assertIn("optimal_inventory", response.data)
        self.assertIn("reorder_point", response.data)
        self.assertIn("order_quantity", response.data)
        self.assertIn("service_level", response.data)
        self.assertIn("estimated_savings", response.data)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_forecast_demand(self, mock_call_model):
        """Test demand forecasting capability."""
        # Mock forecast result
        mock_result = {
            "product_id": "P-1001",
            "forecast": [
                {"month": "2025-03", "demand": 205, "lower_bound": 185, "upper_bound": 225},
                {"month": "2025-04", "demand": 215, "lower_bound": 190, "upper_bound": 240},
                {"month": "2025-05", "demand": 230, "lower_bound": 200, "upper_bound": 260}
            ],
            "trend": "increasing",
            "seasonality_factors": [0.9, 1.0, 1.1, 1.3, 0.95, 0.85, 0.9, 0.95, 1.0, 1.05, 1.15, 1.25],
            "accuracy_metrics": {
                "mape": 8.5,
                "rmse": 17.2
            },
            "confidence_score": 0.87
        }
        mock_call_model.return_value = mock_result
        
        # Create test historical data
        historical_data = [
            {"month": "2024-09", "demand": 180},
            {"month": "2024-10", "demand": 210},
            {"month": "2024-11", "demand": 250},
            {"month": "2024-12", "demand": 320},
            {"month": "2025-01", "demand": 220},
            {"month": "2025-02", "demand": 190}
        ]
        
        # Execute the action
        response = self.supply_chain_agent.execute_action(
            "forecast_demand",
            {
                "product_id": "P-1001",
                "historical_data": historical_data,
                "forecast_horizon": 3,
                "include_seasonality": True
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["product_id"], "P-1001")
        self.assertEqual(len(response.data["forecast"]), 3)
        self.assertIn("trend", response.data)
        self.assertIn("seasonality_factors", response.data)
        self.assertIn("accuracy_metrics", response.data)
        self.assertIn("confidence_score", response.data)
    
    @patch('models.agent_base.AgentBase._call_model')
    def test_evaluate_supplier(self, mock_call_model):
        """Test supplier evaluation capability."""
        # Mock evaluation result
        mock_result = {
            "supplier_id": "S-501",
            "overall_score": 82.5,
            "performance_breakdown": {
                "quality": 85,
                "delivery": 78,
                "cost": 88,
                "responsiveness": 75
            },
            "recommendations": [
                "Implement delivery performance improvement plan",
                "Enhance communication channels for better responsiveness",
                "Maintain current quality control processes"
            ],
            "trend_analysis": {
                "quality": "improving",
                "delivery": "declining",
                "cost": "stable",
                "responsiveness": "stable"
            },
            "risk_assessment": "low",
            "confidence_score": 0.9
        }
        mock_call_model.return_value = mock_result
        
        # Create test performance data
        performance_data = [
            {
                "order_id": "O-10042",
                "date": "2025-01-10",
                "quality_score": 84,
                "delivery_days": 12,
                "delivery_score": 76,
                "cost_variance": -2.5
            },
            {
                "order_id": "O-10156",
                "date": "2025-02-05",
                "quality_score": 85,
                "delivery_days": 13,
                "delivery_score": 74,
                "cost_variance": -3.1
            },
            {
                "order_id": "O-10287",
                "date": "2025-03-12",
                "quality_score": 87,
                "delivery_days": 12,
                "delivery_score": 78,
                "cost_variance": -2.8
            }
        ]
        
        # Execute the action
        response = self.supply_chain_agent.execute_action(
            "evaluate_supplier",
            {
                "supplier_id": "S-501",
                "performance_data": performance_data,
                "evaluation_criteria": ["quality", "delivery", "cost", "responsiveness"]
            }
        )
        
        # Verify the response
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["supplier_id"], "S-501")
        self.assertIn("overall_score", response.data)
        self.assertIn("performance_breakdown", response.data)
        self.assertIn("quality", response.data["performance_breakdown"])
        self.assertIn("delivery", response.data["performance_breakdown"])
        self.assertGreaterEqual(len(response.data["recommendations"]), 2)
        self.assertIn("trend_analysis", response.data)
        self.assertIn("risk_assessment", response.data)


if __name__ == '__main__':
    unittest.main()