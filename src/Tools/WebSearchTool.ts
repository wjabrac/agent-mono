import { BaseTool } from "./BaseTool";
import { z } from "zod";

export class WebSearchTool extends BaseTool {
  name = "WebSearch";
  description = "Search the web for current information";
  schema = z.object({
    query: z.string().describe("Search query"),
  });

  protected async _execute(args: { query: string }): Promise<string> {
    const url = `https://duckduckgo.com/?q=${encodeURIComponent(
      args.query
    )}&format=json&no_redirect=1&no_html=1`;
    try {
      const res = await fetch(url);
      const data: any = await res.json();
      if (data.AbstractText) {
        return data.AbstractText;
      }
      if (Array.isArray(data.RelatedTopics)) {
        const texts = data.RelatedTopics.filter((t: any) => t.Text)
          .slice(0, 3)
          .map((t: any) => t.Text);
        if (texts.length) return texts.join("\n");
      }
      return "No results";
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      return `Search failed: ${msg}`;
    }
  }
}
