import { z } from "zod";

export abstract class BaseTool {
  abstract name: string;
  abstract description: string;
  // schema is validated when safeExecute is called
  abstract schema: z.ZodTypeAny;

  // Backward compatible entrypoint
  async execute(args: any): Promise<string> {
    return this.safeExecute(args);
  }

  async safeExecute(args: unknown): Promise<string> {
    const parsed = this.schema.parse(args);
    try {
      return await this._execute(parsed);
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      return `Error executing ${this.name}: ${msg}`;
    }
  }

  protected abstract _execute(args: any): Promise<string>;
}
