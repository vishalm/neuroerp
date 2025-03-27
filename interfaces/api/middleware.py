"""
AI-Native ERP System - API Middleware

This module provides middleware components for the API interface, including:
- Request authentication and authorization
- Request/response logging
- Error handling
- Performance monitoring
- Rate limiting
- AI context augmentation
"""

import time
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable, Awaitable
from functools import wraps
from datetime import datetime, timedelta

import jwt
from fastapi import Request, Response, HTTPException, FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_middleware")

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock secret key - in production, this should be securely stored
JWT_SECRET = "erp-ai-native-secret-key"  # Replace with secure key in production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=24)

class APIKey:
    """API Key management for service-to-service communication."""
    
    def __init__(self, key: str, service_name: str, scopes: List[str]):
        self.key = key
        self.service_name = service_name
        self.scopes = scopes

# In-memory store of API keys (should be replaced with database in production)
API_KEYS = {
    "finance-service-key": APIKey(
        "finance-service-key", 
        "finance", 
        ["read:finance", "write:finance"]
    ),
    "hr-service-key": APIKey(
        "hr-service-key",
        "hr",
        ["read:hr", "write:hr"]
    ),
    "supply-chain-key": APIKey(
        "supply-chain-key",
        "supply_chain",
        ["read:supply_chain", "write:supply_chain"]
    )
}

class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_history = {}  # client_id -> list of request timestamps
    
    def is_rate_limited(self, client_id: str) -> bool:
        """Check if a client has exceeded their rate limit."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Initialize or clean up old requests
        if client_id not in self.request_history:
            self.request_history[client_id] = []
        
        # Remove requests older than 1 minute
        self.request_history[client_id] = [
            ts for ts in self.request_history[client_id] if ts > minute_ago
        ]
        
        # Check if rate limit is exceeded
        if len(self.request_history[client_id]) >= self.requests_per_minute:
            return True
        
        # Record this request
        self.request_history[client_id].append(now)
        return False

# Initialize rate limiter
rate_limiter = RateLimiter()

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client info
        client_host = request.client.host if request.client else "unknown"
        
        # Log the request
        logger.info(f"Request {request_id}: {request.method} {request.url.path} from {client_host}")
        
        # Record the start time
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log the response
            logger.info(
                f"Response {request_id}: {response.status_code} processed in {process_time:.4f}s"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Error {request_id}: {str(e)}")
            
            # Return error response
            process_time = time.time() - start_time
            error_response = Response(
                content=json.dumps({
                    "error": str(e),
                    "request_id": request_id
                }),
                status_code=500,
                media_type="application/json"
            )
            error_response.headers["X-Request-ID"] = request_id
            error_response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            return error_response

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance."""
    
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log performance metrics
        logger.info(
            f"Performance: {request.method} {request.url.path} took {process_time:.4f}s"
        )
        
        # TODO: Integrate with monitoring system to track performance metrics
        
        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting."""
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address or authenticated user)
        client_id = request.client.host if request.client else "unknown"
        
        # Check for authentication headers
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                client_id = payload.get("sub", client_id)
            except:
                # If token is invalid, fallback to IP address
                pass
        
        # Check rate limit
        if rate_limiter.is_rate_limited(client_id):
            # Return 429 Too Many Requests
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "retry_after": 60  # seconds
                }),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"}
            )
        
        # Process the request
        return await call_next(request)

class AIContextMiddleware(BaseHTTPMiddleware):
    """Middleware for augmenting requests with AI context."""
    
    async def dispatch(self, request: Request, call_next):
        # Store original path for context
        request.state.original_path = request.url.path
        
        # Add AI context information to the request state
        request.state.ai_context = {
            "timestamp": datetime.now().isoformat(),
            "request_type": self._categorize_request(request),
            "complexity": self._estimate_complexity(request),
        }
        
        # Process the request
        response = await call_next(request)
        
        return response
    
    def _categorize_request(self, request: Request) -> str:
        """Categorize the request type for AI processing prioritization."""
        path = request.url.path.lower()
        
        if "finance" in path:
            return "finance"
        elif "hr" in path:
            return "hr"
        elif "supply" in path or "inventory" in path:
            return "supply_chain"
        elif "customer" in path:
            return "customer"
        else:
            return "general"
    
    def _estimate_complexity(self, request: Request) -> str:
        """Estimate the complexity of the request for resource allocation."""
        # This is a simple heuristic and should be enhanced based on actual request patterns
        method = request.method
        
        if method == "GET":
            return "low"
        elif method == "POST" or method == "PUT":
            return "medium"
        elif method == "DELETE":
            return "low"
        else:
            return "medium"

def setup_middlewares(app: FastAPI):
    """Configure all middleware for the FastAPI application."""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middlewares
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.add_middleware(RateLimitingMiddleware)
    app.add_middleware(AIContextMiddleware)

# Authentication utility functions
def create_access_token(user_id: str, scopes: List[str] = None) -> str:
    """Create a JWT access token."""
    expires = datetime.utcnow() + JWT_EXPIRATION
    
    payload = {
        "sub": user_id,
        "exp": expires,
        "scopes": scopes or []
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency to get the current authenticated user from a token."""
    return decode_token(token)

def has_scope(required_scope: str):
    """Dependency to check if the user has the required scope."""
    async def _has_scope(user: Dict[str, Any] = Depends(get_current_user)) -> bool:
        scopes = user.get("scopes", [])
        if required_scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Not authorized. Required scope: {required_scope}",
            )
        return True
    return _has_scope

def verify_api_key(api_key: str = Depends(oauth2_scheme)) -> APIKey:
    """Dependency to verify an API key."""
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return API_KEYS[api_key]

def require_api_scope(required_scope: str):
    """Dependency to check if the API key has the required scope."""
    async def _require_api_scope(api_key: APIKey = Depends(verify_api_key)) -> bool:
        if required_scope not in api_key.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"API key doesn't have required scope: {required_scope}",
            )
        return True
    return _require_api_scope

# Decorator for measuring endpoint performance
def measure_performance(func: Callable) -> Callable:
    """Decorator to measure endpoint performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        # Log performance
        logger.info(f"Endpoint {func.__name__} took {elapsed_time:.4f}s")
        
        return result
    
    return wrapper