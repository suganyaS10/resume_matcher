import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_parameters = StdioServerParameters(command="python", args=["mcp_server.py"])

async def main():
  async with stdio_client(server_parameters) as (read, write):
    async with ClientSession(read, write) as session:
      await session.initialize()

      tools = await session.list_tools()
      for tool in tools.tools:
        print(f"{tool.name} - {tool.description}")

      resources = await session.list_resources()
      for resource in resources.resources:
        print(f"{resource.uri}")

      prompts = await session.list_prompts()
      for prompt in prompts.prompts:
        print(f"{prompt.name}")

      jd = ("Senior Backend Engineer for a payments platform. "
                  "Ruby and SQL required; experience with background jobs and PCI compliance.")
      print("\nCALLING analyze_fit ...")

      result = await session.call_tool("analyze_fit", {"job_description": jd})
      for block in result.content:
        if block.type == "text":
          print(block.text)


if __name__ == "__main__":
  asyncio.run(main())




