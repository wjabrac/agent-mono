import repl from 'repl';
import { ToolRegistry } from './Tools/ToolRegistry';
import { WebSearchTool } from './Tools/WebSearchTool';
import { FileAnalysisTool } from './Tools/FileAnalysisTool';
import { CalculatorTool } from './Tools/CalculatorTool';
import { VectorMemory } from './Memory/VectorMemory';
import { Agent } from './Agent'; // Your existing Agent class
import { createSecureContext } from 'tls';
import vm from 'vm';

// Security setup
const SECURITY_CONFIG = {
  allowedModules: ['fs/promises', 'path', 'pdf-parse', 'mathjs'],
  blockedKeywords: ['child_process', 'process', 'exec', 'spawn']
};

class SecureSandbox {
  static run(code: string, context: object = {}): any {
    const sandbox = {
      ...context,
      require: (mod: string) => {
        if (!SECURITY_CONFIG.allowedModules.includes(mod)) {
          throw new Error(`Module ${mod} is not allowed`);
        }
        return require(mod);
      }
    };

    SECURITY_CONFIG.blockedKeywords.forEach(keyword => {
      if (code.includes(keyword)) {
        throw new Error(`Blocked keyword detected: ${keyword}`);
      }
    });

    return vm.runInNewContext(code, sandbox, { timeout: 1000 });
  }
}

// Tool initialization
const toolRegistry = new ToolRegistry();
toolRegistry.registerTool(new WebSearchTool());
toolRegistry.registerTool(new FileAnalysisTool());
toolRegistry.registerTool(new CalculatorTool());

// Memory initialization
const memory = new VectorMemory();

// Agent initialization (assuming you have an Agent class)
const agent = new Agent(toolRegistry, memory);

// CLI Interface
const r = repl.start({
  prompt: 'Agent> ',
  async eval(input: string, _: any, callback: any) {
    const userInput = input.trim();

    try {
      // Process through agent
      const response = await agent.executeTask(userInput);

      // Store in memory
      await memory.store(`User: ${userInput}\nAgent: ${response}`);

      callback(null, response);
    } catch (error) {
      callback(error instanceof Error ? error : new Error(String(error)), null);
    }
  }
});

// Security enhancements
r.context.require = (mod: string) => {
  if (!SECURITY_CONFIG.allowedModules.includes(mod)) {
    throw new Error(`Module ${mod} is not allowed in REPL`);
  }
  return require(mod);
};

// Handle exit
r.on('exit', () => {
  console.log('Exiting agent session');
  process.exit();
});
