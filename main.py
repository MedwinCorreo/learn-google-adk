"""
Main entry point for Google ADK Teams Bot with Web UI
Serves both the Teams webhook and ADK web interface
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable ADK web interface
SERVE_WEB_INTERFACE = True

# Import the agents
from multi_tool_agent.agent import root_agent

# Import the existing FastAPI app
from app import app

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )