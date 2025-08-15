import { ToolRegistry } from "./Tools/ToolRegistry";
import { VectorMemory } from "./Memory/VectorMemory";
import { Planner } from "./Planner";
import { ResponseGenerator } from "./ResponseGenerator";
import { Security } from "./security";

export class Agent {
  constructor(
    private toolRegistry: ToolRegistry,
    private memory: VectorMemory,
    private planner: Planner,
    private generator: ResponseGenerator
  ) {}

  async executeTask(userInput: string): Promise<string> {
    try {
      Security.validateInput(userInput);

      const context = await this.memory.retrieveRelevant(userInput);

      const plan = await this.planner.generatePlan(userInput, context);

      const results: string[] = [];
      for (const step of plan.steps) {
        const tool = this.toolRegistry.getTool(step.tool);
        if (!tool) throw new Error(`Unknown tool: ${step.tool}`);

        const result = await tool.safeExecute(step.arguments);
        results.push(result);

        await this.memory.store(
          `Tool ${step.tool} executed with arguments: ${JSON.stringify(
            step.arguments
          )}. Result: ${result}`
        );
      }

      const response = await this.generator.generateResponse(
        userInput,
        results.join("\n"),
        context
      );

      await this.memory.store(`User: ${userInput}\nAgent: ${response}`);

      return response;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      await this.memory.store(`Error: ${errorMsg}`);
      return `Agent encountered an error: ${errorMsg}`;
    }
  }
}
