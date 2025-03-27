"""
Event Bus for NeuroERP.

This module implements a publish-subscribe event system that allows different
components of the system to communicate asynchronously.
"""

import time
import uuid
import threading
import queue
import logging
from typing import Dict, Any, List, Callable, Optional, Set, Union
from dataclasses import dataclass, field
import json

from .config import Config

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Represents a system event."""
    
    # Event type (e.g., 'workflow.started', 'document.created')
    event_type: str
    
    # Event payload
    payload: Dict[str, Any]
    
    # Unique event ID
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Timestamp when the event was created
    timestamp: float = field(default_factory=time.time)
    
    # Source component that generated the event
    source: str = "system"
    
    # Event version (for schema evolution)
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "source": self.source,
            "version": self.version
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            event_type=data["event_type"],
            payload=data["payload"],
            timestamp=data.get("timestamp", time.time()),
            source=data.get("source", "system"),
            version=data.get("version", "1.0")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Create event from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class EventBus:
    """Central event bus for system-wide communication."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one event bus exists."""
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the event bus."""
        # Skip if already initialized (singleton pattern)
        if self._initialized:
            return
            
        self._config = Config()
        
        # Map of event types to list of subscribers
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        
        # Event queue for asynchronous processing
        self._event_queue = queue.Queue(maxsize=self._config.get("event_bus.max_queue_size", 1000))
        
        # Map to track event handler failures for retry logic
        self._event_failures: Dict[str, Dict[str, int]] = {}
        
        # Set to track topics that are being processed to avoid duplication
        self._wildcard_subscribers: List[Callable[[Event], None]] = []
        
        # Flag to control worker threads
        self._running = False
        
        # Worker threads
        self._workers: List[threading.Thread] = []
        
        # Start the event bus
        self.start()
        
        self._initialized = True
        logger.info("Event bus initialized")
    
    def start(self):
        """Start the event bus worker threads."""
        if self._running:
            return
            
        self._running = True
        num_workers = self._config.get("event_bus.worker_threads", 4)
        
        # Create and start worker threads
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._event_worker,
                name=f"event-worker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
            
        logger.info(f"Event bus started with {num_workers} workers")
    
    def stop(self, wait_for_completion: bool = True, timeout: Optional[float] = None):
        """Stop the event bus worker threads.
        
        Args:
            wait_for_completion: Wait for all events to be processed
            timeout: Maximum time to wait for completion (seconds)
        """
        if not self._running:
            return
            
        self._running = False
        
        if wait_for_completion:
            try:
                self._event_queue.join()
            except (KeyboardInterrupt, SystemExit):
                pass
        
        # Wait for all worker threads to terminate
        for worker in self._workers:
            worker.join(timeout=timeout)
            
        self._workers = []
        logger.info("Event bus stopped")
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to (use '*' for all events)
            callback: Function to call when event occurs
        """
        if event_type == '*':
            self._wildcard_subscribers.append(callback)
            logger.debug(f"Added wildcard subscriber {callback.__qualname__}")
            return
            
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
            
        self._subscribers[event_type].append(callback)
        logger.debug(f"Added subscriber for '{event_type}': {callback.__qualname__}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> bool:
        """Unsubscribe from events of a specific type.
        
        Args:
            event_type: Type of events to unsubscribe from (use '*' for all events)
            callback: Function to remove from subscribers
            
        Returns:
            True if the subscription was removed, False otherwise
        """
        if event_type == '*':
            try:
                self._wildcard_subscribers.remove(callback)
                logger.debug(f"Removed wildcard subscriber {callback.__qualname__}")
                return True
            except ValueError:
                return False
                
        if event_type not in self._subscribers:
            return False
            
        try:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Removed subscriber for '{event_type}': {callback.__qualname__}")
            
            # Clean up empty subscriber lists
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
                
            return True
        except ValueError:
            return False
    
    def publish(self, event: Union[Event, str], payload: Optional[Dict[str, Any]] = None, 
               source: str = "system") -> str:
        """Publish an event to subscribers.
        
        Args:
            event: Either an Event object or event type string
            payload: Event data (used only if event is a string)
            source: Source component (used only if event is a string)
            
        Returns:
            Event ID
        """
        if isinstance(event, str):
            event = Event(
                event_type=event,
                payload=payload or {},
                source=source
            )
        
        try:
            self._event_queue.put(event, block=False)
            logger.debug(f"Published event {event.id} of type '{event.event_type}'")
            return event.id
        except queue.Full:
            logger.error(f"Event queue full, discarding event of type '{event.event_type}'")
            raise RuntimeError("Event queue full, cannot publish event")
    
    def _event_worker(self):
        """Worker thread to process events from the queue."""
        retry_attempts = self._config.get("event_bus.retry_attempts", 3)
        
        while self._running:
            try:
                event = self._event_queue.get(timeout=1.0)
            except queue.Empty:
                continue
                
            try:
                self._process_event(event, retry_attempts)
            finally:
                self._event_queue.task_done()
    
    def _process_event(self, event: Event, retry_attempts: int):
        """Process a single event by delivering it to subscribers.
        
        Args:
            event: The event to process
            retry_attempts: Maximum number of retry attempts for failed handlers
        """
        event_type = event.event_type
        delivered = False
        
        # Call specific subscribers for this event type
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                    delivered = True
                except Exception as e:
                    logger.error(f"Error in event handler for '{event_type}': {e}", exc_info=True)
                    
                    # Track failure for retry
                    handler_id = f"{callback.__module__}.{callback.__qualname__}"
                    if event.id not in self._event_failures:
                        self._event_failures[event.id] = {}
                    
                    failures = self._event_failures[event.id].get(handler_id, 0) + 1
                    self._event_failures[event.id][handler_id] = failures
                    
                    # Retry if under the limit
                    if failures <= retry_attempts:
                        logger.info(f"Retrying event {event.id} for handler {handler_id} "
                                   f"(attempt {failures}/{retry_attempts})")
                        self.publish(event)
        
        # Call wildcard subscribers
        for callback in self._wildcard_subscribers:
            try:
                callback(event)
                delivered = True
            except Exception as e:
                logger.error(f"Error in wildcard event handler for '{event_type}': {e}", exc_info=True)
                
                # Track failure for retry (same logic as above)
                handler_id = f"{callback.__module__}.{callback.__qualname__}"
                if event.id not in self._event_failures:
                    self._event_failures[event.id] = {}
                
                failures = self._event_failures[event.id].get(handler_id, 0) + 1
                self._event_failures[event.id][handler_id] = failures
                
                # Retry if under the limit
                if failures <= retry_attempts:
                    logger.info(f"Retrying event {event.id} for wildcard handler {handler_id} "
                               f"(attempt {failures}/{retry_attempts})")
                    self.publish(event)
        
        if delivered:
            logger.debug(f"Successfully delivered event {event.id} of type '{event_type}'")
        else:
            logger.warning(f"No handlers found for event of type '{event_type}'")
    
    def get_queue_size(self) -> int:
        """Get the current size of the event queue."""
        return self._event_queue.qsize()
    
    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Get the number of subscribers for a specific event type or all events.
        
        Args:
            event_type: Type of events to count subscribers for, or None for all
            
        Returns:
            Number of subscribers
        """
        if event_type is None:
            # Count all subscribers
            return sum(len(subs) for subs in self._subscribers.values()) + len(self._wildcard_subscribers)
        elif event_type == '*':
            # Count wildcard subscribers
            return len(self._wildcard_subscribers)
        else:
            # Count subscribers for specific event type
            return len(self._subscribers.get(event_type, []))
    
    def clear_error_tracking(self, event_id: Optional[str] = None):
        """Clear error tracking for a specific event or all events.
        
        Args:
            event_id: ID of event to clear tracking for, or None for all
        """
        if event_id is None:
            self._event_failures.clear()
        elif event_id in self._event_failures:
            del self._event_failures[event_id]
    
    def wait_until_empty(self, timeout: Optional[float] = None) -> bool:
        """Wait until the event queue is empty.
        
        Args:
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if queue is empty, False if timeout occurred
        """
        start_time = time.time()
        while not self._event_queue.empty():
            if timeout is not None and time.time() - start_time > timeout:
                return False
            time.sleep(0.1)
        return True