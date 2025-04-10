import streamlit as st
import asyncio
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.callbacks.base import BaseCallbackHandler
from langgraph.prebuilt import create_react_agent
from utils.helpers import aed_to_usd


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        self.container.markdown(self.text + "▌")  # ▌ cursor effect


async def get_response(user_input, container):
    # Initialize stream handler
    handler = StreamHandler(container)

    # Set up LLM with streaming enabled
    llm = ChatOpenAI(
        model="gpt-4o-mini", temperature=0.7, streaming=True, callbacks=[handler]
    )

    # Create agent with the LLM
    agent = create_react_agent(
        model=llm, tools=[aed_to_usd], prompt="Helpful Assistant"
    )

    # Stream the response asynchronously and yield each chunk
    content = ""
    async for chunk, _ in agent.astream({"messages": [HumanMessage(content=user_input)]}, stream_mode="messages"):
        content += chunk.content
        yield content


# Streamlit UI Setup
st.title("🔁 LangChain Streaming in Streamlit")

user_input = st.text_input("Ask something:")

if user_input:
    container = st.empty()

    # Consume the async generator and display output progressively
    async def stream_response():
        async for chunk in get_response(user_input, container):
            # Update container with each chunk of text
            container.markdown(chunk + "▌")

    # Start streaming asynchronously
    # asyncio.run(stream_response())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream_response())

