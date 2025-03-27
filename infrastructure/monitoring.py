"""
AI-Native ERP System - Infrastructure Monitoring Module

This module provides real-time monitoring and observability for the decentralized
AI-native ERP system. It integrates with various AI agents and components to track:
- AI agent performance and resource utilization
- Neural data fabric health and throughput
- Autonomous process orchestration effectiveness
- Self-healing and self-optimization metrics
- Federated learning performance across nodes
"""

import time
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("erp_monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_erp_monitoring")

class AIAgentMonitor:
    """Monitor individual AI agent performance and health."""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.metrics = {
            "inference_times": [],
            "token_usage": 0,
            "errors": 0,
            "successful_executions": 0,
            "last_active": None
        }
    
    async def capture_inference_time(self, execution_time_ms: float):
        """Record the time taken for an inference operation."""
        self.metrics["inference_times"].append(execution_time_ms)
        self.metrics["successful_executions"] += 1
        self.metrics["last_active"] = datetime.now().isoformat()
        
        # Calculate and log rolling average
        avg_time = sum(self.metrics["inference_times"][-100:]) / min(len(self.metrics["inference_times"]), 100)
        logger.info(f"Agent {self.agent_id} ({self.agent_type}) - Avg inference time: {avg_time:.2f}ms")
    
    def record_token_usage(self, tokens: int):
        """Track token usage for LLM-based agents."""
        self.metrics["token_usage"] += tokens
        
    def record_error(self, error_type: str, error_msg: str):
        """Record an error encountered by the agent."""
        self.metrics["errors"] += 1
        logger.error(f"Agent {self.agent_id} error ({error_type}): {error_msg}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return the current health status of the agent."""
        if not self.metrics["inference_times"]:
            return {"status": "inactive", "agent_id": self.agent_id, "agent_type": self.agent_type}
            
        avg_time = sum(self.metrics["inference_times"][-100:]) / min(len(self.metrics["inference_times"]), 100)
        error_rate = self.metrics["errors"] / max(self.metrics["successful_executions"], 1)
        
        status = "healthy"
        if error_rate > 0.05:  # More than 5% error rate
            status = "degraded"
        if error_rate > 0.20:  # More than 20% error rate
            status = "unhealthy"
            
        return {
            "status": status,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "avg_inference_time": avg_time,
            "error_rate": error_rate,
            "token_usage": self.metrics["token_usage"],
            "last_active": self.metrics["last_active"]
        }

class NeuralDataFabricMonitor:
    """Monitor the neural data fabric's health and performance."""
    
    def __init__(self, fabric_id: str, fabric_type: str):
        self.fabric_id = fabric_id
        self.fabric_type = fabric_type  # e.g., "vector_db", "knowledge_graph", "event_stream"
        self.metrics = {
            "query_times": [],
            "storage_used_mb": 0,
            "total_entries": 0,
            "read_ops": 0,
            "write_ops": 0,
            "last_update": None
        }
    
    async def record_query_time(self, query_time_ms: float):
        """Record time taken for data fabric query."""
        self.metrics["query_times"].append(query_time_ms)
        self.metrics["read_ops"] += 1
        self.metrics["last_update"] = datetime.now().isoformat()
    
    def update_storage_metrics(self, storage_mb: float, total_entries: int):
        """Update storage usage metrics."""
        self.metrics["storage_used_mb"] = storage_mb
        self.metrics["total_entries"] = total_entries
        logger.info(f"Data Fabric {self.fabric_id} storage: {storage_mb:.2f}MB, {total_entries} entries")
    
    def record_write_operation(self):
        """Record a write operation to the data fabric."""
        self.metrics["write_ops"] += 1
        self.metrics["last_update"] = datetime.now().isoformat()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return current performance metrics of the data fabric."""
        if not self.metrics["query_times"]:
            return {
                "fabric_id": self.fabric_id,
                "fabric_type": self.fabric_type,
                "status": "inactive"
            }
            
        avg_query_time = sum(self.metrics["query_times"][-100:]) / min(len(self.metrics["query_times"]), 100)
        read_write_ratio = self.metrics["read_ops"] / max(self.metrics["write_ops"], 1)
        
        return {
            "fabric_id": self.fabric_id,
            "fabric_type": self.fabric_type,
            "avg_query_time_ms": avg_query_time,
            "storage_used_mb": self.metrics["storage_used_mb"],
            "total_entries": self.metrics["total_entries"],
            "read_ops": self.metrics["read_ops"],
            "write_ops": self.metrics["write_ops"],
            "read_write_ratio": read_write_ratio,
            "last_update": self.metrics["last_update"]
        }

class OrchestratorMonitor:
    """Monitor autonomous process orchestration."""
    
    def __init__(self, orchestrator_id: str):
        self.orchestrator_id = orchestrator_id
        self.metrics = {
            "workflows_created": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "avg_completion_time_s": 0,
            "self_optimizations": 0,
            "active_workflows": 0
        }
        self.workflow_times = []
    
    def record_workflow_creation(self):
        """Record a new workflow created by the orchestrator."""
        self.metrics["workflows_created"] += 1
        self.metrics["active_workflows"] += 1
        logger.info(f"Orchestrator {self.orchestrator_id} - New workflow created. Active: {self.metrics['active_workflows']}")
    
    def record_workflow_completion(self, execution_time_s: float, optimized: bool = False):
        """Record a completed workflow."""
        self.metrics["workflows_completed"] += 1
        self.metrics["active_workflows"] -= 1
        self.workflow_times.append(execution_time_s)
        
        # Update average completion time
        self.metrics["avg_completion_time_s"] = sum(self.workflow_times[-100:]) / min(len(self.workflow_times), 100)
        
        if optimized:
            self.metrics["self_optimizations"] += 1
            
        logger.info(f"Orchestrator {self.orchestrator_id} - Workflow completed in {execution_time_s:.2f}s")
    
    def record_workflow_failure(self, error_reason: str):
        """Record a failed workflow."""
        self.metrics["workflows_failed"] += 1
        self.metrics["active_workflows"] -= 1
        logger.error(f"Orchestrator {self.orchestrator_id} - Workflow failed: {error_reason}")
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Return current orchestration metrics."""
        success_rate = 0
        if (self.metrics["workflows_completed"] + self.metrics["workflows_failed"]) > 0:
            success_rate = self.metrics["workflows_completed"] / (
                self.metrics["workflows_completed"] + self.metrics["workflows_failed"]
            )
            
        return {
            "orchestrator_id": self.orchestrator_id,
            "success_rate": success_rate,
            "avg_completion_time_s": self.metrics["avg_completion_time_s"],
            "active_workflows": self.metrics["active_workflows"],
            "total_workflows": self.metrics["workflows_created"],
            "self_optimizations": self.metrics["self_optimizations"]
        }

class AIInfrastructureMonitor:
    """Monitor AI infrastructure health and resource utilization."""
    
    def __init__(self):
        self.agents = {}  # Dictionary of agent_id -> AIAgentMonitor
        self.data_fabrics = {}  # Dictionary of fabric_id -> NeuralDataFabricMonitor
        self.orchestrators = {}  # Dictionary of orchestrator_id -> OrchestratorMonitor
        
        # Ollama integration
        self.ollama_endpoint = "http://localhost:11434"
        
    def register_agent(self, agent_id: str, agent_type: str) -> AIAgentMonitor:
        """Register a new AI agent for monitoring."""
        agent = AIAgentMonitor(agent_id, agent_type)
        self.agents[agent_id] = agent
        logger.info(f"Registered new agent: {agent_id} ({agent_type})")
        return agent
    
    def register_data_fabric(self, fabric_id: str, fabric_type: str) -> NeuralDataFabricMonitor:
        """Register a new neural data fabric component for monitoring."""
        fabric = NeuralDataFabricMonitor(fabric_id, fabric_type)
        self.data_fabrics[fabric_id] = fabric
        logger.info(f"Registered new data fabric: {fabric_id} ({fabric_type})")
        return fabric
    
    def register_orchestrator(self, orchestrator_id: str) -> OrchestratorMonitor:
        """Register a new orchestrator for monitoring."""
        orchestrator = OrchestratorMonitor(orchestrator_id)
        self.orchestrators[orchestrator_id] = orchestrator
        logger.info(f"Registered new orchestrator: {orchestrator_id}")
        return orchestrator
    
    async def get_ollama_status(self) -> Dict[str, Any]:
        """Check Ollama service health and available models."""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "available_models": [model["name"] for model in models],
                    "model_count": len(models)
                }
            else:
                return {"status": "degraded", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {str(e)}")
            return {"status": "unavailable", "error": str(e)}
    
    async def get_complete_health_report(self) -> Dict[str, Any]:
        """Generate a complete health report of the entire AI ERP system."""
        ollama_status = await self.get_ollama_status()
        
        # Collect agent statuses
        agent_statuses = [
            agent.get_health_status() for agent in self.agents.values()
        ]
        
        # Count healthy/degraded/unhealthy agents
        agent_health = {
            "total": len(agent_statuses),
            "healthy": sum(1 for a in agent_statuses if a.get("status") == "healthy"),
            "degraded": sum(1 for a in agent_statuses if a.get("status") == "degraded"),
            "unhealthy": sum(1 for a in agent_statuses if a.get("status") == "unhealthy"),
            "inactive": sum(1 for a in agent_statuses if a.get("status") == "inactive")
        }
        
        # Data fabric metrics
        fabric_metrics = [
            fabric.get_performance_metrics() for fabric in self.data_fabrics.values()
        ]
        
        # Orchestrator metrics
        orchestrator_metrics = [
            orch.get_orchestration_metrics() for orch in self.orchestrators.values()
        ]
        
        # Overall system health
        system_status = "healthy"
        if agent_health["unhealthy"] > 0 or ollama_status["status"] != "healthy":
            system_status = "degraded"
        if agent_health["unhealthy"] > agent_health["total"] * 0.25 or ollama_status["status"] == "unavailable":
            system_status = "unhealthy"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": system_status,
            "ollama": ollama_status,
            "agents": {
                "summary": agent_health,
                "details": agent_statuses
            },
            "data_fabric": fabric_metrics,
            "orchestrators": orchestrator_metrics
        }

async def sample_monitoring_flow():
    """Demo of monitoring flow with sample metrics."""
    monitor = AIInfrastructureMonitor()
    
    # Register sample components
    finance_agent = monitor.register_agent("finance-agent-1", "finance")
    hr_agent = monitor.register_agent("hr-agent-1", "hr")
    vector_db = monitor.register_data_fabric("main-vector-db", "vector_db")
    kg = monitor.register_data_fabric("enterprise-kg", "knowledge_graph")
    orchestrator = monitor.register_orchestrator("main-workflow-orchestrator")
    
    # Simulate activity
    for _ in range(10):
        # Simulate agent activity
        await finance_agent.capture_inference_time(120.5)
        finance_agent.record_token_usage(450)
        
        await hr_agent.capture_inference_time(85.3)
        hr_agent.record_token_usage(320)
        
        # Simulate one error
        if _ == 5:
            finance_agent.record_error("API_TIMEOUT", "LLM API timed out after 10s")
        
        # Simulate data fabric operations
        await vector_db.record_query_time(12.5)
        vector_db.update_storage_metrics(256.5, 15000)
        vector_db.record_write_operation()
        
        await kg.record_query_time(45.2)
        kg.update_storage_metrics(512.8, 85000)
        
        # Simulate orchestrator activity
        orchestrator.record_workflow_creation()
        if _ % 3 == 0:
            orchestrator.record_workflow_completion(35.8, optimized=True)
        else:
            orchestrator.record_workflow_completion(42.3)
        
        # Wait a bit
        await asyncio.sleep(0.2)
    
    # Generate report
    health_report = await monitor.get_complete_health_report()
    logger.info(f"System health report: {json.dumps(health_report, indent=2)}")
    
    return health_report

if __name__ == "__main__":
    print("Starting AI ERP Monitoring System...")
    asyncio.run(sample_monitoring_flow())