import { Agent } from "./Agent";
import { ToolRegistry } from "./Tools/ToolRegistry";
import { WebSearchTool } from "./Tools/WebSearchTool";
import { FileAnalysisTool } from "./Tools/FileAnalysisTool";
import { CalculatorTool } from "./Tools/CalculatorTool";
import { PersistentVectorMemory } from "./Memory/PersistentVectorMemory";
import { Planner } from "./Planner";
import { ResponseGenerator } from "./ResponseGenerator";
import { DirectResponseTool } from "./Tools/DirectResponseTool";

export function createDefaultAgent(): { agent: Agent; memory: PersistentVectorMemory } {
  const toolRegistry = new ToolRegistry();
  toolRegistry.registerTool(new WebSearchTool());
  toolRegistry.registerTool(new FileAnalysisTool());
  toolRegistry.registerTool(new CalculatorTool());
  toolRegistry.registerTool(new DirectResponseTool());

  const memory = new PersistentVectorMemory();
  const planner = new Planner();
  const generator = new ResponseGenerator();

  return { agent: new Agent(toolRegistry, memory, planner, generator), memory };
}
