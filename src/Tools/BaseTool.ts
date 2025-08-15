import { z } from "zod";

export abstract class BaseTool {
  abstract name: string;
  abstract description: string;
  abstract schema: z.ZodTypeAny;

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
