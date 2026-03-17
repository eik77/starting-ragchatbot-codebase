import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    MAX_TOOL_ROUNDS = 2

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **Up to 2 sequential searches per query** — use a second search only when the first result is insufficient or the question requires information from two distinct topics or courses.
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **Course outline/structure questions**: Use the `get_course_outline` tool when the user asks about a course's structure, outline, or lesson list. Return the course title, course link, and the numbered list of lessons exactly as provided.
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Agentic loop: allow up to MAX_TOOL_ROUNDS tool-use rounds
        messages = api_params["messages"].copy()
        rounds = 0
        while response.stop_reason == "tool_use" and tool_manager is not None and rounds < self.MAX_TOOL_ROUNDS:
            # Append assistant turn
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        result = tool_manager.execute_tool(block.name, **block.input)
                    except Exception as e:
                        result = f"Tool execution failed: {e}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "user", "content": tool_results})
            rounds += 1

            # Next call keeps tools available
            loop_params = {
                **self.base_params,
                "messages": messages,
                "system": api_params["system"],
                "tools": api_params["tools"],
                "tool_choice": {"type": "auto"}
            }
            response = self.client.messages.create(**loop_params)

        # If Claude returned a text answer, return it directly
        if response.stop_reason != "tool_use":
            if response.content and hasattr(response.content[0], 'text'):
                return response.content[0].text
            return "I was unable to generate a response."

        # Max rounds hit and Claude still wants tools — force a final synthesis call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": api_params["system"]
        }
        final_response = self.client.messages.create(**final_params)
        if final_response.content and hasattr(final_response.content[0], 'text'):
            return final_response.content[0].text
        return "I was unable to generate a response."