"""
AI-Native ERP System - Web Interface

This module provides a web interface for the AI-Native ERP system using FastAPI and Jinja2 templates.
It integrates the chat engine for conversational interactions and provides dashboards for different
business domains (Finance, HR, Supply Chain, Operations).
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.sessions import SessionMiddleware

# Import the chat engine
from interfaces.chat.chat_engine import ChatEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_interface")

# Initialize FastAPI app
app = FastAPI(
    title="AI-Native ERP System",
    description="A fully AI-native Enterprise Resource Planning (ERP) system.",
    version="0.1.0"
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="erp-ai-native-web-secret-key"  # Replace with secure key in production
)

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="interfaces/web/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="interfaces/web/templates")

# Initialize chat engine
chat_engine = ChatEngine()

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory user database (replace with actual database in production)
USERS = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "admin",  # In production, use proper password hashing
        "role": "admin",
        "departments": ["finance", "hr", "supply_chain", "operations"]
    },
    "finance_user": {
        "username": "finance_user",
        "full_name": "Finance User",
        "email": "finance@example.com",
        "hashed_password": "finance",  # In production, use proper password hashing
        "role": "user",
        "departments": ["finance"]
    },
    "hr_user": {
        "username": "hr_user",
        "full_name": "HR User",
        "email": "hr@example.com",
        "hashed_password": "hr",  # In production, use proper password hashing
        "role": "user",
        "departments": ["hr"]
    }
}

# Token storage (replace with proper JWT in production)
TOKENS = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

# Auth utilities
def verify_password(plain_password, hashed_password):
    """Verify password (simplified for demo)."""
    # In production, use proper password hashing
    return plain_password == hashed_password

def get_user(username: str):
    """Get user from database."""
    if username in USERS:
        return USERS[username]
    return None

def authenticate_user(username: str, password: str):
    """Authenticate user with username and password."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = timedelta(hours=24)):
    """Create access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire.timestamp()})
    # In production, use JWT
    token = f"{to_encode['sub']}_{expire.timestamp()}"
    TOKENS[token] = to_encode
    return token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token."""
    if token not in TOKENS:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = TOKENS[token]
    if token_data["exp"] < datetime.utcnow().timestamp():
        TOKENS.pop(token)
        raise HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user(token_data["sub"])
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint, redirects to login."""
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["username"], "departments": user["departments"], "role": user["role"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission."""
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid username or password"}
        )
    
    access_token = create_access_token(
        data={"sub": user["username"], "departments": user["departments"], "role": user["role"]}
    )
    
    # Store token in session
    request.session["token"] = access_token
    
    # Redirect to dashboard
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    """Logout and clear session."""
    if "token" in request.session:
        token = request.session["token"]
        TOKENS.pop(token, None)
        request.session.pop("token", None)
    
    return RedirectResponse(url="/login")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    if "token" not in request.session:
        return RedirectResponse(url="/login")
    
    try:
        user = await get_current_user(request.session["token"])
    except HTTPException:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request,
            "user": user,
            "page": "dashboard",
            "title": "ERP Dashboard"
        }
    )

@app.get("/finance", response_class=HTMLResponse)
async def finance_dashboard(request: Request):
    """Finance dashboard page."""
    if "token" not in request.session:
        return RedirectResponse(url="/login")
    
    try:
        user = await get_current_user(request.session["token"])
        if "finance" not in user["departments"] and user["role"] != "admin":
            return RedirectResponse(url="/dashboard")
    except HTTPException:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "finance.html", 
        {
            "request": request,
            "user": user,
            "page": "finance",
            "title": "Finance Dashboard"
        }
    )

@app.get("/hr", response_class=HTMLResponse)
async def hr_dashboard(request: Request):
    """HR dashboard page."""
    if "token" not in request.session:
        return RedirectResponse(url="/login")
    
    try:
        user = await get_current_user(request.session["token"])
        if "hr" not in user["departments"] and user["role"] != "admin":
            return RedirectResponse(url="/dashboard")
    except HTTPException:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "hr.html", 
        {
            "request": request,
            "user": user,
            "page": "hr",
            "title": "HR Dashboard"
        }
    )

@app.get("/supply-chain", response_class=HTMLResponse)
async def supply_chain_dashboard(request: Request):
    """Supply Chain dashboard page."""
    if "token" not in request.session:
        return RedirectResponse(url="/login")
    
    try:
        user = await get_current_user(request.session["token"])
        if "supply_chain" not in user["departments"] and user["role"] != "admin":
            return RedirectResponse(url="/dashboard")
    except HTTPException:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "supply_chain.html", 
        {
            "request": request,
            "user": user,
            "page": "supply_chain",
            "title": "Supply Chain Dashboard"
        }
    )

@app.get("/operations", response_class=HTMLResponse)
async def operations_dashboard(request: Request):
    """Operations dashboard page."""
    if "token" not in request.session:
        return RedirectResponse(url="/login")
    
    try:
        user = await get_current_user(request.session["token"])
        if "operations" not in user["departments"] and user["role"] != "admin":
            return RedirectResponse(url="/dashboard")
    except HTTPException:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "operations.html", 
        {
            "request": request,
            "user": user,
            "page": "operations",
            "title": "Operations Dashboard"
        }
    )

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Chat interface page."""
    if "token" not in request.session:
        return RedirectResponse(url="/login")
    
    try:
        user = await get_current_user(request.session["token"])
    except HTTPException:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "chat.html", 
        {
            "request": request,
            "user": user,
            "page": "chat",
            "title": "AI Assistant"
        }
    )

@app.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, client_id)
    
    # Create a conversation for this client if it doesn't exist
    conversation_id = f"conversation_{client_id}"
    chat_engine.get_or_create_conversation(conversation_id, client_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # Process the message
                response = await chat_engine.process_message(
                    message=data["content"],
                    conversation_id=conversation_id,
                    user_id=client_id
                )
                
                # Send response back to the client
                await manager.send_message(
                    client_id=client_id,
                    message={
                        "type": "response",
                        "content": response["response"],
                        "domain": response.get("domain", "general"),
                        "message_id": response["message_id"],
                        "timestamp": response["timestamp"]
                    }
                )
            
            elif data["type"] == "clear_history":
                # Clear conversation history
                chat_engine.clear_conversation(conversation_id)
                
                # Send confirmation back to the client
                await manager.send_message(
                    client_id=client_id,
                    message={
                        "type": "system",
                        "content": "Conversation history cleared.",
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")
        try:
            await manager.send_message(
                client_id=client_id,
                message={
                    "type": "error",
                    "content": "An error occurred while processing your message.",
                    "timestamp": datetime.now().isoformat()
                }
            )
        except:
            pass
        manager.disconnect(client_id)

@app.get("/api/chat/history")
async def get_chat_history(request: Request):
    """Get chat history for the current user."""
    if "token" not in request.session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    try:
        user = await get_current_user(request.session["token"])
    except HTTPException:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    conversation_id = f"conversation_{user['username']}"
    history = chat_engine.get_conversation_history(conversation_id)
    
    return JSONResponse(content={"history": history})

@app.get("/api/system/status")
async def get_system_status(request: Request):
    """Get system status."""
    if "token" not in request.session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    try:
        user = await get_current_user(request.session["token"])
        if user["role"] != "admin":
            return JSONResponse(status_code=403, content={"error": "Not authorized"})
    except HTTPException:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    # In a real implementation, this would get actual system status
    status = {
        "status": "healthy",
        "components": {
            "chat_engine": "operational",
            "neural_fabric": "operational",
            "orchestrator": "operational",
            "ollama": "operational"
        },
        "metrics": {
            "active_users": 3,
            "active_conversations": len(chat_engine.conversations),
            "messages_processed_today": 128,
            "system_uptime": "3d 12h 45m"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(content=status)

# Mock API endpoints for frontend demo
@app.get("/api/finance/summary")
async def get_finance_summary(request: Request):
    """Get finance summary data for dashboard."""
    if "token" not in request.session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    try:
        user = await get_current_user(request.session["token"])
        if "finance" not in user["departments"] and user["role"] != "admin":
            return JSONResponse(status_code=403, content={"error": "Not authorized"})
    except HTTPException:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    # Mock finance data
    data = {
        "revenue": {
            "current": 1250000,
            "previous": 1150000,
            "change_percent": 8.7,
            "trend": [1050000, 1100000, 1150000, 1250000]
        },
        "expenses": {
            "current": 850000,
            "previous": 820000,
            "change_percent": 3.7,
            "trend": [780000, 800000, 820000, 850000]
        },
        "profit": {
            "current": 400000,
            "previous": 330000,
            "change_percent": 21.2,
            "trend": [270000, 300000, 330000, 400000]
        },
        "cash_flow": {
            "current": 520000,
            "previous": 480000,
            "change_percent": 8.3,
            "trend": [450000, 460000, 480000, 520000]
        },
        "top_expenses": [
            {"category": "Salaries", "amount": 350000},
            {"category": "Marketing", "amount": 150000},
            {"category": "Operations", "amount": 120000},
            {"category": "R&D", "amount": 100000},
            {"category": "Other", "amount": 130000}
        ],
        "recent_transactions": [
            {"id": "T12345", "description": "Client payment", "amount": 45000, "date": "2023-06-15", "type": "income"},
            {"id": "T12346", "description": "Server infrastructure", "amount": -12000, "date": "2023-06-14", "type": "expense"},
            {"id": "T12347", "description": "Marketing campaign", "amount": -8500, "date": "2023-06-12", "type": "expense"},
            {"id": "T12348", "description": "Client payment", "amount": 32000, "date": "2023-06-10", "type": "income"},
            {"id": "T12349", "description": "Office supplies", "amount": -1500, "date": "2023-06-08", "type": "expense"}
        ]
    }
    
    return JSONResponse(content=data)

@app.get("/api/hr/summary")
async def get_hr_summary(request: Request):
    """Get HR summary data for dashboard."""
    if "token" not in request.session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    try:
        user = await get_current_user(request.session["token"])
        if "hr" not in user["departments"] and user["role"] != "admin":
            return JSONResponse(status_code=403, content={"error": "Not authorized"})
    except HTTPException:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    # Mock HR data
    data = {
        "headcount": {
            "current": 156,
            "previous": 148,
            "change": 8,
            "by_department": [
                {"name": "Engineering", "count": 48},
                {"name": "Sales", "count": 35},
                {"name": "Marketing", "count": 22},
                {"name": "Operations", "count": 30},
                {"name": "Finance", "count": 12},
                {"name": "HR", "count": 9}
            ]
        },
        "turnover": {
            "rate": 12.5,
            "previous_rate": 14.2,
            "change_percent": -12.0,
            "trend": [15.1, 14.8, 14.2, 12.5]
        },
        "satisfaction": {
            "score": 7.8,
            "previous_score": 7.5,
            "change": 0.3,
            "by_department": [
                {"name": "Engineering", "score": 8.2},
                {"name": "Sales", "score": 7.9},
                {"name": "Marketing", "score": 8.1},
                {"name": "Operations", "score": 7.2},
                {"name": "Finance", "score": 7.6},
                {"name": "HR", "score": 8.5}
            ]
        },
        "open_positions": {
            "count": 12,
            "by_department": [
                {"name": "Engineering", "count": 5},
                {"name": "Sales", "count": 3},
                {"name": "Marketing", "count": 1},
                {"name": "Operations", "count": 2},
                {"name": "Finance", "count": 1},
                {"name": "HR", "count": 0}
            ]
        },
        "recent_hires": [
            {"name": "Jane Smith", "position": "Senior Developer", "department": "Engineering", "start_date": "2023-06-01"},
            {"name": "John Doe", "position": "Sales Representative", "department": "Sales", "start_date": "2023-05-15"},
            {"name": "Emily Johnson", "position": "Marketing Specialist", "department": "Marketing", "start_date": "2023-05-10"},
            {"name": "Michael Brown", "position": "Operations Manager", "department": "Operations", "start_date": "2023-05-01"}
        ]
    }
    
    return JSONResponse(content=data)

@app.get("/api/supply-chain/summary")
async def get_supply_chain_summary(request: Request):
    """Get supply chain summary data for dashboard."""
    if "token" not in request.session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    try:
        user = await get_current_user(request.session["token"])
        if "supply_chain" not in user["departments"] and user["role"] != "admin":
            return JSONResponse(status_code=403, content={"error": "Not authorized"})
    except HTTPException:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    # Mock supply chain data
    data = {
        "inventory": {
            "total_value": 2850000,
            "items_count": 2456,
            "breakdown": [
                {"category": "Raw Materials", "value": 950000, "percentage": 33.3},
                {"category": "Work In Progress", "value": 650000, "percentage": 22.8},
                {"category": "Finished Goods", "value": 1250000, "percentage": 43.9}
            ]
        },
        "suppliers": {
            "active_count": 128,
            "on_time_delivery": 92.5,
            "quality_compliance": 95.2,
            "top_suppliers": [
                {"name": "Supplier A", "on_time": 98.5, "quality": 99.1, "spend": 450000},
                {"name": "Supplier B", "on_time": 95.2, "quality": 97.5, "spend": 320000},
                {"name": "Supplier C", "on_time": 92.8, "quality": 96.3, "spend": 280000},
                {"name": "Supplier D", "on_time": 91.5, "quality": 98.2, "spend": 250000},
                {"name": "Supplier E", "on_time": 90.2, "quality": 94.8, "spend": 200000}
            ]
        },
        "orders": {
            "pending": 45,
            "completed": 325,
            "delayed": 8,
            "monthly_trend": [280, 295, 310, 325]
        },
        "critical_items": [
            {"id": "I1001", "name": "Component A", "stock": 125, "min_required": 100, "status": "normal"},
            {"id": "I1032", "name": "Component B", "stock": 85, "min_required": 100, "status": "low"},
            {"id": "I1045", "name": "Component C", "stock": 30, "min_required": 75, "status": "critical"},
            {"id": "I1078", "name": "Component D", "stock": 110, "min_required": 100, "status": "normal"},
            {"id": "I1092", "name": "Component E", "stock": 60, "min_required": 50, "status": "normal"}
        ],
        "logistics": {
            "average_delivery_time": 3.2,
            "in_transit_value": 320000,
            "shipping_costs": 42000,
            "shipping_cost_trend": [38000, 39500, 41000, 42000]
        }
    }
    
    return JSONResponse(content=data)

@app.get("/api/operations/summary")
async def get_operations_summary(request: Request):
    """Get operations summary data for dashboard."""
    if "token" not in request.session:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    try:
        user = await get_current_user(request.session["token"])
        if "operations" not in user["departments"] and user["role"] != "admin":
            return JSONResponse(status_code=403, content={"error": "Not authorized"})
    except HTTPException:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    # Mock operations data
    data = {
        "production": {
            "efficiency": 87.5,
            "previous": 84.2,
            "change_percent": 3.9,
            "trend": [81.5, 82.8, 84.2, 87.5]
        },
        "quality": {
            "defect_rate": 1.2,
            "previous": 1.5,
            "change_percent": -20.0,
            "trend": [1.8, 1.6, 1.5, 1.2]
        },
        "maintenance": {
            "planned": 85,
            "unplanned": 15,
            "equipment_uptime": 97.8,
            "maintenance_costs": 85000,
            "cost_trend": [92000, 89000, 87000, 85000]
        },
        "capacity": {
            "utilization": 82.5,
            "previous": 79.8,
            "change_percent": 3.4,
            "by_facility": [
                {"name": "Facility A", "utilization": 88.5},
                {"name": "Facility B", "utilization": 85.2},
                {"name": "Facility C", "utilization": 79.8},
                {"name": "Facility D", "utilization": 76.5}
            ]
        },
        "critical_issues": [
            {"id": "M2001", "equipment": "Production Line 2", "issue": "Calibration needed", "priority": "medium", "status": "scheduled"},
            {"id": "M2015", "equipment": "Packaging Machine 3", "issue": "Performance degradation", "priority": "high", "status": "in_progress"},
            {"id": "M2023", "equipment": "Quality Scanner", "issue": "Software update required", "priority": "low", "status": "scheduled"},
            {"id": "M2032", "equipment": "Cooling System", "issue": "Pressure fluctuations", "priority": "medium", "status": "investigating"}
        ]
    }
    
    return JSONResponse(content=data)

# Main function to run the app
def run_app():
    """Run the app with uvicorn server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_app()