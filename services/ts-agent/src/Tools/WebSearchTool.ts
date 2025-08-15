import { BaseTool } from "./BaseTool";
import { z } from "zod";

export class WebSearchTool extends BaseTool {
  name = "WebSearch";
  description = "Search the web using DuckDuckGo";
  schema = z.object({
    query: z.string().describe("Search query")
  });

  protected async _execute(args: { query: string }): Promise<string> {
    const response = await fetch(`https://api.duckduckgo.com/?q=${encodeURIComponent(args.query)}&format=json`);
    const data = await response.json();

    return (
      data.Results.slice(0, 3)
        .map((r: any) => `• ${r.Text} (${r.FirstURL})`)
        .join('\n') || "No results found"
    );
  }
}
