from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid

class BaseAgent(ABC):
    """Base class for all AI agents in the system"""
    
    def __init__(self, name: str, agent_type: str, ai_engine=None, vector_store=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.agent_type = agent_type
        self.ai_engine = ai_engine
        self.vector_store = vector_store
        self.memory = []
        self.skills = []
        
    def register_skill(self, skill_name: str, skill_function):
        """Register a skill that the agent can perform"""
        self.skills.append({
            "name": skill_name,
            "function": skill_function
        })
        
    def remember(self, information: Dict[str, Any]):
        """Store information in agent's memory"""
        self.memory.append(information)
        
    def recall(self, query: str) -> List[Dict[str, Any]]:
        """Recall relevant information from memory"""
        # Simple implementation - in practice would use vector search
        relevant_memories = []
        for memory in self.memory:
            if query.lower() in str(memory).lower():
                relevant_memories.append(memory)
        return relevant_memories
        
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results"""
        pass
        
    def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> Any:
        """Execute a registered skill"""
        for skill in self.skills:
            if skill["name"] == skill_name:
                return skill["function"](**params)
        raise ValueError(f"Skill '{skill_name}' not found")