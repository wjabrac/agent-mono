import { BaseTool } from "./BaseTool";
import { z } from "zod";
import { evaluate } from "mathjs";
import { Security } from "../security";

export class CalculatorTool extends BaseTool {
  name = "Calculator";
  description = "Solve math problems";
  schema = z.object({
    expression: z.string().describe("Math expression to evaluate"),
  });

  protected async _execute(args: { expression: string }): Promise<string> {
    Security.validateInput(args.expression);
    try {
      const result = evaluate(args.expression);
      return String(result);
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      return `Calculation error: ${msg}`;
    }
  }
}
