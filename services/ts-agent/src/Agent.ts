import { ToolRegistry } from './Tools/ToolRegistry';
import { VectorMemory } from './Memory/VectorMemory';

export class Agent {
  constructor(private toolRegistry: ToolRegistry, private memory: VectorMemory) {}

  async executeTask(input: string): Promise<string> {
    return `Agent received: ${input}`;
  }
}
