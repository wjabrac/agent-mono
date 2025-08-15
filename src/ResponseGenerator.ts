import { Ollama } from "@langchain/community/llms/ollama";
import { PromptTemplate } from "@langchain/core/prompts";
import { Security } from "./security";

export class ResponseGenerator {
  private model: Ollama;
  private template: PromptTemplate;

  constructor() {
    this.model = new Ollama({
      baseUrl: "http://localhost:11434",
      model: "llama2",
      temperature: 0.7,
    });

    this.template = PromptTemplate.fromTemplate(`
You are an AI assistant. Generate a helpful response based on:
- User request: {input}
- Context: {context}
- Tool results: {results}

Guidelines:
1. Be concise and direct
2. Cite sources when available
3. If multiple results exist, summarize key points
4. Admit when you don't know
5. NEVER invent information

Response:
    `);
  }

  async generateResponse(
    input: string,
    results: string,
    context: string[]
  ): Promise<string> {
    Security.validateInput(input);

    const contextStr = context.join("\n").slice(0, 1500);
    const prompt = await this.template.format({
      input,
      context: contextStr || "No relevant context",
      results: results || "No tool results",
    });

    const response = await this.model.invoke(prompt);
    return this.cleanResponse(response);
  }

  private cleanResponse(response: string): string {
    return response
      .replace(/```[\s\S]*?```/g, "")
      .replace(/\n+/g, "\n")
      .trim();
  }
}
