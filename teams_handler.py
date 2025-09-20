"""
Teams message handler for Google ADK Teams Bot
Processes incoming Teams messages and routes to ADK agents
"""

import re
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from logger_config import get_logger

logger = get_logger(__name__)


class MessageIntent:
    """Message intent types"""
    WEATHER = "weather"
    TIME = "time"
    TRAFFIC = "traffic"
    HELP = "help"
    UNKNOWN = "unknown"


def extract_city_from_text(text: str) -> Optional[str]:
    """
    Extract city name from message text
    
    Args:
        text: Message text
        
    Returns:
        City name if found, None otherwise
    """
    common_patterns = [
        r"(?:weather|time|traffic)\s+(?:in|for|at)\s+([A-Za-z\s]+?)(?:\?|$|\.)",
        r"(?:what's|what is|whats)\s+the\s+(?:weather|time|traffic)\s+(?:in|for|at)\s+([A-Za-z\s]+?)(?:\?|$|\.)",
        r"(?:how's|how is|hows)\s+(?:the\s+)?(?:weather|traffic)\s+(?:in|for|at)\s+([A-Za-z\s]+?)(?:\?|$|\.)",
        r"([A-Za-z\s]+?)\s+(?:weather|time|traffic)",
    ]
    
    text_lower = text.lower()
    
    for pattern in common_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            city = ' '.join(word.capitalize() for word in city.split())
            logger.debug(f"Extracted city: {city}")
            return city
    
    default_cities = ["new york", "los angeles", "chicago", "houston", "phoenix"]
    for city in default_cities:
        if city in text_lower:
            return ' '.join(word.capitalize() for word in city.split())
    
    return "New York"  # Default city


def parse_message_intent(text: str) -> Tuple[str, Optional[str]]:
    """
    Parse user message to determine intent and extract parameters
    
    Args:
        text: Message text from user
        
    Returns:
        Tuple of (intent, city)
    """
    if not text:
        return MessageIntent.HELP, None
    
    text_lower = text.lower().strip()
    
    weather_keywords = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy"]
    time_keywords = ["time", "clock", "hour", "timezone", "what time"]
    traffic_keywords = ["traffic", "congestion", "roads", "commute", "driving"]
    help_keywords = ["help", "hello", "hi", "hey", "start", "commands", "what can you do"]
    
    city = extract_city_from_text(text)
    
    for keyword in weather_keywords:
        if keyword in text_lower:
            logger.info(f"Detected weather intent for city: {city}")
            return MessageIntent.WEATHER, city
    
    for keyword in time_keywords:
        if keyword in text_lower:
            logger.info(f"Detected time intent for city: {city}")
            return MessageIntent.TIME, city
    
    for keyword in traffic_keywords:
        if keyword in text_lower:
            logger.info(f"Detected traffic intent for city: {city}")
            return MessageIntent.TRAFFIC, city
    
    for keyword in help_keywords:
        if keyword in text_lower:
            logger.info("Detected help intent")
            return MessageIntent.HELP, None
    
    logger.info(f"Unknown intent for message: {text}")
    return MessageIntent.UNKNOWN, None


async def route_to_agent(intent: str, city: Optional[str]) -> Dict[str, Any]:
    """
    Route message to appropriate ADK agent
    
    Args:
        intent: Message intent
        city: City parameter
        
    Returns:
        Agent response
    """
    try:
        from multi_tool_agent.agent import weather_time_agent, traffic_agent
        
        if intent == MessageIntent.WEATHER:
            city = city or "New York"
            prompt = f"What's the weather in {city}?"
            logger.info(f"Routing to weather agent: {prompt}")
            
            response = weather_time_agent.run(prompt)
            return {
                "type": "weather",
                "city": city,
                "data": response,
                "status": "success"
            }
            
        elif intent == MessageIntent.TIME:
            city = city or "New York"
            prompt = f"What time is it in {city}?"
            logger.info(f"Routing to time agent: {prompt}")
            
            response = weather_time_agent.run(prompt)
            return {
                "type": "time",
                "city": city,
                "data": response,
                "status": "success"
            }
            
        elif intent == MessageIntent.TRAFFIC:
            city = city or "New York"
            prompt = f"How's the traffic in {city}?"
            logger.info(f"Routing to traffic agent: {prompt}")
            
            response = traffic_agent.run(prompt)
            return {
                "type": "traffic",
                "city": city,
                "data": response,
                "status": "success"
            }
            
        elif intent == MessageIntent.HELP:
            return {
                "type": "help",
                "data": {
                    "message": "I can help you with weather, time, and traffic information!",
                    "commands": [
                        "What's the weather in [city]?",
                        "What time is it in [city]?",
                        "How's the traffic in [city]?"
                    ]
                },
                "status": "success"
            }
            
        else:
            return {
                "type": "error",
                "data": {
                    "message": "I didn't understand that. Try asking about weather, time, or traffic!"
                },
                "status": "error"
            }
            
    except ImportError as e:
        logger.error(f"Failed to import agents: {e}")
        return {
            "type": "error",
            "data": {
                "message": "Agent service is temporarily unavailable"
            },
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Error routing to agent: {e}")
        return {
            "type": "error",
            "data": {
                "message": "An error occurred while processing your request"
            },
            "status": "error"
        }


async def process_teams_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process incoming Teams message
    
    Args:
        payload: Teams webhook payload
        
    Returns:
        Response to send back to Teams
    """
    try:
        text = payload.get("text", "").strip()
        user_info = payload.get("from", {})
        conversation = payload.get("conversation", {})
        
        logger.info(
            f"Processing message from user {user_info.get('name', 'Unknown')}: {text[:100]}",
            extra={
                "user_id": user_info.get("id"),
                "conversation_id": conversation.get("id")
            }
        )
        
        intent, city = parse_message_intent(text)
        
        agent_response = await route_to_agent(intent, city)
        
        try:
            from adaptive_cards import format_agent_response
            formatted_response = format_agent_response(agent_response)
        except ImportError:
            logger.warning("adaptive_cards module not found, returning raw response")
            formatted_response = {
                "type": "message",
                "text": str(agent_response.get("data", {}).get("message", "Response generated"))
            }
        
        return {
            "type": "message",
            "from": {
                "id": "bot",
                "name": "ADK Weather Bot"
            },
            "conversation": conversation,
            "recipient": user_info,
            "attachments": [formatted_response] if "attachments" not in formatted_response else formatted_response["attachments"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing Teams message: {e}", exc_info=True)
        
        return {
            "type": "message",
            "text": "Sorry, I encountered an error processing your message. Please try again.",
            "timestamp": datetime.utcnow().isoformat()
        }


async def validate_teams_payload(payload: Dict[str, Any]) -> bool:
    """
    Validate Teams webhook payload structure
    
    Args:
        payload: Webhook payload
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["type", "from", "conversation"]
    
    for field in required_fields:
        if field not in payload:
            logger.error(f"Missing required field: {field}")
            return False
    
    if payload.get("type") != "message":
        logger.info(f"Ignoring non-message type: {payload.get('type')}")
        return False
    
    return True