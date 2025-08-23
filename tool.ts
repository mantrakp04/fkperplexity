import { MultiServerMCPClient } from "@langchain/mcp-adapters";

const client = new MultiServerMCPClient({
  throwOnLoadError: true,
  prefixToolNameWithServerName: false,
  additionalToolNamePrefix: "",
  useStandardContentBlocks: true,
  mcpServers: {
    "browsermcp": {
      "command": "bunx",
      "args": ["@browsermcp/mcp@latest"]
    }
  },
});

export const tools = await client.getTools();
