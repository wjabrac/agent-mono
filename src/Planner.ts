import { Ollama } from "@langchain/community/llms/ollama";
import { PromptTemplate } from "@langchain/core/prompts";
import { z } from "zod";
import { Security } from "./security";

const planSchema = z.object({
  steps: z.array(
    z.object({
      tool: z.string(),
      arguments: z.record(z.any()),
    })
  ),
});

export class Planner {
  private model: Ollama;
  private template: PromptTemplate;

  constructor() {
    this.model = new Ollama({
      baseUrl: "http://localhost:11434",
      model: "llama2",
      temperature: 0.2,
    });

    this.template = PromptTemplate.fromTemplate(`
You are an AI planner. Given the user request and relevant context, generate a plan of actions.

Available tools:
{tools}

Context:
{context}

User request: {input}

Output a JSON array of steps with "tool" (tool name) and "arguments" (key-value pairs). Example:
[
  {{"tool": "WebSearch", "arguments": {{"query": "current weather"}}}},
  {{"tool": "Calculator", "arguments": {{"expression": "32*1.8+32"}}}}
]

Plan ONLY for the current request. Use minimal steps.
    `);
  }

  async generatePlan(
    input: string,
    context: string[]
  ): Promise<{ steps: any[] }> {
    try {
      Security.validateInput(input);

      const tools = this.toolDescriptions();
      const contextStr = context.join("\n").slice(0, 2000);

      const prompt = await this.template.format({
        tools,
        context: contextStr || "No relevant context",
        input,
      });

      const response = await this.model.invoke(prompt);

      const jsonMatch = response.match(/```json\n([\s\S]*?)\n```/);
      const jsonStr = jsonMatch ? jsonMatch[1] : response;

      const plan = JSON.parse(jsonStr);
      return planSchema.parse(plan);
    } catch (error) {
      console.error("Planning failed, using fallback");
      return {
        steps: [{ tool: "DirectResponse", arguments: { input } }],
      };
    }
  }

  private toolDescriptions(): string {
    return [
      "- WebSearch(query): Search the web for current information",
      "- FileAnalysis(filePath): Read text/PDF files",
      "- Calculator(expression): Solve math problems",
      "- DirectResponse(input): Respond directly to user",
    ].join("\n");
  }
}
