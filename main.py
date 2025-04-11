from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import asyncio
from dotenv import load_dotenv
load_dotenv()


from llama_index.core.workflow import Workflow, Context, StartEvent, StopEvent, step, Event
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import FunctionTool, BaseTool, ToolSelection, ToolOutput


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    escalate: bool = False

memory_store: Dict[str, ChatMemoryBuffer] = {}


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

tools: List[BaseTool] = [
    FunctionTool.from_defaults(name="pricing_agent", fn=pricing_tool),
    FunctionTool.from_defaults(name="scheduling_agent", fn=scheduling_tool),
    FunctionTool.from_defaults(name="vendor_validation_agent", fn=vendor_validation_tool),
    FunctionTool.from_defaults(name="vendor_ingestion_agent", fn=vendor_ingestion_tool),
    FunctionTool.from_defaults(name="obituary_agent", fn=obituary_tool),
    FunctionTool.from_defaults(name="sentiment_agent", fn=sentiment_check_tool),
    FunctionTool.from_defaults(name="payment_agent", fn=payment_tool),
]

llm = OpenAI(model="gpt-4o-mini")

class InputEvent(Event):
    input: list[ChatMessage]

class StreamEvent(Event):
    delta: str

class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]

class FunctionCallingAgent(Workflow):
    def __init__(self, llm, tools, memory):
        super().__init__()
        self.llm = llm
        self.tools = tools
        self.memory = memory

    @step
    async def prepare_chat_history(self, ctx: Context, ev: StartEvent) -> InputEvent:
        self.memory.put(ChatMessage(role="user", content=ev.input))
        return InputEvent(input=self.memory.get_all())

    @step
    async def handle_llm_input(self, ctx: Context, ev: InputEvent) -> ToolCallEvent | StopEvent:
        response_stream = await self.llm.astream_chat_with_tools(self.tools, chat_history=ev.input)
        async for response in response_stream:
            ctx.write_event_to_stream(StreamEvent(delta=response.delta or ""))
        self.memory.put(response.message)
        tool_calls = self.llm.get_tool_calls_from_response(response, error_on_no_tool_call=False)
        if not tool_calls:
            return StopEvent(result={"response": response, "sources": []})
        return ToolCallEvent(tool_calls=tool_calls)

    @step
    async def handle_tool_calls(self, ctx: Context, ev: ToolCallEvent) -> InputEvent:
        tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}
        for tool_call in ev.tool_calls:
            tool = tools_by_name.get(tool_call.tool_name)
            if not tool:
                self.memory.put(ChatMessage(role="tool", content=f"{tool_call.tool_name} not found"))
                continue
            output = tool(**tool_call.tool_kwargs)
            self.memory.put(ChatMessage(role="tool", content=output.content))
        return InputEvent(input=self.memory.get_all())

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    memory = memory_store.setdefault(req.user_id, ChatMemoryBuffer.from_defaults(llm=llm))
    agent = FunctionCallingAgent(llm=llm, tools=tools, memory=memory)

    sentiment = sentiment_check_tool(req.message)
    if "Distress Detected" in sentiment:
        return ChatResponse(response="I'm sensing distress. Escalating to human support.", escalate=True)

    result = await agent.run(input=req.message)
    response_text = result["response"].message.content

    return ChatResponse(response=response_text)
