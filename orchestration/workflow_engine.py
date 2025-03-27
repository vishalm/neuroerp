from typing import Dict, Any, List, Callable
import uuid
import time

class Workflow:
    """Represents a dynamic workflow"""
    
    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.steps = []
        self.current_step = 0
        self.status = "created"
        self.created_at = time.time()
        self.modified_at = time.time()
        self.completed_at = None
        self.results = {}
        
    def add_step(self, name: str, function: Callable, params: Dict[str, Any] = None, 
                depends_on: List[int] = None):
        """Add a step to the workflow"""
        step = {
            "id": len(self.steps),
            "name": name,
            "function": function,
            "params": params or {},
            "depends_on": depends_on or [],
            "status": "pending",
            "result": None,
            "error": None
        }
        self.steps.append(step)
        
    def execute(self):
        """Execute the workflow"""
        self.status = "running"
        
        while self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            
            # Check if dependencies are satisfied
            can_execute = True
            for dep_id in step["depends_on"]:
                if dep_id >= len(self.steps) or self.steps[dep_id]["status"] != "completed":
                    can_execute = False
                    break
                    
            if not can_execute:
                # Skip for now and try the next step
                self.current_step += 1
                continue
                
            # Execute the step
            try:
                # Prepare parameters with results from dependencies
                params = step["params"].copy()
                for dep_id in step["depends_on"]:
                    params[f"dep_{dep_id}_result"] = self.steps[dep_id]["result"]
                    
                step["result"] = step["function"](**params)
                step["status"] = "completed"
                self.results[step["name"]] = step["result"]
            except Exception as e:
                step["status"] = "failed"
                step["error"] = str(e)
                self.status = "failed"
                return False
                
            self.current_step += 1
            
        # Check if all steps completed
        if all(step["status"] == "completed" for step in self.steps):
            self.status = "completed"
            self.completed_at = time.time()
            return True
            
        self.status = "partial"
        return False

class WorkflowEngine:
    """Engine for creating and executing workflows"""
    
    def __init__(self):
        self.workflows = {}
        
    def create_workflow(self, name: str, description: str = "") -> Workflow:
        """Create a new workflow"""
        workflow = Workflow(name, description)
        self.workflows[workflow.id] = workflow
        return workflow
        
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow by ID and return results"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")
            
        workflow = self.workflows[workflow_id]
        success = workflow.execute()
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status,
            "success": success,
            "results": workflow.results
        }
        
    def generate_ai_workflow(self, ai_engine, task_description: str) -> Workflow:
        """Generate a workflow using AI based on task description"""
        # Use AI to generate workflow steps
        prompt = f"""
        Create a workflow for the following task:
        {task_description}
        
        Return the workflow as a JSON structure with steps, dependencies, and functions to call.
        """
        
        # In a real implementation, we would parse the AI response and create the workflow
        # This is a simplified placeholder
        workflow = self.create_workflow(f"AI-Generated: {task_description[:30]}...")
        
        # Add placeholder steps
        workflow.add_step("analyze_request", lambda x: x, {"input": task_description})
        workflow.add_step("process_data", lambda x: x, {"data": "sample"}, [0])
        workflow.add_step("generate_response", lambda x: x, {"processed": "data"}, [1])
        
        return workflow