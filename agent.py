"""
Agent Logic Built From Scratch with Optimized Memory and a Tool-Calling Loop.
The memory is now automatically summarized when the conversation gets too long.
"""

import os
from typing import List
from dotenv import load_dotenv
import tiktoken  # Added for accurate token counting

# LangChain imports for message types and the LLM
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
    AnyMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI

# Import calendar tools
from calenderTool import get_events_between_start_and_end, set_calender_event, find_event_by_name, get_current_date_time , update_event, delete_event

# Load environment variables
load_dotenv()


class SchedulingAgent:
    """
    A robust, stateful agent that manages conversation and tool use from scratch,
    now with intelligent memory summarization.
    """

    def __init__(self, tools, system_prompt=""):
        """
        Initializes the agent with its tools, system prompt, LLM, and memory logic.
        """
        self.system_prompt = SystemMessage(content=system_prompt)
        self.tools = {tool.name: tool for tool in tools}
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        self.llm_with_tools = self.llm.bind_tools(tools)
        self.memory: List[AnyMessage] = []

        # --- New Memory Optimization Attributes ---
        # Using tiktoken for accurate token counting (standard for many LLMs)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.summarization_threshold = 8000  # Trigger summarization after 8k tokens
        self.messages_to_retain = 10  # Keep the last 5 user/AI turns

    def _get_token_count(self) -> int:
        """Calculates the total token count of the current memory."""
        # Simple implementation: concatenate message content and encode
        full_text = " ".join([msg.content for msg in self.memory if isinstance(msg.content, str)])
        return len(self.tokenizer.encode(full_text))

    def _handle_memory(self):
        """
        Checks the memory size and summarizes it if it exceeds the threshold.
        This is the core of the new memory optimization logic.
        """
        token_count = self._get_token_count()
        print(f"--- Current Token Count: {token_count} ---")

        if token_count <= self.summarization_threshold:
            # Memory is within limits, no action needed
            return

        print(f"--- Token count ({token_count}) exceeds threshold ({self.summarization_threshold}). Summarizing memory... ---")

        # 1. Separate the messages to be summarized from those to be retained
        messages_to_summarize = self.memory[:-self.messages_to_retain]
        messages_to_keep = self.memory[-self.messages_to_retain:]

        # 2. Create the prompt for the summarization call
        summarization_prompt = (
            "You are a helpful assistant. Summarize the key facts, entities, and user decisions "
            "from this conversation history. Key information includes event names, attendee names, "
            "preferred times, and meeting durations. The summary should be concise and clear."
            "\n\n--- Conversation to Summarize ---\n"
            + "\n".join([f"{msg.__class__.__name__}: {msg.content}" for msg in messages_to_summarize])
        )

        # 3. Call the base LLM to get the summary
        summary_text = self.llm.invoke(summarization_prompt).content
        
        # 4. Create a new SystemMessage containing the summary
        summary_message = SystemMessage(
            content=f"Summary of the conversation so far:\n{summary_text}"
        )

        # 5. Rebuild the memory with the summary followed by the recent messages
        self.memory = [summary_message] + messages_to_keep
        print("--- Memory has been successfully summarized. ---")


    def _execute_tool_calls(self, ai_message: AIMessage) -> List[ToolMessage]:
        """
        Executes tool calls requested by the LLM and returns the results.
        """
        tool_messages = []
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_to_call = self.tools.get(tool_name)

            if tool_to_call:
                try:
                    tool_output = tool_to_call.invoke(tool_call["args"])
                    tool_messages.append(
                        ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                    )
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    tool_messages.append(
                        ToolMessage(content=error_msg, tool_call_id=tool_call["id"])
                    )
            else:
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: Tool '{tool_name}' not found.",
                        tool_call_id=tool_call["id"],
                    )
                )
        return tool_messages

    def invoke(self, message: str) -> str:
        """
        The main entry point for the agent. It processes a user message,
        manages the conversation loop, and returns the final response.
        """
        # 1. Add the new user message to the conversation memory
        self.memory.append(HumanMessage(content=message))

        # 2. **NEW STEP**: Handle memory summarization if needed
        self._handle_memory()

        # 3. Start the core agent loop
        while True:
            for msg in self.memory:
                print(f"{msg.__class__.__name__}: {msg.content}")
            print("--- Invoking LLM with current memory ---")
            response: AIMessage = self.llm_with_tools.invoke(
                [self.system_prompt] + self.memory
            )

            if not response.tool_calls:
                self.memory.append(response)
                return response.content

            self.memory.append(response)
            tool_results = self._execute_tool_calls(response)
            self.memory.extend(tool_results)
            # The loop will repeat with the tool results in memory


# --- Agent Initialization ---

def get_agent():
    """Initializes the scheduling agent."""
    with open('prompt.txt', "r", encoding="utf-8") as f:
        system_prompt = f.read()
    system_prompt = system_prompt.replace("{current_datetime_str}", get_current_date_time('datetime'))
    tools = [get_events_between_start_and_end, set_calender_event, find_event_by_name , get_current_date_time, update_event, delete_event]
    
    agent_instance = SchedulingAgent(tools=tools, system_prompt=system_prompt)
    return agent_instance

my_agent = get_agent()

def agent(message):
    return my_agent.invoke(message)

# Example usage (for testing)
if __name__ == "__main__":
    my_agent = get_agent()
    
    # First turn
    response1 = my_agent.invoke("Hey, I need to schedule a meeting with my colleague, Sarah.")
    print(f"Agent: {response1}")
    
    # Second turn
    response2 = my_agent.invoke("For one hour, please.")
    print(f"Agent: {response2}")
    
    # The agent's memory now contains the full history
    print("\n--- Agent Memory ---")
    for msg in my_agent.memory:
        print(f"{msg.__class__.__name__}: {msg.content}")

