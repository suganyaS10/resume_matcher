from dotenv import load_dotenv

load_dotenv()

from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from anthropic import AsyncAnthropic
import asyncio

server_params = StdioServerParameters(command="python", args=["mcp_server.py"])
anthropic = AsyncAnthropic()

def to_claude_tool(tool):
  schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
  return {"name": tool.name, "description": tool.description, "input_schema": schema}

async def main():
  async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
      await session.initialize()

      mcp_tools = (await session.list_tools()).tools
      claude_tools = [to_claude_tool(tool) for tool in mcp_tools]

      prompt = """How well does my resume fit this job? Senior Backend Engineer on a payments
                platform. Ruby and SQL required, background jobs and PCI compliance,
                fraud detection a plus."""
      
      messages = [{"role": "user", "content": prompt}]
      
      while True:
        response = await anthropic.messages.create(
          model="claude-haiku-4-5",
          max_tokens=400,
          tools=claude_tools,
          messages=messages
        )

        if response.stop_reason != "tool_use":
          for content in response.content:
            if content.type == "text":
              print(f"CLAUDE: {content.text}")

          break

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
          if block.type == "tool_use":
            result = await session.call_tool(block.name, block.input)
            response = "".join(b.text for b in result.content if b.type == "text")
            results.append({
              "type": "tool_result",
              "tool_use_id": block.id,
              "content": response
            })

        messages.append({"role": "user", "content": results})

asyncio.run(main())         
        
