import { BaseTool } from "./BaseTool";
import { z } from "zod";
import fs from "fs/promises";
import path from "path";
import pdfParse from "pdf-parse";
import { Security } from "../security";

export class FileAnalysisTool extends BaseTool {
  name = "FileAnalysis";
  description = "Read text/PDF files";
  schema = z.object({
    filePath: z.string().describe("Path to the file to read"),
  });

  protected async _execute(args: { filePath: string }): Promise<string> {
    const safePath = Security.sanitizePath(args.filePath);
    const ext = path.extname(safePath).toLowerCase();
    const data = await fs.readFile(safePath);
    if (ext === ".pdf") {
      const pdfData = await pdfParse(data);
      return pdfData.text.slice(0, 2000);
    }
    return data.toString("utf-8");
  }
}
