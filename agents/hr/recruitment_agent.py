"""
Recruitment Agent for NeuroERP.

This agent manages job requisitions, candidate tracking, resume analysis,
interview scheduling, and hiring workflows.
"""

import uuid
import time
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime, date, timedelta

from ...core.config import Config
from ...core.event_bus import EventBus
from ...core.neural_fabric import NeuralFabric
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

class RecruitmentAgent(BaseAgent):
    """AI Agent for recruitment and hiring processes."""
    
    def __init__(self, name: str = "Recruitment Agent", ai_engine=None, vector_store=None):
        """Initialize the recruitment agent.
        
        Args:
            name: Name of the agent
            ai_engine: AI engine for advanced processing
            vector_store: Vector store for semantic search
        """
        super().__init__(name=name, agent_type="hr.recruitment", ai_engine=ai_engine, vector_store=vector_store)
        
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
        self.register_skill("create_job_requisition", self.create_job_requisition)
        self.register_skill("update_job_requisition", self.update_job_requisition)
        self.register_skill("close_job_requisition", self.close_job_requisition)
        self.register_skill("add_candidate", self.add_candidate)
        self.register_skill("update_candidate", self.update_candidate)
        self.register_skill("analyze_resume", self.analyze_resume)
        self.register_skill("schedule_interview", self.schedule_interview)
        self.register_skill("record_interview_feedback", self.record_interview_feedback)
        self.register_skill("make_offer", self.make_offer)
        self.register_skill("process_offer_response", self.process_offer_response)
        self.register_skill("search_candidates", self.search_candidates)
        self.register_skill("generate_recruitment_report", self.generate_recruitment_report)
    
    def _subscribe_to_events(self):
        """Subscribe to relevant system events."""
        self.event_bus.subscribe("job.requisition.created", self._handle_new_requisition)
        self.event_bus.subscribe("candidate.added", self._handle_new_candidate)
        self.event_bus.subscribe("interview.scheduled", self._handle_interview_scheduled)
        self.event_bus.subscribe("interview.completed", self._handle_interview_completed)
        self.event_bus.subscribe("offer.accepted", self._handle_offer_accepted)
        self.event_bus.subscribe("offer.declined", self._handle_offer_declined)
    
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
            if action == "create_job_requisition":
                return {"success": True, "result": self.create_job_requisition(**parameters)}
            elif action == "update_job_requisition":
                return {"success": True, "result": self.update_job_requisition(**parameters)}
            elif action == "close_job_requisition":
                return {"success": True, "result": self.close_job_requisition(**parameters)}
            elif action == "add_candidate":
                return {"success": True, "result": self.add_candidate(**parameters)}
            elif action == "update_candidate":
                return {"success": True, "result": self.update_candidate(**parameters)}
            elif action == "analyze_resume":
                return {"success": True, "result": self.analyze_resume(**parameters)}
            elif action == "schedule_interview":
                return {"success": True, "result": self.schedule_interview(**parameters)}
            elif action == "record_interview_feedback":
                return {"success": True, "result": self.record_interview_feedback(**parameters)}
            elif action == "make_offer":
                return {"success": True, "result": self.make_offer(**parameters)}
            elif action == "process_offer_response":
                return {"success": True, "result": self.process_offer_response(**parameters)}
            elif action == "search_candidates":
                return {"success": True, "result": self.search_candidates(**parameters)}
            elif action == "generate_recruitment_report":
                return {"success": True, "result": self.generate_recruitment_report(**parameters)}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [skill["name"] for skill in self.skills]
                }
        except Exception as e:
            logger.error(f"Error processing {action}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def create_job_requisition(self,
                              title: str,
                              department: str,
                              job_description: str,
                              requirements: List[str],
                              salary_range: Optional[Dict[str, float]] = None,
                              location: Optional[str] = None,
                              employment_type: str = "Full-time",
                              hiring_manager_id: Optional[str] = None,
                              target_hire_date: Optional[str] = None,
                              additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new job requisition.
        
        Args:
            title: Job title
            department: Department name
            job_description: Full job description
            requirements: List of job requirements
            salary_range: Min/max salary range
            location: Job location
            employment_type: Type of employment
            hiring_manager_id: ID of hiring manager
            target_hire_date: Target date to fill position
            additional_info: Additional requisition details
            
        Returns:
            Job requisition information
        """
        # Create base requisition properties
        requisition_properties = {
            "title": title,
            "department": department,
            "job_description": job_description,
            "requirements": requirements,
            "employment_type": employment_type,
            "status": "open",
            "creation_date": datetime.now().isoformat(),
            "requisition_number": f"REQ-{int(time.time())}"
        }
        
        # Add optional properties
        if salary_range:
            requisition_properties["salary_range"] = salary_range
            
        if location:
            requisition_properties["location"] = location
            
        if hiring_manager_id:
            requisition_properties["hiring_manager_id"] = hiring_manager_id
            
            # Get hiring manager name if available
            manager_node = self.neural_fabric.get_node(hiring_manager_id)
            if manager_node and manager_node.node_type == "employee":
                manager_name = f"{manager_node.properties.get('first_name')} {manager_node.properties.get('last_name')}"
                requisition_properties["hiring_manager_name"] = manager_name
        
        if target_hire_date:
            requisition_properties["target_hire_date"] = target_hire_date
        
        # Add additional info
        if additional_info:
            for key, value in additional_info.items():
                if key not in requisition_properties:
                    requisition_properties[key] = value
        
        # Create job requisition node
        requisition_id = self.neural_fabric.create_node(
            node_type="job_requisition",
            properties=requisition_properties
        )
        
        # Connect to department
        department_nodes = self.neural_fabric.query_nodes(
            node_type="department",
            filters={"name": department}
        )
        
        if department_nodes:
            department_node = department_nodes[0]
            self.neural_fabric.connect_nodes(
                source_id=requisition_id,
                target_id=department_node.id,
                relation_type="belongs_to"
            )
        
        # Connect to hiring manager if specified
        if hiring_manager_id:
            manager_node = self.neural_fabric.get_node(hiring_manager_id)
            if manager_node and manager_node.node_type == "employee":
                self.neural_fabric.connect_nodes(
                    source_id=requisition_id,
                    target_id=hiring_manager_id,
                    relation_type="managed_by"
                )
        
        # Publish event
        self.event_bus.publish(
            event_type="job.requisition.created",
            payload={
                "requisition_id": requisition_id,
                "title": title,
                "department": department,
                "requisition_number": requisition_properties["requisition_number"]
            }
        )
        
        logger.info(f"Created job requisition: {title} (ID: {requisition_id})")
        
        # Return requisition info
        return {
            "requisition_id": requisition_id,
            "requisition_number": requisition_properties["requisition_number"],
            "title": title,
            "department": department,
            "status": "open"
        }
    
    def update_job_requisition(self,
                              requisition_id: str,
                              updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a job requisition.
        
        Args:
            requisition_id: ID of the requisition to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated requisition information
        """
        # Get requisition node
        requisition_node = self.neural_fabric.get_node(requisition_id)
        if not requisition_node or requisition_node.node_type != "job_requisition":
            raise ValueError(f"Job requisition not found with ID: {requisition_id}")
        
        # Check if updating closed requisition
        if requisition_node.properties.get("status") == "closed":
            raise ValueError(f"Cannot update closed requisition: {requisition_id}")
        
        # Update neural fabric node
        self.neural_fabric.update_node(
            node_id=requisition_id,
            properties=updates
        )
        
        # Handle hiring manager change if present
        if "hiring_manager_id" in updates:
            new_manager_id = updates["hiring_manager_id"]
            
            # Get current manager connections
            connections = self.neural_fabric.get_connected_nodes(
                node_id=requisition_id,
                relation_type="managed_by"
            )
            
            # Remove existing manager connections
            if "managed_by" in connections:
                for manager_node in connections["managed_by"]:
                    self.neural_fabric.disconnect_nodes(
                        source_id=requisition_id,
                        target_id=manager_node.id,
                        relation_type="managed_by"
                    )
            
            # Add new manager connection if valid
            if new_manager_id:
                manager_node = self.neural_fabric.get_node(new_manager_id)
                if manager_node and manager_node.node_type == "employee":
                    self.neural_fabric.connect_nodes(
                        source_id=requisition_id,
                        target_id=new_manager_id,
                        relation_type="managed_by"
                    )
                    
                    # Update manager name in properties
                    manager_name = f"{manager_node.properties.get('first_name')} {manager_node.properties.get('last_name')}"
                    self.neural_fabric.update_node(
                        node_id=requisition_id,
                        properties={"hiring_manager_name": manager_name}
                    )
        
        # Handle department change if present
        if "department" in updates:
            new_department = updates["department"]
            
            # Get current department connections
            connections = self.neural_fabric.get_connected_nodes(
                node_id=requisition_id,
                relation_type="belongs_to"
            )
            
            # Remove existing department connections
            if "belongs_to" in connections:
                for dept_node in connections["belongs_to"]:
                    if dept_node.node_type == "department":
                        self.neural_fabric.disconnect_nodes(
                            source_id=requisition_id,
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
                    source_id=requisition_id,
                    target_id=department_node.id,
                    relation_type="belongs_to"
                )
        
        # Publish event
        self.event_bus.publish(
            event_type="job.requisition.updated",
            payload={
                "requisition_id": requisition_id,
                "requisition_number": requisition_node.properties.get("requisition_number"),
                "updates": updates
            }
        )
        
        # Get updated requisition data
        updated_requisition = self.neural_fabric.get_node(requisition_id)
        
        logger.info(f"Updated job requisition ID {requisition_id} with {updates}")
        
        # Return updated info
        return {
            "requisition_id": requisition_id,
            "requisition_number": updated_requisition.properties.get("requisition_number"),
            "properties": updated_requisition.properties
        }
    
    def close_job_requisition(self,
                             requisition_id: str,
                             reason: str,
                             hire_made: bool = False,
                             hired_candidate_id: Optional[str] = None,
                             notes: Optional[str] = None) -> Dict[str, Any]:
        """Close a job requisition.
        
        Args:
            requisition_id: ID of the requisition to close
            reason: Reason for closing the requisition
            hire_made: Whether a hire was made
            hired_candidate_id: ID of the hired candidate
            notes: Additional notes on closure
            
        Returns:
            Closed requisition information
        """
        # Get requisition node
        requisition_node = self.neural_fabric.get_node(requisition_id)
        if not requisition_node or requisition_node.node_type != "job_requisition":
            raise ValueError(f"Job requisition not found with ID: {requisition_id}")
        
        # Ensure requisition is open
        if requisition_node.properties.get("status") != "open":
            raise ValueError(f"Cannot close requisition with status: {requisition_node.properties.get('status')}")
        
        # Create closure record
        closure_properties = {
            "requisition_id": requisition_id,
            "requisition_number": requisition_node.properties.get("requisition_number"),
            "reason": reason,
            "hire_made": hire_made,
            "closed_at": datetime.now().isoformat()
        }
        
        if hire_made and hired_candidate_id:
            closure_properties["hired_candidate_id"] = hired_candidate_id
            
        if notes:
            closure_properties["notes"] = notes
        
        # Create closure node
        closure_id = self.neural_fabric.create_node(
            node_type="requisition_closure",
            properties=closure_properties
        )
        
        # Connect closure to requisition
        self.neural_fabric.connect_nodes(
            source_id=closure_id,
            target_id=requisition_id,
            relation_type="closes"
        )
        
        # Update requisition status
        update_properties = {
            "status": "closed",
            "closure_reason": reason,
            "closure_date": datetime.now().isoformat(),
            "hire_made": hire_made
        }
        
        if hire_made and hired_candidate_id:
            update_properties["hired_candidate_id"] = hired_candidate_id
            
        if notes:
            update_properties["closure_notes"] = notes
        
        self.neural_fabric.update_node(
            node_id=requisition_id,
            properties=update_properties
        )
        
        # If a hire was made with a candidate, update the candidate
        if hire_made and hired_candidate_id:
            candidate_node = self.neural_fabric.get_node(hired_candidate_id)
            if candidate_node and candidate_node.node_type == "candidate":
                self.neural_fabric.update_node(
                    node_id=hired_candidate_id,
                    properties={
                        "status": "hired",
                        "hire_date": datetime.now().isoformat(),
                        "hired_for_requisition": requisition_id,
                        "hired_for_position": requisition_node.properties.get("title")
                    }
                )
                
                self.neural_fabric.connect_nodes(
                    source_id=hired_candidate_id,
                    target_id=requisition_id,
                    relation_type="hired_for"
                )
        
        # Publish event
        self.event_bus.publish(
            event_type="job.requisition.closed",
            payload={
                "requisition_id": requisition_id,
                "requisition_number": requisition_node.properties.get("requisition_number"),
                "reason": reason,
                "hire_made": hire_made,
                "hired_candidate_id": hired_candidate_id if hire_made and hired_candidate_id else None
            }
        )
        
        logger.info(f"Closed job requisition ID {requisition_id} due to {reason}")
        
        # Return closure details
        return {
            "requisition_id": requisition_id,
            "requisition_number": requisition_node.properties.get("requisition_number"),
            "closure_id": closure_id,
            "reason": reason,
            "hire_made": hire_made,
            "hired_candidate_id": hired_candidate_id if hire_made and hired_candidate_id else None,
            "status": "closed"
        }
    
    def add_candidate(self,
                     first_name: str,
                     last_name: str,
                     email: str,
                     requisition_id: str,
                     resume_text: Optional[str] = None,
                     phone: Optional[str] = None,
                     source: str = "Direct Application",
                     education: Optional[List[Dict[str, Any]]] = None,
                     experience: Optional[List[Dict[str, Any]]] = None,
                     skills: Optional[List[str]] = None,
                     additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a new candidate for a job requisition.
        
        Args:
            first_name: Candidate's first name
            last_name: Candidate's last name
            email: Candidate's email
            requisition_id: Job requisition ID
            resume_text: Full text of resume
            phone: Candidate's phone number
            source: Source of the candidate
            education: List of education details
            experience: List of work experience details
            skills: List of skills
            additional_info: Additional candidate information
            
        Returns:
            Candidate information
        """
        # Verify requisition exists and is open
        requisition_node = self.neural_fabric.get_node(requisition_id)
        if not requisition_node or requisition_node.node_type != "job_requisition":
            raise ValueError(f"Job requisition not found with ID: {requisition_id}")
        
        if requisition_node.properties.get("status") != "open":
            raise ValueError(f"Cannot add candidate to closed requisition: {requisition_id}")
        
        # Create base candidate properties
        candidate_properties = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "email": email,
            "status": "new",
            "application_date": datetime.now().isoformat(),
            "source": source,
            "requisition_id": requisition_id,
            "requisition_number": requisition_node.properties.get("requisition_number"),
            "position_applied": requisition_node.properties.get("title")
        }
        
        # Add optional properties
        if phone:
            candidate_properties["phone"] = phone
            
        if resume_text:
            candidate_properties["resume_text"] = resume_text
            
        if education:
            candidate_properties["education"] = education
            
        if experience:
            candidate_properties["experience"] = experience
            
        if skills:
            candidate_properties["skills"] = skills
        
        # Add additional info
        if additional_info:
            for key, value in additional_info.items():
                if key not in candidate_properties:
                    candidate_properties[key] = value
        
        # Create candidate node
        candidate_id = self.neural_fabric.create_node(
            node_type="candidate",
            properties=candidate_properties
        )
        
        # Connect candidate to requisition
        self.neural_fabric.connect_nodes(
            source_id=candidate_id,
            target_id=requisition_id,
            relation_type="applied_for"
        )
        
        # If resume text is provided, analyze it
        if resume_text and self.ai_engine:
            self.analyze_resume(candidate_id=candidate_id, requisition_id=requisition_id)
        
        # Publish event
        self.event_bus.publish(
            event_type="candidate.added",
            payload={
                "candidate_id": candidate_id,
                "requisition_id": requisition_id,
                "requisition_number": requisition_node.properties.get("requisition_number"),
                "candidate_name": f"{first_name} {last_name}"
            }
        )
        
        logger.info(f"Added candidate: {first_name} {last_name} (ID: {candidate_id}) for requisition {requisition_id}")
        
        # Return candidate info
        return {
            "candidate_id": candidate_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "status": "new",
            "requisition_id": requisition_id,
            "requisition_number": requisition_node.properties.get("requisition_number"),
            "position_applied": requisition_node.properties.get("title")
        }
    
    def update_candidate(self,
                        candidate_id: str,
                        updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a candidate's information.
        
        Args:
            candidate_id: ID of the candidate to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated candidate information
        """
        # Get candidate node
        candidate_node = self.neural_fabric.get_node(candidate_id)
        if not candidate_node or candidate_node.node_type != "candidate":
            raise ValueError(f"Candidate not found with ID: {candidate_id}")
        
        # Update neural fabric node
        self.neural_fabric.update_node(
            node_id=candidate_id,
            properties=updates
        )
        
        # Handle requisition change if present
        if "requisition_id" in updates:
            new_requisition_id = updates["requisition_id"]
            
            # Verify new requisition exists and is open
            new_requisition_node = self.neural_fabric.get_node(new_requisition_id)
            if not new_requisition_node or new_requisition_node.node_type != "job_requisition":
                raise ValueError(f"Job requisition not found with ID: {new_requisition_id}")
            
            if new_requisition_node.properties.get("status") != "open":
                raise ValueError(f"Cannot move candidate to closed requisition: {new_requisition_id}")
            
            # Get current requisition connections
            connections = self.neural_fabric.get_connected_nodes(
                node_id=candidate_id,
                relation_type="applied_for"
            )
            
            # Remove existing requisition connections
            if "applied_for" in connections:
                for req_node in connections["applied_for"]:
                    self.neural_fabric.disconnect_nodes(
                        source_id=candidate_id,
                        target_id=req_node.id,
                        relation_type="applied_for"
                    )
            
            # Add new requisition connection
            self.neural_fabric.connect_nodes(
                source_id=candidate_id,
                target_id=new_requisition_id,
                relation_type="applied_for"
            )
            
            # Update requisition information in properties
            additional_updates = {
                "requisition_id": new_requisition_id,
                "requisition_number": new_requisition_node.properties.get("requisition_number"),
                "position_applied": new_requisition_node.properties.get("title")
            }
            
            self.neural_fabric.update_node(
                node_id=candidate_id,
                properties=additional_updates
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="candidate.updated",
            payload={
                "candidate_id": candidate_id,
                "updates": updates
            }
        )
        
        # Get updated candidate data
        updated_candidate = self.neural_fabric.get_node(candidate_id)
        
        logger.info(f"Updated candidate ID {candidate_id} with {updates}")
        
        # Return updated info
        return {
            "candidate_id": candidate_id,
            "properties": updated_candidate.properties
        }
    
    def analyze_resume(self,
                      candidate_id: str,
                      requisition_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a candidate's resume against job requirements.
        
        Args:
            candidate_id: ID of the candidate
            requisition_id: Optional requisition ID to compare against
            
        Returns:
            Analysis results
        """
        if not self.ai_engine:
            raise ValueError("AI engine is required for resume analysis")
        
        # Get candidate node
        candidate_node = self.neural_fabric.get_node(candidate_id)
        if not candidate_node or candidate_node.node_type != "candidate":
            raise ValueError(f"Candidate not found with ID: {candidate_id}")
        
        # Ensure resume text is available
        resume_text = candidate_node.properties.get("resume_text")
        if not resume_text:
            raise ValueError(f"Resume text not found for candidate: {candidate_id}")
        
        # If requisition ID not provided, use the one from candidate
        if not requisition_id:
            requisition_id = candidate_node.properties.get("requisition_id")
            if not requisition_id:
                raise ValueError(f"No requisition ID found for candidate: {candidate_id}")
        
        # Get requisition node
        requisition_node = self.neural_fabric.get_node(requisition_id)
        if not requisition_node or requisition_node.node_type != "job_requisition":
            raise ValueError(f"Job requisition not found with ID: {requisition_id}")
        
        # Extract job requirements
        job_title = requisition_node.properties.get("title", "")
        job_description = requisition_node.properties.get("job_description", "")
        requirements = requisition_node.properties.get("requirements", [])
        
        # Build prompt for AI analysis
        prompt = f"""
Analyze the following resume for the position of {job_title}:

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

KEY REQUIREMENTS:
{', '.join(requirements)}

Please provide:
1. Skills extracted from the resume
2. Relevant experience extracted from the resume
3. Education details extracted from the resume
4. Match score (0-100) against job requirements
5. Key strengths for this position
6. Key gaps or missing requirements
7. Overall assessment and recommendation

Format your response as a structured JSON object with these fields.
"""
        
        # Generate analysis using AI
        analysis_text = self.ai_engine.get_agent_response(
            agent_type="hr",
            prompt=prompt,
            context={"resume_analysis": True}
        )
        
        # Parse JSON from AI response
        try:
            # Extract JSON part from possibly larger text
            json_match = re.search(r'(\{[\s\S]*\})', analysis_text)
            if json_match:
                analysis_json = json.loads(json_match.group(1))
            else:
                # Fallback: try to parse the entire text as JSON
                analysis_json = json.loads(analysis_text)
                
        except json.JSONDecodeError:
            # If parsing fails, create a basic structure with the raw text
            analysis_json = {
                "raw_analysis": analysis_text,
                "match_score": 0,
                "recommendation": "Unable to parse structured analysis"
            }
        
        # Create analysis record
        analysis_properties = {
            "candidate_id": candidate_id,
            "requisition_id": requisition_id,
            "analysis_date": datetime.now().isoformat(),
            "analysis_results": analysis_json
        }
        
        # Add match score if available
        if "match_score" in analysis_json:
            analysis_properties["match_score"] = analysis_json["match_score"]
        
        # Add recommendation if available
        if "recommendation" in analysis_json:
            analysis_properties["recommendation"] = analysis_json["recommendation"]
        
        # Create analysis node
        analysis_id = self.neural_fabric.create_node(
            node_type="resume_analysis",
            properties=analysis_properties
        )
        
        # Connect analysis to candidate
        self.neural_fabric.connect_nodes(
            source_id=analysis_id,
            target_id=candidate_id,
            relation_type="analyzes"
        )
        
        # Connect analysis to requisition
        self.neural_fabric.connect_nodes(
            source_id=analysis_id,
            target_id=requisition_id,
            relation_type="analyzes_for"
        )
        
        # Update candidate with extracted information
        candidate_updates = {
            "has_analysis": True,
            "last_analysis_id": analysis_id,
            "match_score": analysis_properties.get("match_score")
        }
        
        # Add extracted skills if available
        if "skills" in analysis_json:
            candidate_updates["extracted_skills"] = analysis_json["skills"]
        
        # Add extracted experience if available
        if "experience" in analysis_json:
            candidate_updates["extracted_experience"] = analysis_json["experience"]
        
        # Add extracted education if available
        if "education" in analysis_json:
            candidate_updates["extracted_education"] = analysis_json["education"]
        
        self.neural_fabric.update_node(
            node_id=candidate_id,
            properties=candidate_updates
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="resume.analyzed",
            payload={
                "candidate_id": candidate_id,
                "requisition_id": requisition_id,
                "analysis_id": analysis_id,
                "match_score": analysis_properties.get("match_score")
            }
        )
        
        logger.info(f"Analyzed resume for candidate ID {candidate_id} against requisition {requisition_id}")
        
        # Return analysis results
        return {
            "candidate_id": candidate_id,
            "requisition_id": requisition_id,
            "analysis_id": analysis_id,
            "match_score": analysis_properties.get("match_score"),
            "analysis_results": analysis_json
        }
    
    def schedule_interview(self,
                          candidate_id: str,
                          interview_type: str,
                          scheduled_date: str,
                          scheduled_time: str,
                          duration_minutes: int = 60,
                          interviewers: Optional[List[str]] = None,
                          location: Optional[str] = None,
                          virtual_meeting_link: Optional[str] = None,
                          notes: Optional[str] = None) -> Dict[str, Any]:
        """Schedule an interview for a candidate.
        
        Args:
            candidate_id: ID of the candidate
            interview_type: Type of interview (phone, technical, onsite, etc.)
            scheduled_date: Interview date (YYYY-MM-DD)
            scheduled_time: Interview time (HH:MM)
            duration_minutes: Duration in minutes
            interviewers: List of interviewer employee IDs
            location: Physical location for the interview
            virtual_meeting_link: Link for virtual interviews
            notes: Additional interview notes
            
        Returns:
            Interview details
        """
        # Get candidate node
        candidate_node = self.neural_fabric.get_node(candidate_id)
        if not candidate_node or candidate_node.node_type != "candidate":
            raise ValueError(f"Candidate not found with ID: {candidate_id}")
        
        # Parse scheduled date and time
        try:
            scheduled_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(f"Invalid date/time format. Expected YYYY-MM-DD and HH:MM")
        
        # Create interview properties
        interview_properties = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_node.properties.get("full_name"),
            "requisition_id": candidate_node.properties.get("requisition_id"),
            "position": candidate_node.properties.get("position_applied"),
            "interview_type": interview_type,
            "scheduled_date": scheduled_date,
            "scheduled_time": scheduled_time,
            "scheduled_datetime": scheduled_datetime.isoformat(),
            "duration_minutes": duration_minutes,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        if interviewers:
            interview_properties["interviewers"] = interviewers
            
            # Add interviewer names if available
            interviewer_names = []
            for interviewer_id in interviewers:
                interviewer_node = self.neural_fabric.get_node(interviewer_id)
                if interviewer_node and interviewer_node.node_type == "employee":
                    name = f"{interviewer_node.properties.get('first_name')} {interviewer_node.properties.get('last_name')}"
                    interviewer_names.append(name)
            
            if interviewer_names:
                interview_properties["interviewer_names"] = interviewer_names
        
        if location:
            interview_properties["location"] = location
            
        if virtual_meeting_link:
            interview_properties["virtual_meeting_link"] = virtual_meeting_link
            
        if notes:
            interview_properties["notes"] = notes
        
        # Create interview node
        interview_id = self.neural_fabric.create_node(
            node_type="interview",
            properties=interview_properties
        )
        
        # Connect interview to candidate
        self.neural_fabric.connect_nodes(
            source_id=interview_id,
            target_id=candidate_id,
            relation_type="interviews"
        )
        
        # Connect interview to requisition
        requisition_id = candidate_node.properties.get("requisition_id")
        if requisition_id:
            self.neural_fabric.connect_nodes(
                source_id=interview_id,
                target_id=requisition_id,
                relation_type="interviews_for"
            )
        
        # Connect interview to interviewers
        if interviewers:
            for interviewer_id in interviewers:
                interviewer_node = self.neural_fabric.get_node(interviewer_id)
                if interviewer_node and interviewer_node.node_type == "employee":
                    self.neural_fabric.connect_nodes(
                        source_id=interview_id,
                        target_id=interviewer_id,
                        relation_type="conducted_by"
                    )
        
        # Update candidate status if this is their first interview
        candidate_interviews = self.neural_fabric.get_connected_nodes(
            node_id=candidate_id,
            relation_type="interviews_inverse"
        )
        
        if "interviews_inverse" not in candidate_interviews or len(candidate_interviews["interviews_inverse"]) == 1:
            self.neural_fabric.update_node(
                node_id=candidate_id,
                properties={"status": "interviewing"}
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="interview.scheduled",
            payload={
                "interview_id": interview_id,
                "candidate_id": candidate_id,
                "requisition_id": candidate_node.properties.get("requisition_id"),
                "interview_type": interview_type,
                "scheduled_datetime": scheduled_datetime.isoformat(),
                "candidate_name": candidate_node.properties.get("full_name")
            }
        )
        
        logger.info(f"Scheduled {interview_type} interview for candidate ID {candidate_id}")
        
        # Return interview details
        return {
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "interview_type": interview_type,
            "scheduled_date": scheduled_date,
            "scheduled_time": scheduled_time,
            "duration_minutes": duration_minutes,
            "status": "scheduled"
        }
    
    def record_interview_feedback(self,
                                 interview_id: str,
                                 feedback: Dict[str, Any],
                                 overall_rating: float,
                                 recommendation: str,
                                 submitted_by: str) -> Dict[str, Any]:
        """Record feedback for an interview.
        
        Args:
            interview_id: ID of the interview
            feedback: Detailed feedback by category
            overall_rating: Overall rating (0-5)
            recommendation: Hiring recommendation
            submitted_by: ID of employee submitting feedback
            
        Returns:
            Feedback details
        """
        # Get interview node
        interview_node = self.neural_fabric.get_node(interview_id)
        if not interview_node or interview_node.node_type != "interview":
            raise ValueError(f"Interview not found with ID: {interview_id}")
        
        # Verify interviewer
        interviewers = interview_node.properties.get("interviewers", [])
        if submitted_by not in interviewers:
            logger.warning(f"Feedback submitted by {submitted_by} who is not a listed interviewer")
        
        # Get interviewer name
        interviewer_name = submitted_by
        interviewer_node = self.neural_fabric.get_node(submitted_by)
        if interviewer_node and interviewer_node.node_type == "employee":
            interviewer_name = f"{interviewer_node.properties.get('first_name')} {interviewer_node.properties.get('last_name')}"
        
        # Create feedback properties
        feedback_properties = {
            "interview_id": interview_id,
            "interview_type": interview_node.properties.get("interview_type"),
            "candidate_id": interview_node.properties.get("candidate_id"),
            "requisition_id": interview_node.properties.get("requisition_id"),
            "detailed_feedback": feedback,
            "overall_rating": overall_rating,
            "recommendation": recommendation,
            "submitted_by": submitted_by,
            "submitted_by_name": interviewer_name,
            "submitted_at": datetime.now().isoformat()
        }
        
        # Create feedback node
        feedback_id = self.neural_fabric.create_node(
            node_type="interview_feedback",
            properties=feedback_properties
        )
        
        # Connect feedback to interview
        self.neural_fabric.connect_nodes(
            source_id=feedback_id,
            target_id=interview_id,
            relation_type="feedback_for"
        )
        
        # Connect feedback to candidate
        candidate_id = interview_node.properties.get("candidate_id")
        self.neural_fabric.connect_nodes(
            source_id=feedback_id,
            target_id=candidate_id,
            relation_type="feedback_on"
        )
        
        # Connect feedback to interviewer
        self.neural_fabric.connect_nodes(
            source_id=feedback_id,
            target_id=submitted_by,
            relation_type="submitted_by"
        )
        
        # Update interview status
        self.neural_fabric.update_node(
            node_id=interview_id,
            properties={
                "status": "completed",
                "has_feedback": True,
                "last_feedback_id": feedback_id,
                "overall_rating": overall_rating,
                "recommendation": recommendation
            }
        )
        
        # Update candidate aggregate feedback
        candidate_node = self.neural_fabric.get_node(candidate_id)
        if candidate_node:
            # Get all feedback for this candidate
            all_feedback = []
            
            # Get connected interviews
            interviews = self.neural_fabric.get_connected_nodes(
                node_id=candidate_id,
                relation_type="interviews_inverse"
            )
            
            if "interviews_inverse" in interviews:
                for interview in interviews["interviews_inverse"]:
                    # Get feedback for each interview
                    interview_feedback = self.neural_fabric.get_connected_nodes(
                        node_id=interview.id,
                        relation_type="feedback_for_inverse"
                    )
                    
                    if "feedback_for_inverse" in interview_feedback:
                        for feedback_node in interview_feedback["feedback_for_inverse"]:
                            all_feedback.append({
                                "feedback_id": feedback_node.id,
                                "interview_type": feedback_node.properties.get("interview_type"),
                                "overall_rating": feedback_node.properties.get("overall_rating"),
                                "recommendation": feedback_node.properties.get("recommendation"),
                                "submitted_by": feedback_node.properties.get("submitted_by_name"),
                                "submitted_at": feedback_node.properties.get("submitted_at")
                            })
            
            # Calculate average rating
            if all_feedback:
                ratings = [f.get("overall_rating") for f in all_feedback if f.get("overall_rating") is not None]
                avg_rating = sum(ratings) / len(ratings) if ratings else None
                
                # Count recommendations
                recommendations = {}
                for f in all_feedback:
                    rec = f.get("recommendation")
                    if rec:
                        recommendations[rec] = recommendations.get(rec, 0) + 1
                
                # Find most common recommendation
                most_common_rec = max(recommendations.items(), key=lambda x: x[1])[0] if recommendations else None
                
                # Update candidate with feedback summary
                self.neural_fabric.update_node(
                    node_id=candidate_id,
                    properties={
                        "average_rating": avg_rating,
                        "feedback_count": len(all_feedback),
                        "interview_recommendation": most_common_rec,
                        "feedback_summary": recommendations
                    }
                )
                
                # Update candidate status based on feedback if more than half interviewers submitted
                if "interviewers" in interview_node.properties:
                    total_interviewers = len(interview_node.properties["interviewers"])
                    if len(all_feedback) >= total_interviewers / 2:
                        if most_common_rec == "Hire" or most_common_rec == "Strong Hire":
                            self.neural_fabric.update_node(
                                node_id=candidate_id,
                                properties={"status": "recommended"}
                            )
                        elif most_common_rec == "Reject" or most_common_rec == "Strong Reject":
                            self.neural_fabric.update_node(
                                node_id=candidate_id,
                                properties={"status": "rejected"}
                            )
        
        # Publish event
        self.event_bus.publish(
            event_type="interview.completed",
            payload={
                "interview_id": interview_id,
                "feedback_id": feedback_id,
                "candidate_id": candidate_id,
                "overall_rating": overall_rating,
                "recommendation": recommendation
            }
        )
        
        logger.info(f"Recorded feedback for interview ID {interview_id} with rating {overall_rating}")
        
        # Return feedback details
        return {
            "feedback_id": feedback_id,
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "overall_rating": overall_rating,
            "recommendation": recommendation,
            "status": "recorded"
        }
    
    def make_offer(self,
                  candidate_id: str,
                  salary: float,
                  start_date: str,
                  expiration_date: str,
                  benefits: Optional[Dict[str, Any]] = None,
                  additional_terms: Optional[Dict[str, Any]] = None,
                  notes: Optional[str] = None) -> Dict[str, Any]:
        """Make an offer to a candidate.
        
        Args:
            candidate_id: ID of the candidate
            salary: Offered salary
            start_date: Proposed start date (YYYY-MM-DD)
            expiration_date: Offer expiration date (YYYY-MM-DD)
            benefits: Offered benefits package
            additional_terms: Additional offer terms
            notes: Additional notes about the offer
            
        Returns:
            Offer details
        """
        # Get candidate node
        candidate_node = self.neural_fabric.get_node(candidate_id)
        if not candidate_node or candidate_node.node_type != "candidate":
            raise ValueError(f"Candidate not found with ID: {candidate_id}")
        
        # Check if candidate is in appropriate status
        valid_statuses = ["interviewing", "recommended"]
        if candidate_node.properties.get("status") not in valid_statuses:
            logger.warning(f"Making offer to candidate with status: {candidate_node.properties.get('status')}")
        
        # Parse dates
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            expiration_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD")
        
        # Create offer properties
        offer_properties = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_node.properties.get("full_name"),
            "requisition_id": candidate_node.properties.get("requisition_id"),
            "position": candidate_node.properties.get("position_applied"),
            "salary": salary,
            "start_date": start_date,
            "expiration_date": expiration_date,
            "status": "extended",
            "created_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        if benefits:
            offer_properties["benefits"] = benefits
            
        if additional_terms:
            offer_properties["additional_terms"] = additional_terms
            
        if notes:
            offer_properties["notes"] = notes
        
        # Create offer node
        offer_id = self.neural_fabric.create_node(
            node_type="job_offer",
            properties=offer_properties
        )
        
        # Connect offer to candidate
        self.neural_fabric.connect_nodes(
            source_id=offer_id,
            target_id=candidate_id,
            relation_type="offered_to"
        )
        
        # Connect offer to requisition
        requisition_id = candidate_node.properties.get("requisition_id")
        if requisition_id:
            self.neural_fabric.connect_nodes(
                source_id=offer_id,
                target_id=requisition_id,
                relation_type="offer_for"
            )
        
        # Update candidate status
        self.neural_fabric.update_node(
            node_id=candidate_id,
            properties={
                "status": "offer_extended",
                "offer_id": offer_id,
                "offered_salary": salary,
                "offer_date": datetime.now().isoformat(),
                "offer_expiration": expiration_date
            }
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="offer.extended",
            payload={
                "offer_id": offer_id,
                "candidate_id": candidate_id,
                "requisition_id": requisition_id,
                "salary": salary,
                "expiration_date": expiration_date,
                "candidate_name": candidate_node.properties.get("full_name")
            }
        )
        
        logger.info(f"Extended offer to candidate ID {candidate_id} with salary {salary}")
        
        # Return offer details
        return {
            "offer_id": offer_id,
            "candidate_id": candidate_id,
            "requisition_id": requisition_id,
            "salary": salary,
            "start_date": start_date,
            "expiration_date": expiration_date,
            "status": "extended"
        }
    
    def process_offer_response(self,
                              offer_id: str,
                              accepted: bool,
                              response_date: Optional[str] = None,
                              negotiation_requests: Optional[Dict[str, Any]] = None,
                              decline_reason: Optional[str] = None,
                              notes: Optional[str] = None) -> Dict[str, Any]:
        """Process a candidate's response to an offer.
        
        Args:
            offer_id: ID of the job offer
            accepted: Whether the offer was accepted
            response_date: Date of response (defaults to today)
            negotiation_requests: Details of any negotiation requests
            decline_reason: Reason for declining the offer
            notes: Additional notes about the response
            
        Returns:
            Response details
        """
        # Get offer node
        offer_node = self.neural_fabric.get_node(offer_id)
        if not offer_node or offer_node.node_type != "job_offer":
            raise ValueError(f"Job offer not found with ID: {offer_id}")
        
        # Ensure offer is still extended
        if offer_node.properties.get("status") != "extended":
            raise ValueError(f"Cannot process response for offer with status: {offer_node.properties.get('status')}")
        
        # Process response date
        if response_date:
            try:
                response_date_obj = datetime.strptime(response_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD")
        else:
            response_date = datetime.now().date().isoformat()
        
        # Get candidate and requisition IDs
        candidate_id = offer_node.properties.get("candidate_id")
        requisition_id = offer_node.properties.get("requisition_id")
        
        # Build response properties
        response_properties = {
            "offer_id": offer_id,
            "candidate_id": candidate_id,
            "requisition_id": requisition_id,
            "accepted": accepted,
            "response_date": response_date,
            "processed_at": datetime.now().isoformat()
        }
        
        # Add optional properties
        if negotiation_requests:
            response_properties["negotiation_requests"] = negotiation_requests
            
        if decline_reason:
            response_properties["decline_reason"] = decline_reason
            
        if notes:
            response_properties["notes"] = notes
        
        # Create response node
        response_id = self.neural_fabric.create_node(
            node_type="offer_response",
            properties=response_properties
        )
        
        # Connect response to offer
        self.neural_fabric.connect_nodes(
            source_id=response_id,
            target_id=offer_id,
            relation_type="responds_to"
        )
        
        # Update offer status
        if accepted:
            new_offer_status = "accepted"
        elif negotiation_requests:
            new_offer_status = "negotiating"
        else:
            new_offer_status = "declined"
        
        self.neural_fabric.update_node(
            node_id=offer_id,
            properties={
                "status": new_offer_status,
                "response_date": response_date,
                "response_id": response_id
            }
        )
        
        # Update candidate status
        candidate_node = self.neural_fabric.get_node(candidate_id)
        if candidate_node:
            new_candidate_status = "offer_accepted" if accepted else "offer_declined"
            if negotiation_requests:
                new_candidate_status = "negotiating"
                
            self.neural_fabric.update_node(
                node_id=candidate_id,
                properties={
                    "status": new_candidate_status,
                    "offer_response_date": response_date,
                    "offer_response_id": response_id
                }
            )
            
            # If accepted, close requisition with this hire
            if accepted and requisition_id:
                self.close_job_requisition(
                    requisition_id=requisition_id,
                    reason="Position filled",
                    hire_made=True,
                    hired_candidate_id=candidate_id,
                    notes=f"Offer accepted on {response_date}"
                )
        
        # Publish event
        event_type = "offer.accepted" if accepted else "offer.declined"
        if negotiation_requests:
            event_type = "offer.negotiating"
            
        self.event_bus.publish(
            event_type=event_type,
            payload={
                "offer_id": offer_id,
                "response_id": response_id,
                "candidate_id": candidate_id,
                "requisition_id": requisition_id,
                "accepted": accepted,
                "candidate_name": offer_node.properties.get("candidate_name")
            }
        )
        
        logger.info(f"Processed response for offer ID {offer_id}: {'Accepted' if accepted else 'Declined'}")
        
        # Return response details
        return {
            "response_id": response_id,
            "offer_id": offer_id,
            "candidate_id": candidate_id,
            "requisition_id": requisition_id,
            "accepted": accepted,
            "status": new_offer_status
        }
    
    def search_candidates(self,
                         query: str,
                         filters: Optional[Dict[str, Any]] = None,
                         limit: int = 20) -> Dict[str, Any]:
        """Search for candidates based on text query and filters.
        
        Args:
            query: Text search query
            filters: Additional filters (status, skills, etc.)
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        if not self.ai_engine:
            raise ValueError("AI engine is required for semantic candidate search")
        
        # Convert query to vector if neural fabric has embedding
        query_vector = None
        if hasattr(self.neural_fabric, "text_to_vector"):
            query_vector = self.neural_fabric.text_to_vector(query)
        
        # Perform semantic search if vector available
        semantic_candidates = []
        if query_vector:
            semantic_results = self.neural_fabric.semantic_search(
                query_vector=query_vector,
                node_type="candidate",
                limit=limit * 2  # Get more for filtering
            )
            
            semantic_candidates = [result[0] for result in semantic_results]
        
        # Perform keyword-based search
        keyword_candidates = []
        
        # Search in resume text and skills
        all_candidates = self.neural_fabric.query_nodes(
            node_type="candidate",
            limit=1000  # Reasonable limit
        )
        
        query_terms = query.lower().split()
        for candidate in all_candidates:
            score = 0
            
            # Check resume text
            resume_text = candidate.properties.get("resume_text", "").lower()
            for term in query_terms:
                if term in resume_text:
                    score += 1
            
            # Check skills
            skills = candidate.properties.get("skills", [])
            extracted_skills = candidate.properties.get("extracted_skills", [])
            all_skills = skills + extracted_skills
            
            for skill in all_skills:
                if isinstance(skill, str):
                    skill_text = skill.lower()
                    for term in query_terms:
                        if term in skill_text:
                            score += 2  # Skills match is more important
            
            # Check experience
            experience = candidate.properties.get("experience", [])
            extracted_experience = candidate.properties.get("extracted_experience", [])
            
            for exp in experience + extracted_experience:
                if isinstance(exp, dict):
                    exp_text = json.dumps(exp).lower()
                elif isinstance(exp, str):
                    exp_text = exp.lower()
                else:
                    continue
                    
                for term in query_terms:
                    if term in exp_text:
                        score += 1
            
            if score > 0:
                keyword_candidates.append((candidate, score))
        
        # Sort keyword results by score
        keyword_candidates.sort(key=lambda x: x[1], reverse=True)
        keyword_candidates = [c[0] for c in keyword_candidates[:limit]]
        
        # Combine results (remove duplicates)
        combined_candidates = []
        seen_ids = set()
        
        for candidate in semantic_candidates + keyword_candidates:
            if candidate.id not in seen_ids:
                combined_candidates.append(candidate)
                seen_ids.add(candidate.id)
                
                if len(combined_candidates) >= limit:
                    break
        
        # Apply filters if provided
        if filters:
            filtered_candidates = []
            for candidate in combined_candidates:
                match = True
                
                for key, value in filters.items():
                    # Handle special filter cases
                    if key == "skills" and isinstance(value, list):
                        # Skills filter: Check if candidate has any of the required skills
                        candidate_skills = candidate.properties.get("skills", []) + candidate.properties.get("extracted_skills", [])
                        candidate_skills = [s.lower() if isinstance(s, str) else "" for s in candidate_skills]
                        filter_skills = [s.lower() for s in value]
                        
                        if not any(fs in cs for fs in filter_skills for cs in candidate_skills):
                            match = False
                            break
                    elif key == "experience_years" and isinstance(value, (int, float)):
                        # Experience years filter
                        experience = candidate.properties.get("experience", [])
                        total_years = sum(exp.get("years", 0) for exp in experience if isinstance(exp, dict))
                        
                        if total_years < value:
                            match = False
                            break
                    elif key == "status" and value:
                        # Status filter
                        if candidate.properties.get("status") != value:
                            match = False
                            break
                    elif key == "match_score" and isinstance(value, (int, float)):
                        # Match score filter
                        if (candidate.properties.get("match_score") or 0) < value:
                            match = False
                            break
                    else:
                        # Standard property filter
                        if candidate.properties.get(key) != value:
                            match = False
                            break
                
                if match:
                    filtered_candidates.append(candidate)
            
            candidates = filtered_candidates
        else:
            candidates = combined_candidates
        
        # Format results
        results = []
        for candidate in candidates:
            results.append({
                "candidate_id": candidate.id,
                "name": candidate.properties.get("full_name"),
                "email": candidate.properties.get("email"),
                "status": candidate.properties.get("status"),
                "position_applied": candidate.properties.get("position_applied"),
                "match_score": candidate.properties.get("match_score"),
                "skills": candidate.properties.get("skills", []) + candidate.properties.get("extracted_skills", []),
                "application_date": candidate.properties.get("application_date")
            })
        
        logger.info(f"Searched candidates with query '{query}' and found {len(results)} matches")
        
        return {
            "query": query,
            "filters": filters,
            "count": len(results),
            "results": results
        }
    
    def generate_recruitment_report(self,
                                   report_type: str,
                                   filters: Optional[Dict[str, Any]] = None,
                                   group_by: Optional[List[str]] = None,
                                   time_period: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate recruitment analytics report.
        
        Args:
            report_type: Type of report (requisition, candidate, hiring, etc.)
            filters: Criteria to filter data
            group_by: Fields to group results by
            time_period: Date range for the report
            
        Returns:
            Report data
        """
        # Set default parameters
        if group_by is None:
            if report_type == "requisition":
                group_by = ["department", "status"]
            elif report_type == "candidate":
                group_by = ["status"]
            else:
                group_by = []
        
        if time_period is None:
            # Default to last 90 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            time_period = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        
        # Build report data based on report type
        if report_type == "requisition":
            return self._generate_requisition_report(filters, group_by, time_period)
        elif report_type == "candidate":
            return self._generate_candidate_report(filters, group_by, time_period)
        elif report_type == "hiring":
            return self._generate_hiring_report(filters, group_by, time_period)
        elif report_type == "time_to_fill":
            return self._generate_time_to_fill_report(filters, group_by, time_period)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def _generate_requisition_report(self, filters, group_by, time_period):
        """Generate requisition analysis report."""
        # Query requisitions
        requisition_nodes = self.neural_fabric.query_nodes(
            node_type="job_requisition",
            limit=1000  # Reasonable limit
        )
        
        # Filter by time period
        start_date = datetime.fromisoformat(time_period["start_date"])
        end_date = datetime.fromisoformat(time_period["end_date"])
        
        filtered_requisitions = []
        for req in requisition_nodes:
            creation_date = req.properties.get("creation_date")
            if creation_date:
                try:
                    req_date = datetime.fromisoformat(creation_date)
                    if start_date <= req_date <= end_date:
                        filtered_requisitions.append(req)
                except (ValueError, TypeError):
                    pass
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                filtered_requisitions = [r for r in filtered_requisitions if r.properties.get(key) == value]
        
        # Group requisitions according to group_by fields
        def group_data(data, group_fields):
            """Recursively group data by fields."""
            if not group_fields:
                return data
                
            current_field = group_fields[0]
            remaining_fields = group_fields[1:]
            
            grouped = {}
            for item in data:
                key = item.properties.get(current_field, "Unknown")
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(item)
            
            if not remaining_fields:
                return grouped
                
            return {key: group_data(items, remaining_fields) for key, items in grouped.items()}
        
        grouped_data = group_data(filtered_requisitions, group_by)
        
        # Calculate metrics for each group
        def calculate_metrics(reqs):
            """Calculate metrics for a list of requisitions."""
            total = len(reqs)
            open_count = sum(1 for r in reqs if r.properties.get("status") == "open")
            closed_count = sum(1 for r in reqs if r.properties.get("status") == "closed")
            
            filled_count = sum(1 for r in reqs 
                             if r.properties.get("status") == "closed" 
                             and r.properties.get("hire_made", False))
            
            fill_rate = (filled_count / closed_count * 100) if closed_count > 0 else 0
            
            # Calculate average time to fill for filled positions
            time_to_fill_days = []
            for req in reqs:
                if req.properties.get("status") == "closed" and req.properties.get("hire_made", False):
                    creation_date = req.properties.get("creation_date")
                    closure_date = req.properties.get("closure_date")
                    
                    if creation_date and closure_date:
                        try:
                            c_date = datetime.fromisoformat(creation_date)
                            cl_date = datetime.fromisoformat(closure_date)
                            days = (cl_date - c_date).days
                            time_to_fill_days.append(days)
                        except (ValueError, TypeError):
                            pass
            
            avg_time_to_fill = sum(time_to_fill_days) / len(time_to_fill_days) if time_to_fill_days else None
            
            return {
                "total": total,
                "open": open_count,
                "closed": closed_count,
                "filled": filled_count,
                "fill_rate": fill_rate,
                "avg_time_to_fill_days": avg_time_to_fill
            }
        
        # Process grouped data recursively
        def process_groups(data, path=None):
            if path is None:
                path = []
                
            result = {}
            
            if isinstance(data, list):  # Leaf node with requisitions
                return calculate_metrics(data)
            else:  # Nested group
                for key, value in data.items():
                    result[key] = process_groups(value, path + [key])
                    
                return result
        
        processed_data = process_groups(grouped_data)
        
        # Calculate overall metrics
        overall_metrics = calculate_metrics(filtered_requisitions)
        
        # Prepare report
        report = {
            "report_type": "requisition",
            "time_period": time_period,
            "overall_metrics": overall_metrics,
            "grouped_data": processed_data,
            "total_requisitions": len(filtered_requisitions)
        }
        
        logger.info(f"Generated requisition report with {len(filtered_requisitions)} requisitions")
        
        return report
    
    def _generate_candidate_report(self, filters, group_by, time_period):
        """Generate candidate analysis report."""
        # Query candidates
        candidate_nodes = self.neural_fabric.query_nodes(
            node_type="candidate",
            limit=1000  # Reasonable limit
        )
        
        # Filter by time period
        start_date = datetime.fromisoformat(time_period["start_date"])
        end_date = datetime.fromisoformat(time_period["end_date"])
        
        filtered_candidates = []
        for candidate in candidate_nodes:
            application_date = candidate.properties.get("application_date")
            if application_date:
                try:
                    app_date = datetime.fromisoformat(application_date)
                    if start_date <= app_date <= end_date:
                        filtered_candidates.append(candidate)
                except (ValueError, TypeError):
                    pass
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                filtered_candidates = [c for c in filtered_candidates if c.properties.get(key) == value]
        
        # Group candidates according to group_by fields
        def group_data(data, group_fields):
            """Recursively group data by fields."""
            if not group_fields:
                return data
                
            current_field = group_fields[0]
            remaining_fields = group_fields[1:]
            
            grouped = {}
            for item in data:
                key = item.properties.get(current_field, "Unknown")
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(item)
            
            if not remaining_fields:
                return grouped
                
            return {key: group_data(items, remaining_fields) for key, items in grouped.items()}
        
        grouped_data = group_data(filtered_candidates, group_by)
        
        # Calculate metrics for each group
        def calculate_metrics(candidates):
            """Calculate metrics for a list of candidates."""
            total = len(candidates)
            
            # Status breakdown
            status_counts = {}
            for c in candidates:
                status = c.properties.get("status", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Source breakdown
            source_counts = {}
            for c in candidates:
                source = c.properties.get("source", "Unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
            
            # Calculate average match score
            match_scores = [c.properties.get("match_score") for c in candidates if c.properties.get("match_score") is not None]
            avg_match_score = sum(match_scores) / len(match_scores) if match_scores else None
            
            # Calculate interview to offer ratio
            interviewed_count = sum(1 for c in candidates if c.properties.get("status") in ["interviewing", "offer_extended", "offer_accepted", "hired"])
            offered_count = sum(1 for c in candidates if c.properties.get("status") in ["offer_extended", "offer_accepted", "hired"])
            
            interview_to_offer_ratio = (offered_count / interviewed_count) if interviewed_count > 0 else 0
            
            # Calculate offer acceptance rate
            accepted_count = sum(1 for c in candidates if c.properties.get("status") in ["offer_accepted", "hired"])
            
            offer_acceptance_rate = (accepted_count / offered_count) if offered_count > 0 else 0
            
            return {
                "total": total,
                "status_breakdown": status_counts,
                "source_breakdown": source_counts,
                "avg_match_score": avg_match_score,
                "interviewed_count": interviewed_count,
                "offered_count": offered_count,
                "accepted_count": accepted_count,
                "interview_to_offer_ratio": interview_to_offer_ratio,
                "offer_acceptance_rate": offer_acceptance_rate
            }
        
        # Process grouped data recursively
        def process_groups(data, path=None):
            if path is None:
                path = []
                
            result = {}
            
            if isinstance(data, list):  # Leaf node with candidates
                return calculate_metrics(data)
            else:  # Nested group
                for key, value in data.items():
                    result[key] = process_groups(value, path + [key])
                    
                return result
        
        processed_data = process_groups(grouped_data)
        
        # Calculate overall metrics
        overall_metrics = calculate_metrics(filtered_candidates)
        
        # Prepare report
        report = {
            "report_type": "candidate",
            "time_period": time_period,
            "overall_metrics": overall_metrics,
            "grouped_data": processed_data,
            "total_candidates": len(filtered_candidates)
        }
        
        logger.info(f"Generated candidate report with {len(filtered_candidates)} candidates")
        
        return report
    
    def _generate_hiring_report(self, filters, group_by, time_period):
        """Generate hiring metrics report."""
        # Similar implementation to candidate report but focusing on hires
        # Simplified implementation for now
        candidate_report = self._generate_candidate_report(filters, group_by, time_period)
        
        # Focus on hired candidates
        hired_count = candidate_report["overall_metrics"]["status_breakdown"].get("hired", 0)
        offered_count = candidate_report["overall_metrics"]["offered_count"]
        total_candidates = candidate_report["total_candidates"]
        
        hiring_rate = (hired_count / total_candidates * 100) if total_candidates > 0 else 0
        
        hiring_report = {
            "report_type": "hiring",
            "time_period": time_period,
            "overall_metrics": {
                "total_candidates": total_candidates,
                "hired_count": hired_count,
                "offered_count": offered_count,
                "hiring_rate": hiring_rate,
                "offer_to_hire_rate": (hired_count / offered_count * 100) if offered_count > 0 else 0
            },
            "grouped_data": candidate_report["grouped_data"]
        }
        
        logger.info(f"Generated hiring report with {hired_count} hires")
        
        return hiring_report
    
    def _generate_time_to_fill_report(self, filters, group_by, time_period):
        """Generate time-to-fill metrics report."""
        # Query requisitions that were filled
        requisition_nodes = self.neural_fabric.query_nodes(
            node_type="job_requisition",
            filters={"status": "closed", "hire_made": True},
            limit=1000
        )
        
        # Filter by time period (using closure date)
        start_date = datetime.fromisoformat(time_period["start_date"])
        end_date = datetime.fromisoformat(time_period["end_date"])
        
        filtered_requisitions = []
        for req in requisition_nodes:
            closure_date = req.properties.get("closure_date")
            if closure_date:
                try:
                    cl_date = datetime.fromisoformat(closure_date)
                    if start_date <= cl_date <= end_date:
                        filtered_requisitions.append(req)
                except (ValueError, TypeError):
                    pass
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                filtered_requisitions = [r for r in filtered_requisitions if r.properties.get(key) == value]
        
        # Calculate time-to-fill for each requisition
        time_to_fill_data = []
        for req in filtered_requisitions:
            creation_date = req.properties.get("creation_date")
            closure_date = req.properties.get("closure_date")
            
            if creation_date and closure_date:
                try:
                    c_date = datetime.fromisoformat(creation_date)
                    cl_date = datetime.fromisoformat(closure_date)
                    days = (cl_date - c_date).days
                    
                    time_to_fill_data.append({
                        "requisition_id": req.id,
                        "requisition_number": req.properties.get("requisition_number"),
                        "department": req.properties.get("department"),
                        "title": req.properties.get("title"),
                        "days_to_fill": days
                    })
                except (ValueError, TypeError):
                    pass
        
        # Group data if needed
        grouped_data = {}
        if group_by:
            for ttf in time_to_fill_data:
                for field in group_by:
                    key = ttf.get(field, "Unknown")
                    if key not in grouped_data:
                        grouped_data[key] = []
                    grouped_data[key].append(ttf)
        
        # Calculate metrics
        def calculate_ttf_metrics(ttf_list):
            """Calculate time-to-fill metrics for a list of requisitions."""
            if not ttf_list:
                return {"count": 0}
                
            days_list = [item["days_to_fill"] for item in ttf_list]
            
            return {
                "count": len(ttf_list),
                "avg_days_to_fill": sum(days_list) / len(days_list),
                "min_days": min(days_list),
                "max_days": max(days_list),
                "median_days": sorted(days_list)[len(days_list) // 2] if days_list else None
            }
        
        # Process overall metrics
        overall_metrics = calculate_ttf_metrics(time_to_fill_data)
        
        # Process grouped metrics
        grouped_metrics = {}
        for key, items in grouped_data.items():
            grouped_metrics[key] = calculate_ttf_metrics(items)
        
        # Prepare report
        report = {
            "report_type": "time_to_fill",
            "time_period": time_period,
            "overall_metrics": overall_metrics,
            "grouped_metrics": grouped_metrics,
            "total_filled_requisitions": len(time_to_fill_data)
        }
        
        logger.info(f"Generated time-to-fill report with {len(time_to_fill_data)} filled requisitions")
        
        return report
    
    # Event handlers
    def _handle_new_requisition(self, event):
        """Handle creation of new job requisition."""
        requisition_id = event.payload.get("requisition_id")
        if not requisition_id:
            return
            
        logger.info(f"Handling new requisition event for ID {requisition_id}")
        
        # Could add automated actions here, such as:
        # - Posting job to job boards
        # - Notifying recruiting team
        # - Searching for matching candidates in database
    
    def _handle_new_candidate(self, event):
        """Handle addition of new candidate."""
        candidate_id = event.payload.get("candidate_id")
        requisition_id = event.payload.get("requisition_id")
        if not candidate_id:
            return
            
        logger.info(f"Handling new candidate event for ID {candidate_id}")
        
        # Automatically analyze resume if AI engine is available
        if self.ai_engine:
            try:
                candidate_node = self.neural_fabric.get_node(candidate_id)
                if candidate_node and candidate_node.properties.get("resume_text"):
                    self.analyze_resume(candidate_id=candidate_id, requisition_id=requisition_id)
            except Exception as e:
                logger.error(f"Error analyzing resume for candidate {candidate_id}: {e}")
    
    def _handle_interview_scheduled(self, event):
        """Handle interview scheduling."""
        interview_id = event.payload.get("interview_id")
        candidate_id = event.payload.get("candidate_id")
        if not interview_id or not candidate_id:
            return
            
        logger.info(f"Handling interview scheduled event for ID {interview_id}")
        
        # Could add automated actions here, such as:
        # - Sending calendar invites
        # - Preparing interview materials
        # - Sending reminders to interviewers
    
    def _handle_interview_completed(self, event):
        """Handle interview completion."""
        interview_id = event.payload.get("interview_id")
        candidate_id = event.payload.get("candidate_id")
        recommendation = event.payload.get("recommendation")
        if not interview_id or not candidate_id:
            return
            
        logger.info(f"Handling interview completion event for ID {interview_id}")
        
        # Check if all interviews are complete and recommendation is to hire
        if recommendation in ["Hire", "Strong Hire"]:
            candidate_node = self.neural_fabric.get_node(candidate_id)
            if candidate_node:
                # Check if all scheduled interviews are complete
                interviews = self.neural_fabric.get_connected_nodes(
                    node_id=candidate_id,
                    relation_type="interviews_inverse"
                )
                
                all_complete = True
                if "interviews_inverse" in interviews:
                    for interview in interviews["interviews_inverse"]:
                        if interview.properties.get("status") != "completed":
                            all_complete = False
                            break
                    
                    if all_complete and candidate_node.properties.get("status") != "offer_extended":
                        # Could trigger offer generation workflow
                        logger.info(f"All interviews complete with positive recommendation for candidate {candidate_id}")
    
    def _handle_offer_accepted(self, event):
        """Handle offer acceptance."""
        offer_id = event.payload.get("offer_id")
        candidate_id = event.payload.get("candidate_id")
        requisition_id = event.payload.get("requisition_id")
        if not offer_id or not candidate_id:
            return
            
        logger.info(f"Handling offer acceptance event for ID {offer_id}")
        
        # Trigger onboarding process
        self.event_bus.publish(
            event_type="employee.onboarding.started",
            payload={
                "candidate_id": candidate_id,
                "requisition_id": requisition_id,
                "offer_id": offer_id
            }
        )
    
    def _handle_offer_declined(self, event):
        """Handle offer decline."""
        offer_id = event.payload.get("offer_id")
        candidate_id = event.payload.get("candidate_id")
        requisition_id = event.payload.get("requisition_id")
        if not offer_id or not candidate_id:
            return
            
        logger.info(f"Handling offer decline event for ID {offer_id}")
        
        # Update requisition to reflect declined offer
        if requisition_id:
            requisition_node = self.neural_fabric.get_node(requisition_id)
            if requisition_node and requisition_node.node_type == "job_requisition":
                # Check if requisition is still open
                if requisition_node.properties.get("status") == "open":
                    # Update declined offers count
                    declined_offers = requisition_node.properties.get("declined_offers", 0) + 1
                    self.neural_fabric.update_node(
                        node_id=requisition_id,
                        properties={"declined_offers": declined_offers}
                    )
                    
                    # Could trigger additional actions here
                    if declined_offers >= 3:
                        logger.warning(f"Requisition {requisition_id} has had {declined_offers} declined offers")
                        
                        # Create a review task for hiring manager and HR to reassess
                        hiring_manager_id = requisition_node.properties.get("hiring_manager_id")
                        
                        if hiring_manager_id:
                            # Create a task for hiring manager to review
                            task_properties = {
                                "title": "Review job requisition after multiple declined offers",
                                "description": f"Requisition {requisition_node.properties.get('requisition_number')} has had {declined_offers} declined offers. Please review position details, compensation, and requirements.",
                                "assigned_to": hiring_manager_id,
                                "priority": "high",
                                "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                                "status": "open",
                                "related_type": "job_requisition",
                                "related_id": requisition_id
                            }
                            
                            task_id = self.neural_fabric.create_node(
                                node_type="task",
                                properties=task_properties
                            )
                            
                            # Link task to requisition
                            self.neural_fabric.connect_nodes(
                                source_id=task_id,
                                target_id=requisition_id,
                                relation_type="related_to"
                            )
                            
                            logger.info(f"Created review task for hiring manager for requisition {requisition_id}")
                            
                            # Also notify HR team
                            self.event_bus.publish(
                                event_type="notification.created",
                                payload={
                                    "type": "hr_alert",
                                    "title": "Multiple Offer Declines",
                                    "message": f"Requisition {requisition_node.properties.get('requisition_number')} has had {declined_offers} declined offers. Consider reviewing the position details.",
                                    "context": {
                                        "requisition_id": requisition_id,
                                        "declined_offers": declined_offers
                                    },
                                    "priority": "medium"
                                }
                            )
        
        # Get the candidate details for additional processing
        candidate_node = self.neural_fabric.get_node(candidate_id)
        if candidate_node and candidate_node.node_type == "candidate":
            # Get decline reason
            offer_response = self.neural_fabric.query_nodes(
                node_type="offer_response",
                filters={"offer_id": offer_id}
            )
            
            decline_reason = None
            if offer_response:
                decline_reason = offer_response[0].properties.get("decline_reason")
            
            # Log detailed information
            logger.info(f"Candidate {candidate_node.properties.get('full_name')} declined offer. Reason: {decline_reason}")
            
            # Add decline to analytics for reporting
            decline_analytics = {
                "offer_id": offer_id,
                "candidate_id": candidate_id,
                "requisition_id": requisition_id,
                "position": requisition_node.properties.get("title") if requisition_node else "Unknown",
                "reason": decline_reason,
                "declined_at": datetime.now().isoformat()
            }
            
            analytics_id = self.neural_fabric.create_node(
                node_type="offer_decline_analytics",
                properties=decline_analytics
            )
            
            # Trigger follow-up survey if applicable
            self.event_bus.publish(
                event_type="survey.needed",
                payload={
                    "type": "offer_decline",
                    "candidate_id": candidate_id,
                    "offer_id": offer_id,
                    "email": candidate_node.properties.get("email"),
                    "name": candidate_node.properties.get("full_name")
                }
            )
            
            # Check if this is a high-priority or executive position
            if requisition_node and requisition_node.properties.get("priority") == "high":
                # Notify leadership team
                self.event_bus.publish(
                    event_type="notification.created",
                    payload={
                        "type": "exec_alert",
                        "title": "High-Priority Offer Declined",
                        "message": f"A candidate has declined an offer for the high-priority position: {requisition_node.properties.get('title')}.",
                        "priority": "high"
                    }
                )