import { BaseTool } from "./BaseTool";
import { z } from "zod";
import { Security } from "../security";
import { promises as fs } from "fs";
import path from "path";
import { v4 as uuidv4 } from "uuid";
import { execa } from "execa";
import docker from "dockerode";
import tar from "tar-fs";

const dockerClient = new docker();

export class CodeInterpreterTool extends BaseTool {
  name = "CodeInterpreter";
  description = "Write, execute, and debug code in multiple programming languages";
  schema = z.object({
    language: z.enum(["python", "javascript", "typescript", "rust", "go"]),
    code: z.string().describe("Code to execute"),
    files: z.record(z.string()).optional().describe("Additional files to include")
  });

  private async createTempDir(): Promise<string> {
    const tempDir = path.join(process.cwd(), "temp", uuidv4());
    await fs.mkdir(tempDir, { recursive: true });
    return tempDir;
  }

  private async writeFiles(dir: string, files: Record<string, string> = {}) {
    for (const [filePath, content] of Object.entries(files)) {
      const safePath = Security.sanitizePath(path.join(dir, filePath));
      await fs.mkdir(path.dirname(safePath), { recursive: true });
      await fs.writeFile(safePath, content);
    }
  }

  private getImageName(language: string): string {
    const images = {
      python: "python:3.11-slim",
      javascript: "node:20-slim",
      typescript: "node:20-slim",
      rust: "rust:1.75-slim",
      go: "golang:1.22-alpine"
    } as const;
    return images[language as keyof typeof images];
  }

  private getExecutionCommand(language: string, mainFile: string): string[] {
    switch (language) {
      case "python": return ["python", mainFile];
      case "javascript": return ["node", mainFile];
      case "typescript": return ["sh", "-c", `tsc ${mainFile} && node ${mainFile.replace('.ts', '.js')}`];
      case "rust": return ["sh", "-c", `rustc ${mainFile} && ./main`];
      case "go": return ["go", "run", mainFile];
      default: throw new Error(`Unsupported language: ${language}`);
    }
  }

  protected async _execute(args: {
    language: string,
    code: string,
    files?: Record<string, string>
  }): Promise<string> {
    const tempDir = await this.createTempDir();
    const mainFile = `main.${this.getFileExtension(args.language)}`;
    const files = { [mainFile]: args.code, ...(args.files || {}) };

    await this.writeFiles(tempDir, files);

    // Create Docker container
    const imageName = this.getImageName(args.language);
    const container = await dockerClient.createContainer({
      Image: imageName,
      Cmd: this.getExecutionCommand(args.language, mainFile),
      HostConfig: {
        AutoRemove: true,
        Binds: [`${tempDir}:/app:ro`],
        Memory: 256 * 1024 * 1024, // 256MB memory limit
        NetworkMode: "none" // Disable network access
      },
      WorkingDir: "/app",
      Tty: false
    });

    // Execute code in container
    const output: string[] = [];
    try {
      await container.start();
      const stream = await container.logs({
        follow: true,
        stdout: true,
        stderr: true
      });

      stream.on("data", (chunk) => {
        output.push(chunk.toString());
      });

      // Wait with timeout (10 seconds)
      await Promise.race([
        container.wait(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Execution timed out")), 10000)
        )
      ]);
    } catch (error) {
      output.push(`Execution error: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      try {
        await container.stop();
        await container.remove();
      } catch {}
      await fs.rm(tempDir, { recursive: true, force: true });
    }

    return output.join("\n").trim();
  }

  private getFileExtension(language: string): string {
    switch (language) {
      case "python": return "py";
      case "javascript": return "js";
      case "typescript": return "ts";
      case "rust": return "rs";
      case "go": return "go";
      default: return "txt";
    }
  }
}
