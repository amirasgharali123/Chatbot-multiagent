# from typing import Any, List
# import asyncio
# import os
# from dotenv import load_dotenv
# load_dotenv()


# from llama_index.core.workflow import (
#     Context,
#     Workflow,
#     StartEvent,
#     StopEvent,
#     step,
#     Event,
# )
# from llama_index.llms.openai import OpenAI
# from llama_index.core.llms import ChatMessage
# from llama_index.core.memory import ChatMemoryBuffer
# from llama_index.core.tools import FunctionTool, BaseTool, ToolSelection, ToolOutput

# llm = OpenAI(model="gpt-4o-mini")

# class InputEvent(Event):
#     input: list[ChatMessage]

# class StreamEvent(Event):
#     delta: str

# class ToolCallEvent(Event):
#     tool_calls: list[ToolSelection]

# class FunctionOutputEvent(Event):
#     output: ToolOutput


# def pricing_tool(query: str) -> str:
#     return "Eco-friendly funeral package: $4,700 including casket, service, and flowers."

# def scheduling_tool(query: str) -> str:
#     return "Thursday is available at 10am and 2pm. Shall I book one?"

# def vendor_validation_tool(query: str) -> str:
#     return "All vendors validated with 95% confidence."

# def vendor_ingestion_tool(query: str) -> str:
#     return "Vendor database updated from latest APIs."

# def obituary_tool(query: str) -> str:
#     return "Here’s a draft: ‘John Doe, 67, loved jazz and gardening…’"

# def sentiment_check_tool(query: str) -> str:
#     if any(word in query.lower() for word in ["confused", "sad", "upset", "don't get it"]):
#         return "Distress Detected: Escalate to human support."
#     return "Sentiment normal."

# def payment_tool(query: str) -> str:
#     return "Escrow of $1,000 processed. Transaction ID: abc123."


# tools: List[BaseTool] = [
#     FunctionTool.from_defaults(name="pricing_agent", fn=pricing_tool,
#         description="Calculate costs and bundle funeral services with discounts."),
#     FunctionTool.from_defaults(name="scheduling_agent", fn=scheduling_tool,
#         description="Check vendor availability and propose times for services."),
#     FunctionTool.from_defaults(name="vendor_validation_agent", fn=vendor_validation_tool,
#         description="Ensure vendors are legitimate, stocked, and compliant."),
#     FunctionTool.from_defaults(name="vendor_ingestion_agent", fn=vendor_ingestion_tool,
#         description="Pull in updated vendor pricing and inventory data."),
#     FunctionTool.from_defaults(name="obituary_agent", fn=obituary_tool,
#         description="Write an obituary based on user-supplied info."),
#     FunctionTool.from_defaults(name="sentiment_agent", fn=sentiment_check_tool,
#         description="Detect user sentiment and escalate if needed."),
#     FunctionTool.from_defaults(name="payment_agent", fn=payment_tool,
#         description="Handle payment and escrow initiation requests."),
# ]


# class FunctionCallingAgent(Workflow):
#     def __init__(
#         self,
#         *args: Any,
#         llm: OpenAI | None = None,
#         tools: List[BaseTool] | None = None,
#         **kwargs: Any,
#     ) -> None:
#         super().__init__(*args, **kwargs)
#         self.tools = tools or []
#         self.llm = llm or OpenAI()
#         assert self.llm.metadata.is_function_calling_model

#     @step
#     async def prepare_chat_history(self, ctx: Context, ev: StartEvent) -> InputEvent:
#         await ctx.set("sources", [])

#         memory = await ctx.get("memory", default=None)
#         if not memory:
#             memory = ChatMemoryBuffer.from_defaults(llm=self.llm)

#         user_msg = ChatMessage(role="user", content=ev.input)
#         print("user message Amir here : ",user_msg)
#         memory.put(user_msg)
#         await ctx.set("memory", memory)

#         return InputEvent(input=memory.get())

#     @step
#     async def handle_llm_input(self, ctx: Context, ev: InputEvent) -> ToolCallEvent | StopEvent:
#         chat_history = ev.input
#         response_stream = await self.llm.astream_chat_with_tools(self.tools, chat_history=chat_history)

#         async for response in response_stream:
#             ctx.write_event_to_stream(StreamEvent(delta=response.delta or ""))

#         memory = await ctx.get("memory")
#         memory.put(response.message)
#         await ctx.set("memory", memory)

#         tool_calls = self.llm.get_tool_calls_from_response(response, error_on_no_tool_call=False)
#         if not tool_calls:
#             sources = await ctx.get("sources", default=[])
#             return StopEvent(result={"response": response, "sources": sources})
#         return ToolCallEvent(tool_calls=tool_calls)

#     @step
#     async def handle_tool_calls(self, ctx: Context, ev: ToolCallEvent) -> InputEvent:
#         tool_calls = ev.tool_calls
#         tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}

#         tool_msgs = []
#         sources = await ctx.get("sources", default=[])

#         for tool_call in tool_calls:
#             tool = tools_by_name.get(tool_call.tool_name)
#             additional_kwargs = {"tool_call_id": tool_call.tool_id, "name": tool_call.tool_name}

#             if not tool:
#                 tool_msgs.append(ChatMessage(role="tool", content=f"Tool {tool_call.tool_name} does not exist", additional_kwargs=additional_kwargs))
#                 continue

#             try:
#                 tool_output = tool(**tool_call.tool_kwargs)
#                 sources.append(tool_output)
#                 tool_msgs.append(ChatMessage(role="tool", content=tool_output.content, additional_kwargs=additional_kwargs))
#             except Exception as e:
#                 tool_msgs.append(ChatMessage(role="tool", content=f"Error in tool call: {e}", additional_kwargs=additional_kwargs))

#         memory = await ctx.get("memory")
#         for msg in tool_msgs:
#             memory.put(msg)
#         await ctx.set("sources", sources)
#         await ctx.set("memory", memory)

#         return InputEvent(input=memory.get())


# user_inputs = [
#     "Hi, I’m looking for a funeral plan under $5,000, eco-friendly, in Austin TX, next Thursday.",
#     "Can you show me available times?",
#     "This is a lot and I'm feeling really confused...",
#     "Can I now make a deposit?",
# ]

# agent = FunctionCallingAgent(tools=tools, llm=llm)

# async def run_conversation():
#     for user_input in user_inputs:
#         print(f"\n🧍 User: {user_input}")
        
#         sentiment = sentiment_check_tool(user_input)
#         if "Distress Detected" in sentiment:
#             print("🤖 Sentiment Agent: Distress detected! Escalating to human support.")
#             print("🧑‍💼 Human staff notified via dashboard or Slack.")
#             continue

#         result = await agent.run(input=user_input)
#         print("🤖 Renidy AI:", result["response"].message.content)

# if __name__ == "__main__":
#     asyncio.run(run_conversation())


from typing import Any, List
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
    Event,
)
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import FunctionTool, BaseTool, ToolSelection, ToolOutput

# Load OpenAI key from environment
llm = OpenAI(model="gpt-4o-mini")

# ========== Define Events ==========
class InputEvent(Event):
    input: list[ChatMessage]

class StreamEvent(Event):
    delta: str

class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]

class FunctionOutputEvent(Event):
    output: ToolOutput

# ========== Define Tool Functions ==========
def pricing_tool(query: str) -> str:
    return "Eco-friendly funeral package: $4,700 including casket, service, and flowers."

def scheduling_tool(query: str) -> str:
    return "Thursday is available at 10am and 2pm. Shall I book one?"

def vendor_validation_tool(query: str) -> str:
    return "All vendors validated with 95% confidence."

def vendor_ingestion_tool(query: str) -> str:
    return "Vendor database updated from latest APIs."

def obituary_tool(query: str) -> str:
    return "Here’s a draft: ‘John Doe, 67, loved jazz and gardening…’"

def sentiment_check_tool(query: str) -> str:
    if any(word in query.lower() for word in ["confused", "sad", "upset", "don't get it"]):
        return "Distress Detected: Escalate to human support."
    return "Sentiment normal."

def payment_tool(query: str) -> str:
    return "Escrow of $1,000 processed. Transaction ID: abc123."

# ========== Register Tools ==========
tools: List[BaseTool] = [
    FunctionTool.from_defaults(name="pricing_agent", fn=pricing_tool,
        description="Calculate costs and bundle funeral services with discounts."),
    FunctionTool.from_defaults(name="scheduling_agent", fn=scheduling_tool,
        description="Check vendor availability and propose times for services."),
    FunctionTool.from_defaults(name="vendor_validation_agent", fn=vendor_validation_tool,
        description="Ensure vendors are legitimate, stocked, and compliant."),
    FunctionTool.from_defaults(name="vendor_ingestion_agent", fn=vendor_ingestion_tool,
        description="Pull in updated vendor pricing and inventory data."),
    FunctionTool.from_defaults(name="obituary_agent", fn=obituary_tool,
        description="Write an obituary based on user-supplied info."),
    FunctionTool.from_defaults(name="sentiment_agent", fn=sentiment_check_tool,
        description="Detect user sentiment and escalate if needed."),
    FunctionTool.from_defaults(name="payment_agent", fn=payment_tool,
        description="Handle payment and escrow initiation requests."),
]

# ========== Define Agent ==========
class FunctionCallingAgent(Workflow):
    def __init__(self, *args: Any, llm: OpenAI | None = None, tools: List[BaseTool] | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.tools = tools or []
        self.llm = llm or OpenAI()
        assert self.llm.metadata.is_function_calling_model

    @step
    async def prepare_chat_history(self, ctx: Context, ev: StartEvent) -> InputEvent:
        await ctx.set("sources", [])
        memory = await ctx.get("memory", default=None)
        if not memory:
            memory = ChatMemoryBuffer.from_defaults(llm=self.llm)
        user_msg = ChatMessage(role="user", content=ev.input)
        memory.put(user_msg)
        await ctx.set("memory", memory)
        return InputEvent(input=memory.get())

    @step
    async def handle_llm_input(self, ctx: Context, ev: InputEvent) -> ToolCallEvent | StopEvent:
        chat_history = ev.input
        response_stream = await self.llm.astream_chat_with_tools(self.tools, chat_history=chat_history)
        async for response in response_stream:
            ctx.write_event_to_stream(StreamEvent(delta=response.delta or ""))

        memory = await ctx.get("memory")
        memory.put(response.message)
        await ctx.set("memory", memory)

        tool_calls = self.llm.get_tool_calls_from_response(response, error_on_no_tool_call=False)
        if not tool_calls:
            sources = await ctx.get("sources", default=[])
            return StopEvent(result={"response": response, "sources": sources})
        return ToolCallEvent(tool_calls=tool_calls)

    @step
    async def handle_tool_calls(self, ctx: Context, ev: ToolCallEvent) -> InputEvent:
        tool_calls = ev.tool_calls
        tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}

        tool_msgs = []
        sources = await ctx.get("sources", default=[])

        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call.tool_name)
            additional_kwargs = {"tool_call_id": tool_call.tool_id, "name": tool_call.tool_name}

            if not tool:
                tool_msgs.append(ChatMessage(role="tool", content=f"Tool {tool_call.tool_name} does not exist", additional_kwargs=additional_kwargs))
                continue

            try:
                tool_output = tool(**tool_call.tool_kwargs)
                sources.append(tool_output)
                tool_msgs.append(ChatMessage(role="tool", content=tool_output.content, additional_kwargs=additional_kwargs))
            except Exception as e:
                tool_msgs.append(ChatMessage(role="tool", content=f"Error in tool call: {e}", additional_kwargs=additional_kwargs))

        memory = await ctx.get("memory")
        for msg in tool_msgs:
            memory.put(msg)
        await ctx.set("sources", sources)
        await ctx.set("memory", memory)

        return InputEvent(input=memory.get())

# ========== FastAPI Setup ==========
app = FastAPI()
agent = FunctionCallingAgent(tools=tools, llm=llm)

# Enable CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Change if deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    message: str

@app.post("/chat")
async def chat(chat_input: ChatInput):
    sentiment = sentiment_check_tool(chat_input.message)
    if "Distress Detected" in sentiment:
        return {
            "response": "We're here for you. Let me connect you with a human advisor.",
            "escalate": True,
        }

    result = await agent.run(input=chat_input.message)
    return {"response": result["response"].message.content, "escalate": False}

# ========== Main ==========
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
