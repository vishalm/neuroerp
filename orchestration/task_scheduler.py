"""
Task Scheduler for AI-Native ERP System

This module provides a decentralized, adaptive task scheduling system for orchestrating
AI agents and workflow tasks across the ERP system. It optimizes resource allocation,
manages priorities, and ensures efficient execution of business processes.
"""

import datetime
import heapq
import uuid
from typing import Dict, List, Optional, Any, Callable, Union, Set
from enum import Enum
import logging
from dataclasses import dataclass, field


class Priority(Enum):
    """Task priority levels to determine execution order."""
    CRITICAL = 0  # Immediate execution, may preempt other tasks
    HIGH = 1      # Execute ASAP but doesn't preempt
    MEDIUM = 2    # Standard priority
    LOW = 3       # Background tasks, executed when resources available
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


@dataclass(order=True)
class ScheduledTask:
    """A task scheduled for execution with metadata for scheduling decisions."""
    priority: Priority
    scheduled_time: datetime.datetime
    # Sort by earliest deadline first within same priority
    deadline: Optional[datetime.datetime] = None
    # These fields don't affect sorting
    task_id: str = field(compare=False)
    workflow_id: str = field(compare=False)
    estimated_duration: datetime.timedelta = field(compare=False)
    agent_type: Optional[str] = field(compare=False)
    parameters: Dict[str, Any] = field(default_factory=dict, compare=False)
    execute_func: Callable = field(compare=False)
    resource_requirements: Dict[str, Union[int, float]] = field(default_factory=dict, compare=False)
    tags: List[str] = field(default_factory=list, compare=False)


class TaskScheduler:
    """
    Adaptive, decentralized task scheduler that manages execution of workflow tasks
    across distributed agent resources.
    """
    
    def __init__(
        self,
        resource_limits: Optional[Dict[str, Union[int, float]]] = None,
        optimization_strategy: str = "balanced"
    ):
        """
        Initialize the task scheduler.
        
        Args:
            resource_limits: Dictionary mapping resource types to available capacity
            optimization_strategy: Strategy for optimization (balanced, throughput, latency, cost)
        """
        self.optimization_strategy = optimization_strategy
        self.resource_limits = resource_limits or {
            "cpu": 100,         # Percentage of CPU capacity
            "memory": 1000,     # MB of memory
            "api_tokens": 1000, # Number of API calls per minute
            "agent_workers": 20 # Maximum concurrent agent tasks
        }
        
        # Priority queues for different types of tasks
        self.task_queue = []  # heapq of ScheduledTask objects
        
        # Currently executing tasks
        self.executing_tasks: Dict[str, ScheduledTask] = {}
        
        # Resource usage tracking
        self.current_resource_usage: Dict[str, Union[int, float]] = {
            resource: 0 for resource in self.resource_limits
        }
        
        # Task execution history for optimization
        self.task_history: List[Dict[str, Any]] = []
        
        # Resource predictions based on historical data
        self.resource_predictions: Dict[str, Dict[str, float]] = {}
        
        # Agent performance metrics
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        
        # Scheduled periodic tasks
        self.periodic_tasks: Dict[str, Dict[str, Any]] = {}
        
        # Task dependencies tracking
        self.task_dependencies: Dict[str, Set[str]] = {}
        
        # Setup logging
        self.logger = logging.getLogger("task_scheduler")
    
    def schedule_task(
        self,
        task_id: str,
        workflow_id: str,
        execute_func: Callable,
        priority: Priority = Priority.MEDIUM,
        scheduled_time: Optional[datetime.datetime] = None,
        deadline: Optional[datetime.datetime] = None,
        estimated_duration: Optional[datetime.timedelta] = None,
        agent_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        resource_requirements: Optional[Dict[str, Union[int, float]]] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Schedule a task for execution.
        
        Args:
            task_id: Unique identifier for the task
            workflow_id: ID of the workflow this task belongs to
            execute_func: Function to call to execute the task
            priority: Priority level for the task
            scheduled_time: When the task should execute (default: now)
            deadline: When the task must complete by
            estimated_duration: Expected execution time
            agent_type: Type of agent required to execute the task
            parameters: Parameters to pass to the execute function
            resource_requirements: Resources needed by the task
            dependencies: IDs of tasks that must complete before this one
            tags: List of tags for categorization and filtering
            
        Returns:
            Task ID
        """
        if scheduled_time is None:
            scheduled_time = datetime.datetime.now()
        
        if estimated_duration is None:
            estimated_duration = datetime.timedelta(minutes=10)
        
        if parameters is None:
            parameters = {}
        
        if resource_requirements is None:
            resource_requirements = {
                "cpu": 1,
                "memory": 10,
                "api_tokens": 1,
                "agent_workers": 1
            }
        
        if tags is None:
            tags = []
        
        # Create scheduled task
        task = ScheduledTask(
            priority=priority,
            scheduled_time=scheduled_time,
            deadline=deadline,
            task_id=task_id,
            workflow_id=workflow_id,
            estimated_duration=estimated_duration,
            agent_type=agent_type,
            parameters=parameters,
            execute_func=execute_func,
            resource_requirements=resource_requirements,
            tags=tags
        )
        
        # Register task dependencies if any
        if dependencies:
            self.task_dependencies[task_id] = set(dependencies)
        
        # Add to priority queue
        heapq.heappush(self.task_queue, task)
        
        self.logger.info(f"Scheduled task {task_id} with priority {priority} for {scheduled_time}")
        
        # Try to execute tasks now if resources available
        self._process_queue()
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled or executing task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was successfully canceled
        """
        # Check if task is currently executing
        if task_id in self.executing_tasks:
            # In a real implementation, we would implement task interruption
            # For now, just remove from executing tasks
            task = self.executing_tasks.pop(task_id)
            
            # Release resources
            for resource, amount in task.resource_requirements.items():
                if resource in self.current_resource_usage:
                    self.current_resource_usage[resource] -= amount
            
            self.logger.info(f"Canceled executing task {task_id}")
            return True
        
        # Check if task is in queue
        for i, task in enumerate(self.task_queue):
            if task.task_id == task_id:
                # Remove from queue - note this breaks heap invariant
                self.task_queue[i] = self.task_queue[-1]
                self.task_queue.pop()
                
                # Restore heap invariant
                if i < len(self.task_queue):
                    heapq.heapify(self.task_queue)
                
                self.logger.info(f"Canceled queued task {task_id}")
                return True
        
        self.logger.warning(f"Task {task_id} not found for cancellation")
        return False
    
    def reschedule_task(
        self,
        task_id: str,
        new_scheduled_time: Optional[datetime.datetime] = None,
        new_priority: Optional[Priority] = None,
        new_deadline: Optional[datetime.datetime] = None
    ) -> bool:
        """
        Reschedule a task that's already in the queue.
        
        Args:
            task_id: ID of the task to reschedule
            new_scheduled_time: New scheduled execution time
            new_priority: New priority level
            new_deadline: New deadline for task completion
            
        Returns:
            True if task was successfully rescheduled
        """
        # Find the task in the queue
        task_idx = None
        for i, task in enumerate(self.task_queue):
            if task.task_id == task_id:
                task_idx = i
                break
        
        if task_idx is None:
            self.logger.warning(f"Task {task_id} not found for rescheduling")
            return False
        
        # Get the task
        task = self.task_queue[task_idx]
        
        # Update task properties
        if new_scheduled_time is not None:
            task.scheduled_time = new_scheduled_time
        
        if new_priority is not None:
            task.priority = new_priority
        
        if new_deadline is not None:
            task.deadline = new_deadline
        
        # Rebuild heap to maintain invariant
        heapq.heapify(self.task_queue)
        
        self.logger.info(f"Rescheduled task {task_id} with new priority {task.priority} for {task.scheduled_time}")
        
        return True
    
    def _process_queue(self) -> int:
        """
        Process the task queue, executing ready tasks as resources permit.
        
        Returns:
            Number of tasks started in this processing cycle
        """
        started_tasks = 0
        
        # Check if any tasks are scheduled for now or earlier
        now = datetime.datetime.now()
        
        # Loop until no more tasks can be started
        while self.task_queue and self._can_start_next_task():
            # Peek at the next task
            next_task = self.task_queue[0]
            
            # Check if task is ready to execute
            if next_task.scheduled_time > now:
                # No tasks ready yet
                break
            
            # Check if dependencies are satisfied
            if next_task.task_id in self.task_dependencies:
                unsatisfied_deps = self.task_dependencies[next_task.task_id]
                if unsatisfied_deps:
                    # Task has unmet dependencies, try the next one
                    # We should actually find the next eligible task, but for simplicity
                    # we'll just break here
                    break
            
            # Try to allocate resources for the task
            if not self._can_allocate_resources(next_task.resource_requirements):
                # Not enough resources, try the next task
                # Again, for a real implementation we'd check other tasks
                break
            
            # Remove the task from the queue
            next_task = heapq.heappop(self.task_queue)
            
            # Allocate resources
            self._allocate_resources(next_task.resource_requirements)
            
            # Add to executing tasks
            self.executing_tasks[next_task.task_id] = next_task
            
            # Start execution (in a real system, this would be asynchronous)
            self._execute_task(next_task)
            
            started_tasks += 1
        
        return started_tasks
    
    def _execute_task(self, task: ScheduledTask):
        """
        Execute a task and handle its completion.
        
        In a real implementation, this would launch the task asynchronously
        and register callbacks for completion.
        
        Args:
            task: The task to execute
        """
        self.logger.info(f"Starting execution of task {task.task_id}")
        
        # In a real system, we would execute the task asynchronously
        # For this example, we'll simulate immediate execution
        try:
            # Call the execute function
            result = task.execute_func()
            
            # Record task completion
            self._task_completed(task, result)
        except Exception as e:
            # Record task failure
            self._task_failed(task, str(e))
    
    def _task_completed(self, task: ScheduledTask, result: Any):
        """
        Handle successful task completion.
        
        Args:
            task: The completed task
            result: The result of the task execution
        """
        # Remove from executing tasks
        if task.task_id in self.executing_tasks:
            self.executing_tasks.pop(task.task_id)
        
        # Release resources
        self._release_resources(task.resource_requirements)
        
        # Update task dependencies for other tasks
        for other_task_id, deps in self.task_dependencies.items():
            if task.task_id in deps:
                deps.remove(task.task_id)
        
        # Record execution statistics
        execution_time = datetime.datetime.now() - task.scheduled_time
        
        # Add to history
        history_entry = {
            "task_id": task.task_id,
            "workflow_id": task.workflow_id,
            "agent_type": task.agent_type,
            "priority": task.priority,
            "scheduled_time": task.scheduled_time,
            "completed_time": datetime.datetime.now(),
            "duration": execution_time,
            "status": "completed",
            "result": result
        }
        
        self.task_history.append(history_entry)
        
        # Update agent performance metrics
        if task.agent_type:
            if task.agent_type not in self.agent_performance:
                self.agent_performance[task.agent_type] = {
                    "task_count": 0,
                    "total_duration": datetime.timedelta(0),
                    "success_rate": 1.0
                }
            
            performance = self.agent_performance[task.agent_type]
            performance["task_count"] += 1
            performance["total_duration"] += execution_time
        
        self.logger.info(f"Task {task.task_id} completed successfully in {execution_time}")
        
        # Process queue again since resources were freed
        self._process_queue()
    
    def _task_failed(self, task: ScheduledTask, error: str):
        """
        Handle task failure.
        
        Args:
            task: The failed task
            error: Error information
        """
        # Remove from executing tasks
        if task.task_id in self.executing_tasks:
            self.executing_tasks.pop(task.task_id)
        
        # Release resources
        self._release_resources(task.resource_requirements)
        
        # Record execution statistics
        execution_time = datetime.datetime.now() - task.scheduled_time
        
        # Add to history
        history_entry = {
            "task_id": task.task_id,
            "workflow_id": task.workflow_id,
            "agent_type": task.agent_type,
            "priority": task.priority,
            "scheduled_time": task.scheduled_time,
            "completed_time": datetime.datetime.now(),
            "duration": execution_time,
            "status": "failed",
            "error": error
        }
        
        self.task_history.append(history_entry)
        
        # Update agent performance metrics
        if task.agent_type:
            if task.agent_type not in self.agent_performance:
                self.agent_performance[task.agent_type] = {
                    "task_count": 0,
                    "total_duration": datetime.timedelta(0),
                    "success_rate": 0.0
                }
            
            performance = self.agent_performance[task.agent_type]
            performance["task_count"] += 1
            performance["total_duration"] += execution_time
            
            # Update success rate
            performance["success_rate"] = (
                (performance["success_rate"] * (performance["task_count"] - 1) + 0) / 
                performance["task_count"]
            )
        
        self.logger.error(f"Task {task.task_id} failed: {error}")
        
        # Process queue again since resources were freed
        self._process_queue()
    
    def _can_start_next_task(self) -> bool:
        """Check if the scheduler can start executing another task."""
        # Check if we're at the maximum concurrent tasks limit
        return len(self.executing_tasks) < self.resource_limits.get("agent_workers", float('inf'))
    
    def _can_allocate_resources(self, requirements: Dict[str, Union[int, float]]) -> bool:
        """Check if required resources are available."""
        for resource, amount in requirements.items():
            if resource in self.resource_limits:
                if self.current_resource_usage[resource] + amount > self.resource_limits[resource]:
                    return False
        return True
    
    def _allocate_resources(self, requirements: Dict[str, Union[int, float]]):
        """Allocate resources for a task."""
        for resource, amount in requirements.items():
            if resource in self.current_resource_usage:
                self.current_resource_usage[resource] += amount
    
    def _release_resources(self, requirements: Dict[str, Union[int, float]]):
        """Release resources after task completion."""
        for resource, amount in requirements.items():
            if resource in self.current_resource_usage:
                self.current_resource_usage[resource] = max(0, self.current_resource_usage[resource] - amount)
    
    def schedule_periodic_task(
        self,
        task_func: Callable,
        interval: datetime.timedelta,
        task_id: Optional[str] = None,
        priority: Priority = Priority.LOW,
        agent_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        resource_requirements: Optional[Dict[str, Union[int, float]]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Schedule a task to run at regular intervals.
        
        Args:
            task_func: Function to execute
            interval: Time between executions
            task_id: Optional ID for the periodic task
            priority: Priority level
            agent_type: Type of agent to execute the task
            parameters: Parameters for the task
            resource_requirements: Resources required by the task
            tags: Tags for the task
            
        Returns:
            ID of the scheduled periodic task
        """
        if task_id is None:
            task_id = f"periodic-{uuid.uuid4()}"
        
        # Store periodic task information
        self.periodic_tasks[task_id] = {
            "task_func": task_func,
            "interval": interval,
            "last_scheduled": None,
            "priority": priority,
            "agent_type": agent_type,
            "parameters": parameters or {},
            "resource_requirements": resource_requirements,
            "tags": tags or []
        }
        
        # Schedule the first execution
        self._schedule_next_periodic_execution(task_id)
        
        return task_id
    
    def _schedule_next_periodic_execution(self, periodic_task_id: str):
        """Schedule the next execution of a periodic task."""
        if periodic_task_id not in self.periodic_tasks:
            return
        
        periodic_info = self.periodic_tasks[periodic_task_id]
        
        # Calculate next execution time
        now = datetime.datetime.now()
        if periodic_info["last_scheduled"] is None:
            next_execution = now
        else:
            next_execution = periodic_info["last_scheduled"] + periodic_info["interval"]
            if next_execution < now:
                # We missed some executions, schedule for now
                next_execution = now
        
        # Update last scheduled time
        periodic_info["last_scheduled"] = next_execution
        
        # Create a unique ID for this execution
        execution_id = f"{periodic_task_id}-{next_execution.strftime('%Y%m%d%H%M%S')}"
        
        # Create a wrapper function that will schedule the next execution
        def _periodic_wrapper():
            try:
                result = periodic_info["task_func"](**periodic_info["parameters"])
                # Schedule next execution
                self._schedule_next_periodic_execution(periodic_task_id)
                return result
            except Exception as e:
                # Still schedule next execution even if this one failed
                self._schedule_next_periodic_execution(periodic_task_id)
                raise e
        
        # Schedule this execution
        self.schedule_task(
            task_id=execution_id,
            workflow_id=f"periodic-{periodic_task_id}",
            execute_func=_periodic_wrapper,
            priority=periodic_info["priority"],
            scheduled_time=next_execution,
            agent_type=periodic_info["agent_type"],
            parameters=periodic_info["parameters"],
            resource_requirements=periodic_info["resource_requirements"],
            tags=periodic_info["tags"] + ["periodic"]
        )
    
    def cancel_periodic_task(self, periodic_task_id: str) -> bool:
        """
        Cancel a periodic task.
        
        Args:
            periodic_task_id: ID of the periodic task to cancel
            
        Returns:
            True if the task was found and canceled
        """
        if periodic_task_id in self.periodic_tasks:
            # Remove from periodic tasks
            self.periodic_tasks.pop(periodic_task_id)
            
            # Cancel any pending executions
            # This would require finding all tasks with workflow_id = f"periodic-{periodic_task_id}"
            # For simplicity, we'll omit this part
            
            self.logger.info(f"Canceled periodic task {periodic_task_id}")
            return True
        
        return False
    
    def optimize_resource_allocation(self):
        """
        Analyze execution history to optimize resource allocation.
        This would use historical data to improve future scheduling decisions.
        """
        if not self.task_history:
            return
        
        # Example optimization: update resource predictions based on history
        agent_resource_usage = {}
        
        for entry in self.task_history[-100:]:  # Look at recent history
            agent_type = entry.get("agent_type")
            if not agent_type:
                continue
            
            if agent_type not in agent_resource_usage:
                agent_resource_usage[agent_type] = {
                    "task_count": 0,
                    "total_duration": datetime.timedelta(0)
                }
            
            agent_resource_usage[agent_type]["task_count"] += 1
            
            if "duration" in entry:
                agent_resource_usage[agent_type]["total_duration"] += entry["duration"]
        
        # Update resource predictions
        for agent_type, usage in agent_resource_usage.items():
            if usage["task_count"] > 0:
                avg_duration = usage["total_duration"] / usage["task_count"]
                
                self.resource_predictions[agent_type] = {
                    "avg_duration": avg_duration.total_seconds(),
                    "estimated_resource_usage": {
                        # Example resource estimation based on agent type
                        "cpu": 5 if "analytics" in agent_type else 2,
                        "memory": 100 if "data" in agent_type else 50,
                        "api_tokens": 10 if "external" in agent_type else 2
                    }
                }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status information for all tasks in a workflow.
        
        Args:
            workflow_id: ID of the workflow to query
            
        Returns:
            Dictionary with workflow status information
        """
        # Find all tasks for this workflow
        executing = []
        queued = []
        completed = []
        failed = []
        
        # Check executing tasks
        for task_id, task in self.executing_tasks.items():
            if task.workflow_id == workflow_id:
                executing.append({
                    "task_id": task_id,
                    "agent_type": task.agent_type,
                    "started_at": task.scheduled_time,
                    "estimated_completion": task.scheduled_time + task.estimated_duration
                })
        
        # Check queued tasks
        for task in self.task_queue:
            if task.workflow_id == workflow_id:
                queued.append({
                    "task_id": task.task_id,
                    "agent_type": task.agent_type,
                    "priority": task.priority,
                    "scheduled_time": task.scheduled_time
                })
        
        # Check history for completed/failed tasks
        for entry in self.task_history:
            if entry["workflow_id"] == workflow_id:
                if entry["status"] == "completed":
                    completed.append({
                        "task_id": entry["task_id"],
                        "agent_type": entry["agent_type"],
                        "completed_at": entry["completed_time"],
                        "duration": entry["duration"]
                    })
                elif entry["status"] == "failed":
                    failed.append({
                        "task_id": entry["task_id"],
                        "agent_type": entry["agent_type"],
                        "failed_at": entry["completed_time"],
                        "error": entry.get("error", "Unknown error")
                    })
        
        # Compile the status report
        return {
            "workflow_id": workflow_id,
            "executing_tasks": executing,
            "queued_tasks": queued,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_task_count": len(executing) + len(queued) + len(completed) + len(failed),
            "progress": len(completed) / (len(executing) + len(queued) + len(completed) + len(failed)) if 
                       (len(executing) + len(queued) + len(completed) + len(failed)) > 0 else 0,
            "has_failures": len(failed) > 0
        }
    
    def get_agent_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for different agent types.
        
        Returns:
            Dictionary mapping agent types to their performance metrics
        """
        metrics = {}
        
        for agent_type, perf in self.agent_performance.items():
            avg_duration = None
            if perf["task_count"] > 0:
                avg_duration = perf["total_duration"] / perf["task_count"]
            
            metrics[agent_type] = {
                "task_count": perf["task_count"],
                "success_rate": perf["success_rate"],
                "avg_duration": avg_duration
            }
        
        return metrics
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage information.
        
        Returns:
            Dictionary with resource usage statistics
        """
        usage = {}
        
        for resource, used in self.current_resource_usage.items():
            limit = self.resource_limits.get(resource, float('inf'))
            usage[resource] = {
                "used": used,
                "limit": limit,
                "utilization": used / limit if limit > 0 else 0
            }
        
        return {
            "current_usage": usage,
            "executing_tasks": len(self.executing_tasks),
            "queued_tasks": len(self.task_queue)
        }
    
    def run_maintenance(self):
        """
        Perform scheduler maintenance tasks:
        - Optimize resource allocation
        - Clean up old history entries
        - Check for stalled tasks
        """
        # Optimize resource allocation based on history
        self.optimize_resource_allocation()
        
        # Clean up history (keep last 1000 entries)
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
        
        # Check for stalled tasks (running much longer than estimated)
        now = datetime.datetime.now()
        for task_id, task in list(self.executing_tasks.items()):
            expected_end = task.scheduled_time + task.estimated_duration * 2  # Allow 2x duration
            if now > expected_end:
                # Log potentially stalled task
                self.logger.warning(f"Task {task_id} may be stalled - running longer than 2x estimated duration")
                
                # In a real implementation, we might:
                # 1. Send alerts
                # 2. Attempt to restart the task
                # 3. Escalate to human operator
                pass