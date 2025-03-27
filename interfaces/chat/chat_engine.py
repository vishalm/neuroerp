"""
AI-Native ERP System - Chat Engine

This module provides the core chat interface for the AI-Native ERP system.
It handles:
- User message processing
- Context management
- Conversation routing to appropriate AI agents
- Response generation
- Tool/function calling for the AI
- Memory and conversation history
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from datetime import datetime
import re
import uuid

# For vector embeddings and similarity search
import numpy as np

# Import system components
from neural_data_fabric.vector_store import VectorStore
from ai_agents.agent_base import AgentResponse

# Import prompt templates
from .prompt_templates import (
    SYSTEM_PROMPT,
    FINANCE_PROMPT,
    HR_PROMPT,
    SUPPLY_CHAIN_PROMPT,
    OPERATIONS_PROMPT,
    ROUTER_PROMPT,
    TOOL_DEFINITIONS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chat_engine")

class Message:
    """Represents a message in the conversation."""
    
    def __init__(
        self, 
        role: str,
        content: str,
        message_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.role = role  # "user", "assistant", "system", "function"
        self.content = content
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to a dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            message_id=data.get("message_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None,
            metadata=data.get("metadata", {})
        )

class Conversation:
    """Manages a conversation session with history and context."""
    
    def __init__(
        self, 
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        messages: Optional[List[Message]] = None,
        max_history: int = 50
    ):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.messages = messages or []
        self.max_history = max_history
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.metadata = {
            "domain_focus": None,  # Primary domain this conversation relates to
            "entities": {},        # Key entities mentioned in conversation
            "intent": None,        # Current user intent
            "actions_taken": [],   # Actions the system has taken
        }
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history."""
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Trim history if it exceeds max_history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get the conversation history, optionally limited to recent messages."""
        if limit is None or limit >= len(self.messages):
            return self.messages
        return self.messages[-limit:]
    
    def get_formatted_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get the conversation history formatted for LLM context."""
        history = self.get_history(limit)
        return [{"role": msg.role, "content": msg.content} for msg in history]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to a dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a conversation from a dictionary."""
        conversation = cls(
            conversation_id=data.get("conversation_id"),
            user_id=data.get("user_id"),
            messages=[Message.from_dict(msg) for msg in data.get("messages", [])]
        )
        conversation.created_at = datetime.fromisoformat(data["created_at"])
        conversation.updated_at = datetime.fromisoformat(data["updated_at"])
        conversation.metadata = data.get("metadata", {})
        return conversation
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.messages = []
        self.updated_at = datetime.now()
        self.metadata = {
            "domain_focus": None,
            "entities": {},
            "intent": None,
            "actions_taken": [],
        }

class Tool:
    """Represents a tool/function that the AI can call."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to a dictionary for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

class Agent:
    """Base class for domain-specific AI agents."""
    
    def __init__(self, name: str, system_prompt: str, model: str = "general"):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.tools = []
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool that this agent can use."""
        self.tools.append(tool)
    
    async def process(self, conversation: Conversation, message: str) -> str:
        """Process a user message and generate a response."""
        # This is a base implementation that would be overridden by specific agents
        raise NotImplementedError("Agents must implement the process method")

class AgentRouter:
    """Routes conversations to the appropriate domain-specific agent."""
    
    def __init__(self, agents: Dict[str, Agent], system_prompt: str = ROUTER_PROMPT):
        self.agents = agents
        self.system_prompt = system_prompt
    
    async def route(self, conversation: Conversation, message: str) -> str:
        """Determine which agent should handle the message."""
        # In a real implementation, this would use an LLM to analyze the message
        # and determine the appropriate domain
        
        # Simple keyword-based routing for demo purposes
        message_lower = message.lower()
        
        if any(term in message_lower for term in ['finance', 'money', 'budget', 'cost', 'revenue', 'profit']):
            return 'finance'
        elif any(term in message_lower for term in ['employee', 'hr', 'hire', 'staff', 'talent', 'training']):
            return 'hr'
        elif any(term in message_lower for term in ['inventory', 'supplier', 'ship', 'stock', 'order', 'warehouse']):
            return 'supply_chain'
        elif any(term in message_lower for term in ['production', 'machine', 'maintenance', 'quality', 'operation']):
            return 'operations'
        else:
            # Default to the agent that handled the most recent messages if available
            if conversation.metadata.get("domain_focus"):
                return conversation.metadata["domain_focus"]
            
            # Otherwise default to general
            return 'general'

class OllamaClient:
    """Client for interacting with Ollama LLM service."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def generate(
        self, 
        model: str, 
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        # In a real implementation, this would make an API call to Ollama
        # For demonstration purposes, we'll simulate the response
        
        await asyncio.sleep(1.0)  # Simulate LLM processing time
        
        # Extract the last user message
        user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        
        # Generate a mock response based on the system prompt and user message
        if system and "finance" in system.lower():
            response = f"Finance AI: Based on your financial data, I recommend optimizing your cash flow by {user_message.split()[0].lower()}ing your payment terms."
        elif system and "hr" in system.lower():
            response = f"HR AI: After analyzing employee data, I suggest focusing on improving engagement in the {user_message.split()[0].lower()} department."
        elif system and "supply" in system.lower():
            response = f"Supply Chain AI: Your inventory optimization should prioritize reducing stock levels for {user_message.split()[0].lower()} items."
        elif system and "operations" in system.lower():
            response = f"Operations AI: To improve efficiency, consider automating the {user_message.split()[0].lower()} process in your production line."
        else:
            response = f"I've analyzed your question about '{user_message.split()[0]}'. To help you better, could you provide more specific details about what you're looking for?"
        
        # Simulate tool/function call if tools are provided
        if tools and "search" in user_message.lower():
            tool_call = {
                "name": "search_documents",
                "arguments": {
                    "query": user_message,
                    "limit": 3
                }
            }
            return {
                "tool_calls": [tool_call],
                "content": None,
                "model": model,
                "usage": {
                    "prompt_tokens": 250,
                    "completion_tokens": 50,
                    "total_tokens": 300
                }
            }
        
        # Return normal text response
        return {
            "content": response,
            "model": model,
            "usage": {
                "prompt_tokens": 200,
                "completion_tokens": len(response.split()),
                "total_tokens": 200 + len(response.split())
            }
        }

class ChatEngine:
    """Core chat engine for the AI-Native ERP system."""
    
    def __init__(self):
        # Initialize LLM client
        self.llm_client = OllamaClient()
        
        # Initialize vector store for document retrieval
        self.vector_store = None  # Would be initialized with VectorStore() in production
        
        # Set up domain-specific agents
        self.agents = {
            "finance": Agent("Finance", FINANCE_PROMPT, "finance"),
            "hr": Agent("HR", HR_PROMPT, "hr"),
            "supply_chain": Agent("Supply Chain", SUPPLY_CHAIN_PROMPT, "supply_chain"),
            "operations": Agent("Operations", OPERATIONS_PROMPT, "operations"),
            "general": Agent("General", SYSTEM_PROMPT, "general")
        }
        
        # Set up agent router
        self.router = AgentRouter(self.agents)
        
        # Set up tools
        self._setup_tools()
        
        # In-memory conversation store (would be a database in production)
        self.conversations: Dict[str, Conversation] = {}
    
    def _setup_tools(self) -> None:
        """Set up the tools available to the AI agents."""
        # Document search tool
        search_tool = Tool(
            name="search_documents",
            description="Search for relevant documents in the system",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            handler=self._search_documents
        )
        
        # Data analysis tool
        analyze_tool = Tool(
            name="analyze_data",
            description="Analyze data from a specific domain",
            parameters={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain to analyze (finance, hr, etc.)"
                    },
                    "metric": {
                        "type": "string",
                        "description": "Specific metric to analyze"
                    },
                    "time_period": {
                        "type": "string",
                        "description": "Time period for analysis (e.g., 'last_30_days')"
                    }
                },
                "required": ["domain", "metric"]
            },
            handler=self._analyze_data
        )
        
        # Add tools to agents
        for agent in self.agents.values():
            agent.add_tool(search_tool)
            agent.add_tool(analyze_tool)
    
    async def _search_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for document search."""
        query = params.get("query", "")
        limit = params.get("limit", 5)
        
        # In a real implementation, this would search the vector store
        # For demonstration purposes, we'll return mock results
        await asyncio.sleep(0.5)  # Simulate search time
        
        return {
            "results": [
                {
                    "title": f"Document about {query.split()[0]}",
                    "content": f"This document contains information about {query}...",
                    "relevance": 0.92,
                    "last_updated": "2023-06-15"
                },
                {
                    "title": f"Analysis of {query.split()[0]} trends",
                    "content": f"Recent trends in {query} show significant changes...",
                    "relevance": 0.85,
                    "last_updated": "2023-05-22"
                }
            ],
            "query": query,
            "total_results": 2
        }
    
    async def _analyze_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for data analysis."""
        domain = params.get("domain", "")
        metric = params.get("metric", "")
        time_period = params.get("time_period", "last_30_days")
        
        # In a real implementation, this would analyze actual data
        # For demonstration purposes, we'll return mock results
        await asyncio.sleep(1.0)  # Simulate analysis time
        
        if domain == "finance":
            return {
                "domain": domain,
                "metric": metric,
                "time_period": time_period,
                "value": 1250000,
                "change": "+12.3%",
                "trend": "increasing",
                "analysis": f"The {metric} has shown consistent growth over the {time_period}, primarily driven by increased product adoption in the enterprise segment."
            }
        elif domain == "hr":
            return {
                "domain": domain,
                "metric": metric,
                "time_period": time_period,
                "value": 87.5,
                "change": "+2.1%",
                "trend": "stable",
                "analysis": f"Employee {metric} has remained relatively stable over the {time_period}, with slight improvements in the engineering department but decreased scores in operations."
            }
        else:
            return {
                "domain": domain,
                "metric": metric,
                "time_period": time_period,
                "value": 500,
                "change": "-5.2%",
                "trend": "decreasing",
                "analysis": f"The {metric} in {domain} has decreased over the {time_period}, potentially due to seasonal variations and market conditions."
            }
    
    def get_or_create_conversation(self, conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> Conversation:
        """Get an existing conversation or create a new one."""
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        # Create a new conversation
        conversation = Conversation(conversation_id=conversation_id, user_id=user_id)
        self.conversations[conversation.conversation_id] = conversation
        return conversation
    
    async def process_message(
        self, 
        message: str, 
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and generate a response."""
        # Get or create the conversation
        conversation = self.get_or_create_conversation(conversation_id, user_id)
        
        # Add the user message to the conversation
        user_message = Message(role="user", content=message)
        conversation.add_message(user_message)
        
        try:
            # Determine which agent should handle this message
            domain = await self.router.route(conversation, message)
            agent = self.agents[domain]
            
            # Update conversation metadata
            conversation.metadata["domain_focus"] = domain
            
            # Format the conversation history for the LLM
            formatted_history = conversation.get_formatted_history(limit=10)
            
            # Prepare tools if available
            tools = [tool.to_dict() for tool in agent.tools] if agent.tools else None
            
            # Generate response using the LLM
            response = await self.llm_client.generate(
                model=agent.model,
                messages=formatted_history,
                system=agent.system_prompt,
                tools=tools
            )
            
            # Handle tool calls if present
            if response.get("tool_calls"):
                tool_calls = response["tool_calls"]
                tool_results = []
                
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    arguments = tool_call["arguments"]
                    
                    # Find the matching tool
                    tool = next((t for t in agent.tools if t.name == tool_name), None)
                    if tool:
                        # Call the tool handler
                        tool_result = await tool.handler(arguments)
                        tool_results.append({
                            "tool_name": tool_name,
                            "result": tool_result
                        })
                        
                        # Add function message to conversation
                        function_message = Message(
                            role="function",
                            content=json.dumps(tool_result),
                            metadata={"tool_name": tool_name}
                        )
                        conversation.add_message(function_message)
                
                # Generate a new response with the tool results
                formatted_history = conversation.get_formatted_history(limit=12)
                second_response = await self.llm_client.generate(
                    model=agent.model,
                    messages=formatted_history,
                    system=agent.system_prompt,
                    tools=None  # No need for tools in the follow-up
                )
                
                response_content = second_response["content"]
                conversation.metadata["actions_taken"].append({
                    "type": "tool_usage",
                    "tools": [t["tool_name"] for t in tool_results],
                    "timestamp": datetime.now().isoformat()
                })
            else:
                response_content = response["content"]
            
            # Add the assistant's response to the conversation
            assistant_message = Message(role="assistant", content=response_content)
            conversation.add_message(assistant_message)
            
            # Return the result
            return {
                "message_id": assistant_message.message_id,
                "conversation_id": conversation.conversation_id,
                "response": response_content,
                "domain": domain,
                "timestamp": assistant_message.timestamp.isoformat(),
                "usage": response.get("usage", {})
            }
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
            # Add error response to conversation
            error_message = f"I'm sorry, I encountered an error while processing your request. Please try again or contact support if the issue persists."
            assistant_message = Message(role="assistant", content=error_message)
            conversation.add_message(assistant_message)
            
            return {
                "message_id": assistant_message.message_id,
                "conversation_id": conversation.conversation_id,
                "response": error_message,
                "error": str(e),
                "timestamp": assistant_message.timestamp.isoformat()
            }
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the conversation history for a specific conversation."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return []
        
        return [msg.to_dict() for msg in conversation.messages]
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation's history."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return False
        
        conversation.clear_history()
        return True
    
    async def save_conversations(self, file_path: str) -> bool:
        """Save all conversations to a file (for demo purposes)."""
        try:
            data = {
                conv_id: conv.to_dict() 
                for conv_id, conv in self.conversations.items()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving conversations: {str(e)}")
            return False
    
    async def load_conversations(self, file_path: str) -> bool:
        """Load conversations from a file (for demo purposes)."""
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.conversations = {
                conv_id: Conversation.from_dict(conv_data)
                for conv_id, conv_data in data.items()
            }
            
            return True
        except Exception as e:
            logger.error(f"Error loading conversations: {str(e)}")
            return False

# Example usage
async def main():
    """Example of using the ChatEngine."""
    chat_engine = ChatEngine()
    
    # Process a financial question
    finance_response = await chat_engine.process_message(
        "What's our current cash flow status?",
        user_id="example_user"
    )
    print(f"Finance response: {finance_response['response']}")
    
    # Get the conversation ID
    conversation_id = finance_response["conversation_id"]
    
    # Ask an HR question in the same conversation
    hr_response = await chat_engine.process_message(
        "How's employee satisfaction trending?",
        conversation_id=conversation_id
    )
    print(f"HR response: {hr_response['response']}")
    
    # Ask a question that would trigger tool usage
    tool_response = await chat_engine.process_message(
        "Can you search for documents about revenue forecasting?",
        conversation_id=conversation_id
    )
    print(f"Tool response: {tool_response['response']}")
    
    # Print the conversation history
    history = chat_engine.get_conversation_history(conversation_id)
    print(f"Conversation history: {json.dumps(history, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())