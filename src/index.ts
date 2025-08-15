import { Agent } from "./Agent";
import { ToolRegistry } from "./Tools/ToolRegistry";
import { WebSearchTool } from "./Tools/WebSearchTool";
import { FileAnalysisTool } from "./Tools/FileAnalysisTool";
import { CalculatorTool } from "./Tools/CalculatorTool";
import { VectorMemory } from "./Memory/VectorMemory";
import { Planner } from "./Planner";
import { ResponseGenerator } from "./ResponseGenerator";
import { DirectResponseTool } from "./Tools/DirectResponseTool";
import readline from "readline";

const toolRegistry = new ToolRegistry();
toolRegistry.registerTool(new WebSearchTool());
toolRegistry.registerTool(new FileAnalysisTool());
toolRegistry.registerTool(new CalculatorTool());
toolRegistry.registerTool(new DirectResponseTool());

const memory = new VectorMemory();
const planner = new Planner();
const generator = new ResponseGenerator();

const agent = new Agent(toolRegistry, memory, planner, generator);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

async function main() {
  console.log('Agent initialized. Type your query or "exit" to quit.');

  while (true) {
    const input = await new Promise<string>((resolve) =>
      rl.question('\nUser: ', resolve)
    );

    if (input.toLowerCase() === 'exit') break;

    try {
      process.stdout.write('Agent: ');
      const response = await agent.executeTask(input);

      for (const char of response) {
        process.stdout.write(char);
        await new Promise((resolve) => setTimeout(resolve, 20));
      }
      process.stdout.write('\n');
    } catch (error) {
      console.error(`\nError: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  rl.close();
  console.log('Session ended');
}

memory.initialize().then(() => {
  main().catch(console.error);
});
