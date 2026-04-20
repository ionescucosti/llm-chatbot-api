import json
import logging
from datetime import datetime

from openai import OpenAI

from core.config import settings
from core.prompts import TOOLS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


# Define available tools
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The timezone to get the time for (e.g., 'UTC', 'America/New_York')",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a mathematical calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a location (mock data for demo)",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country (e.g., 'London, UK')",
                    }
                },
                "required": ["location"],
            },
        },
    },
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool and return the result."""
    logger.info("Executing tool: %s with args: %s", tool_name, arguments)

    if tool_name == "get_current_time":
        timezone = arguments.get("timezone", "UTC")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return json.dumps({"time": current_time, "timezone": timezone})

    elif tool_name == "calculate":
        expression = arguments.get("expression", "")
        try:
            # Safe evaluation of mathematical expressions
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return json.dumps({"error": "Invalid characters in expression"})
            result = eval(expression)  # noqa: S307
            return json.dumps({"expression": expression, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    elif tool_name == "get_weather":
        location = arguments.get("location", "Unknown")
        # Mock weather data for demo purposes
        return json.dumps(
            {
                "location": location,
                "temperature": "22°C",
                "condition": "Partly cloudy",
                "humidity": "65%",
                "note": "This is mock data for demonstration purposes",
            }
        )

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


class ToolsService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_response(self, chat_history: list[dict]) -> str:
        """Generate a response using tools/function calling."""
        logger.info("Calling OpenAI API with tools model=%s", settings.openai_model)

        try:
            # Build messages for chat completion
            messages = [{"role": "system", "content": TOOLS_SYSTEM_PROMPT}]
            messages.extend(chat_history)

            # Initial call with tools
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=AVAILABLE_TOOLS,
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message

            # Check if the model wants to use tools
            if assistant_message.tool_calls:
                logger.info("Model requested %d tool calls", len(assistant_message.tool_calls))

                # Add assistant message to conversation
                messages.append(assistant_message)

                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    tool_result = execute_tool(tool_name, arguments)

                    # Add tool response to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        }
                    )

                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                )
                logger.info("OpenAI API tools response received")
                return final_response.choices[0].message.content or ""

            # No tool calls, return direct response
            logger.info("OpenAI API response received (no tools used)")
            return assistant_message.content or ""

        except Exception as e:
            logger.error("OpenAI API error in tools service: %s", str(e))
            raise
