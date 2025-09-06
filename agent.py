"""
LangGraph Agent with Calendar Scheduling Tools and Short-term Memory
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict, Annotated
from dotenv import load_dotenv
import json

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

## calender tool imports
from calenderTool import get_events_between_start_and_end, set_calender_event
import datetime as dt

load_dotenv()
# os.environ["GOOGLE_API_KEY"] = os.getenv("gemini")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
)
tools = [get_events_between_start_and_end, set_calender_event]

llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

relevant_questions = ['meeting duration', 'meeting day' , 'meeting time']

def assistant(state : State):
  now = dt.datetime.now().isoformat() + 'Z'
  sys_msg = SystemMessage(content=f'''You are an Assistant that helps a user find a meeting time on Google calender through a back-and-forth conversation (each question at a time). You must be able to understand the user's needs, ask clarifying questions when information is
missing, and interact with a Google Calendar to find available slots. Current date is {now}. Only ask questions that relevant {relevant_questions} . Your Tone is Natural and Friendly . Do not sound Robotic  ''')
  response = llm_with_tools.invoke([sys_msg] + state["messages"])
  return {"messages": [response]}

checkpointer = InMemorySaver()
builder = StateGraph(MessagesState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")
react_graph = builder.compile(checkpointer=checkpointer)
config = {'configurable' : {'thread_id' : 1}}

def agent(message):
    response = react_graph.invoke({"messages" : [HumanMessage(content = message)]}, config)
    return response['messages'][-1].content