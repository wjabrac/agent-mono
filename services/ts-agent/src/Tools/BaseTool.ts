import { z } from "zod";

export abstract class BaseTool {
  abstract name: string;
  abstract description: string;
  abstract schema: any;

  async safeExecute(args: unknown): Promise<string> {
    try {
      const parsedArgs = this.schema.parse(args);
      return await this._execute(parsedArgs);
    } catch (error) {
      return `Tool error: ${error instanceof Error ? error.message : String(error)}`;
    }
  }

  protected abstract _execute(args: any): Promise<string>;
}
