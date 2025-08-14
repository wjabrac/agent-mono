import { BaseTool } from "./BaseTool";
import { z } from "zod";
import { evaluate } from "mathjs";

export class CalculatorTool extends BaseTool {
  name = "Calculator";
  description = "Perform mathematical calculations";
  schema = z.object({
    expression: z.string().describe("Math expression")
  });

  protected async _execute(args: { expression: string }): Promise<string> {
    return evaluate(args.expression).toString();
  }
}
