import { BaseTool } from "./BaseTool";
import { z } from "zod";

export class DirectResponseTool extends BaseTool {
  name = "DirectResponse";
  description = "Respond directly to user without using tools";
  schema = z.object({
    input: z.string().describe("The user's input"),
  });

  protected async _execute(args: { input: string }): Promise<string> {
    return `The agent will respond directly to: "${args.input}"`;
  }
}
