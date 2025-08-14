import { BaseTool } from "./BaseTool";

export class ToolRegistry {
  private tools: Map<string, BaseTool> = new Map();

  registerTool(tool: BaseTool) {
    this.tools.set(tool.name, tool);
  }

  getTool(name: string): BaseTool | undefined {
    return this.tools.get(name);
  }

  listTools(): BaseTool[] {
    return Array.from(this.tools.values());
  }
}
