import { BaseTool } from "./BaseTool";
import { z } from "zod";
import { readFile } from "fs/promises";
import * as pdf from "pdf-parse";
import path from "path";

export class FileAnalysisTool extends BaseTool {
  name = "FileAnalysis";
  description = "Read and analyze text/PDF files";
  schema = z.object({
    filePath: z.string().describe("Absolute file path")
  });

  protected async _execute(args: { filePath: string }): Promise<string> {
    const safePath = this.sanitizePath(args.filePath);
    const buffer = await readFile(safePath);

    if (safePath.endsWith('.pdf')) {
      const data = await pdf(buffer);
      return data.text.slice(0, 2000);
    }

    return buffer.toString('utf8').slice(0, 2000);
  }

  private sanitizePath(userPath: string): string {
    const resolved = path.resolve(process.cwd(), userPath);
    if (!resolved.startsWith(process.cwd())) {
      throw new Error("Path traversal attempt blocked");
    }
    return resolved;
  }
}
