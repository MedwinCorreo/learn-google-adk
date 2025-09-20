"""
FastAPI webhook application for Google ADK Teams Bot
Handles incoming Teams messages and routes to ADK agents
"""

import os
import time
import hmac
import hashlib
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from logger_config import get_logger, log_request, log_response, log_error

load_dotenv()

app = FastAPI(
    title="Google ADK Teams Bot",
    description="Teams bot powered by Google ADK agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://teams.microsoft.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

logger = get_logger(__name__)

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret')
TEAMS_APP_ID = os.getenv('TEAMS_APP_ID')
REQUEST_TIMEOUT = 30  # seconds


class TeamsMessage(BaseModel):
    """Teams message payload model"""
    type: str
    id: Optional[str] = None
    timestamp: Optional[str] = None
    serviceUrl: Optional[str] = None
    channelId: Optional[str] = None
    from_: Optional[Dict[str, Any]] = None
    conversation: Optional[Dict[str, Any]] = None
    recipient: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    locale: Optional[str] = None
    
    class Config:
        fields = {'from_': 'from'}


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    version: str = "1.0.0"
    service: str = "adk-teams-bot"


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Google ADK Teams Bot starting up...")
    logger.info(f"Teams App ID: {TEAMS_APP_ID}")
    logger.info(f"Request timeout: {REQUEST_TIMEOUT} seconds")
    
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        logger.info(f"Created logs directory: {logs_dir}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Google ADK Teams Bot shutting down...")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", str(int(time.time() * 1000)))
    
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={"request_id": request_id}
    )
    
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        
        logger.info(
            f"Request completed: {response.status_code} ({duration:.2f}ms)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration
            }
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"
        return response
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_error(logger, e, {"request_id": request_id})
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def verify_hmac_signature(request_body: bytes, signature: str) -> bool:
    """
    Verify HMAC signature for webhook security
    
    Args:
        request_body: Raw request body
        signature: Signature from header
        
    Returns:
        True if signature is valid
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not configured, skipping signature verification")
        return True
        
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/api/teams/webhook")
async def teams_webhook(request: Request):
    """
    Main webhook endpoint for Teams messages
    
    Handles incoming messages from Microsoft Teams and routes them
    to appropriate ADK agents for processing
    """
    start_time = time.time()
    
    try:
        signature = request.headers.get("X-Teams-Signature", "")
        request_body = await request.body()
        
        if not verify_hmac_signature(request_body, signature):
            logger.warning("Invalid HMAC signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        try:
            payload = await request.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        log_request(logger, payload)
        
        message_type = payload.get("type", "")
        
        if message_type != "message":
            logger.info(f"Ignoring non-message activity: {message_type}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "ignored", "reason": "Not a message activity"}
            )
        
        try:
            from teams_handler import process_teams_message
        except ImportError:
            logger.error("teams_handler module not found")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "Service temporarily unavailable"}
            )
        
        try:
            response = await asyncio.wait_for(
                process_teams_message(payload),
                timeout=REQUEST_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {REQUEST_TIMEOUT} seconds")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={"error": "Request processing timeout"}
            )
        
        duration_ms = (time.time() - start_time) * 1000
        log_response(logger, response, duration_ms)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(logger, e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Failed to process message",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Endpoint not found",
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    log_error(logger, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )