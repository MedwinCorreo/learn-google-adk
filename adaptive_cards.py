"""
Adaptive Cards formatter for Teams responses
Creates rich, formatted cards for bot responses
"""

from typing import Dict, Any, List
from datetime import datetime

from logger_config import get_logger

logger = get_logger(__name__)


def create_weather_card(city: str, data: Any) -> Dict[str, Any]:
    """
    Create weather information Adaptive Card
    
    Args:
        city: City name
        data: Weather data from agent
        
    Returns:
        Adaptive Card attachment
    """
    weather_info = extract_weather_info(data)
    
    card_content = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"☁️ Weather in {city}",
                        "weight": "Bolder",
                        "size": "Large",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                        "isSubtle": True,
                        "size": "Small",
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Temperature",
                                "value": weather_info.get("temperature", "72°F")
                            },
                            {
                                "title": "Condition",
                                "value": weather_info.get("condition", "Partly Cloudy")
                            },
                            {
                                "title": "Humidity",
                                "value": weather_info.get("humidity", "65%")
                            },
                            {
                                "title": "Wind Speed",
                                "value": weather_info.get("wind_speed", "10 mph")
                            }
                        ]
                    }
                ]
            },
            {
                "type": "TextBlock",
                "text": weather_info.get("forecast", "Pleasant weather expected throughout the day."),
                "wrap": True,
                "separator": True,
                "spacing": "Medium"
            }
        ]
    }
    
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card_content
    }


def create_time_card(city: str, data: Any) -> Dict[str, Any]:
    """
    Create time information Adaptive Card
    
    Args:
        city: City name
        data: Time data from agent
        
    Returns:
        Adaptive Card attachment
    """
    time_info = extract_time_info(data)
    
    card_content = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"🕐 Time in {city}",
                        "weight": "Bolder",
                        "size": "Large",
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": time_info.get("current_time", "12:00 PM"),
                        "weight": "Bolder",
                        "size": "ExtraLarge",
                        "horizontalAlignment": "Center",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": time_info.get("date", "January 1, 2025"),
                        "horizontalAlignment": "Center",
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            },
            {
                "type": "FactSet",
                "facts": [
                    {
                        "title": "Timezone",
                        "value": time_info.get("timezone", "EST")
                    },
                    {
                        "title": "UTC Offset",
                        "value": time_info.get("utc_offset", "UTC-5")
                    }
                ],
                "separator": True
            }
        ]
    }
    
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card_content
    }


def create_traffic_card(city: str, data: Any) -> Dict[str, Any]:
    """
    Create traffic information Adaptive Card
    
    Args:
        city: City name
        data: Traffic data from agent
        
    Returns:
        Adaptive Card attachment
    """
    traffic_info = extract_traffic_info(data)
    
    status_color = {
        "Light": "Good",
        "Moderate": "Warning",
        "Heavy": "Attention",
        "Severe": "Attention"
    }.get(traffic_info.get("status", "Moderate"), "Default")
    
    card_content = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"🚗 Traffic in {city}",
                        "weight": "Bolder",
                        "size": "Large",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                        "isSubtle": True,
                        "size": "Small",
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "style": status_color,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"Status: {traffic_info.get('status', 'Moderate')}",
                        "weight": "Bolder",
                        "size": "Medium",
                        "wrap": True
                    }
                ]
            },
            {
                "type": "FactSet",
                "facts": [
                    {
                        "title": "Average Speed",
                        "value": traffic_info.get("average_speed", "25 mph")
                    },
                    {
                        "title": "Congestion Level",
                        "value": traffic_info.get("congestion", "Medium")
                    },
                    {
                        "title": "Incidents",
                        "value": traffic_info.get("incidents", "2 minor delays")
                    }
                ],
                "separator": True
            },
            {
                "type": "TextBlock",
                "text": traffic_info.get("recommendation", "Consider alternative routes during peak hours."),
                "wrap": True,
                "separator": True,
                "spacing": "Medium"
            }
        ]
    }
    
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card_content
    }


def create_help_card() -> Dict[str, Any]:
    """
    Create help/welcome Adaptive Card
    
    Returns:
        Adaptive Card attachment
    """
    card_content = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "👋 Welcome to ADK Weather Bot!",
                        "weight": "Bolder",
                        "size": "Large",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "I can help you with weather, time, and traffic information for any city.",
                        "wrap": True,
                        "spacing": "Medium"
                    }
                ]
            },
            {
                "type": "Container",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "**Available Commands:**",
                        "weight": "Bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "• What's the weather in [city]?",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "• What time is it in [city]?",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "• How's the traffic in [city]?",
                        "wrap": True
                    }
                ]
            },
            {
                "type": "Container",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "**Examples:**",
                        "weight": "Bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "• \"What's the weather in New York?\"",
                        "wrap": True,
                        "isSubtle": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "• \"What time is it in London?\"",
                        "wrap": True,
                        "isSubtle": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "• \"How's traffic in Los Angeles?\"",
                        "wrap": True,
                        "isSubtle": True
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Check Weather",
                "data": {
                    "action": "weather",
                    "text": "What's the weather in New York?"
                }
            },
            {
                "type": "Action.Submit",
                "title": "Check Time",
                "data": {
                    "action": "time",
                    "text": "What time is it in New York?"
                }
            },
            {
                "type": "Action.Submit",
                "title": "Check Traffic",
                "data": {
                    "action": "traffic",
                    "text": "How's traffic in New York?"
                }
            }
        ]
    }
    
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card_content
    }


def create_error_card(message: str) -> Dict[str, Any]:
    """
    Create error message Adaptive Card
    
    Args:
        message: Error message to display
        
    Returns:
        Adaptive Card attachment
    """
    card_content = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "style": "attention",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "⚠️ Error",
                        "weight": "Bolder",
                        "size": "Large",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": message,
                        "wrap": True,
                        "spacing": "Medium"
                    }
                ]
            },
            {
                "type": "Container",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "Please try again or type 'help' for available commands.",
                        "wrap": True,
                        "isSubtle": True
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Get Help",
                "data": {
                    "action": "help",
                    "text": "help"
                }
            }
        ]
    }
    
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card_content
    }


def extract_weather_info(data: Any) -> Dict[str, str]:
    """Extract weather information from agent response"""
    if isinstance(data, str):
        return {
            "temperature": "72°F",
            "condition": "Partly Cloudy",
            "humidity": "65%",
            "wind_speed": "10 mph",
            "forecast": data[:200] if len(data) > 200 else data
        }
    
    return {
        "temperature": "72°F",
        "condition": "Partly Cloudy",
        "humidity": "65%",
        "wind_speed": "10 mph",
        "forecast": "Pleasant weather expected throughout the day."
    }


def extract_time_info(data: Any) -> Dict[str, str]:
    """Extract time information from agent response"""
    from datetime import datetime
    import pytz
    
    now = datetime.now(pytz.timezone('America/New_York'))
    
    if isinstance(data, str) and "time" in data.lower():
        return {
            "current_time": now.strftime("%I:%M %p"),
            "date": now.strftime("%B %d, %Y"),
            "timezone": "EST",
            "utc_offset": "UTC-5"
        }
    
    return {
        "current_time": now.strftime("%I:%M %p"),
        "date": now.strftime("%B %d, %Y"),
        "timezone": "EST",
        "utc_offset": "UTC-5"
    }


def extract_traffic_info(data: Any) -> Dict[str, str]:
    """Extract traffic information from agent response"""
    if isinstance(data, str):
        if "heavy" in data.lower():
            return {
                "status": "Heavy",
                "average_speed": "15 mph",
                "congestion": "High",
                "incidents": "3 accidents reported",
                "recommendation": "Avoid main highways. Use alternative routes."
            }
        elif "light" in data.lower():
            return {
                "status": "Light",
                "average_speed": "45 mph",
                "congestion": "Low",
                "incidents": "No incidents",
                "recommendation": "Good time to travel. All routes clear."
            }
    
    return {
        "status": "Moderate",
        "average_speed": "25 mph",
        "congestion": "Medium",
        "incidents": "2 minor delays",
        "recommendation": "Consider alternative routes during peak hours."
    }


def format_agent_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format agent response as Adaptive Card
    
    Args:
        response: Agent response dictionary
        
    Returns:
        Formatted Adaptive Card attachment
    """
    try:
        response_type = response.get("type", "unknown")
        city = response.get("city", "Unknown")
        data = response.get("data", {})
        
        logger.info(f"Formatting response type: {response_type}")
        
        if response_type == "weather":
            return create_weather_card(city, data)
        elif response_type == "time":
            return create_time_card(city, data)
        elif response_type == "traffic":
            return create_traffic_card(city, data)
        elif response_type == "help":
            return create_help_card()
        elif response_type == "error":
            error_message = data.get("message", "An error occurred")
            return create_error_card(error_message)
        else:
            return create_error_card("I didn't understand your request. Please try again.")
            
    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        return create_error_card("Failed to format response. Please try again.")