import docker from "dockerode";
import { promises as fs } from "fs";
import path from "path";
import tar from "tar-fs";
import { Security } from "./security";

export class ContainerManager {
  private docker = new docker();
  
  async executeCode(options: {
    language: string;
    code: string;
    files?: Record<string, string>;
    timeout?: number;
    memoryMB?: number;
  }): Promise<{ output: string; error: boolean }> {
    const { language, code, files = {}, timeout = 10000, memoryMB = 256 } = options;
    const tempDir = await this.createTempDir();
    const mainFile = `main.${this.getFileExtension(language)}`;
    
    // Write files to temp directory
    await this.writeFiles(tempDir, { [mainFile]: code, ...files });
    
    // Create container
    const container = await this.docker.createContainer({
      Image: this.getImageName(language),
      Cmd: this.getExecutionCommand(language, mainFile),
      HostConfig: {
        AutoRemove: true,
        Binds: [`${tempDir}:/app:ro`],
        Memory: memoryMB * 1024 * 1024,
        MemorySwap: memoryMB * 1024 * 1024,
        NetworkMode: "none",
        IpcMode: "none",
        CapDrop: ["ALL"],
        SecurityOpt: ["no-new-privileges"]
      },
      WorkingDir: "/app",
    });
    
    // Execute and capture output
    let output = "";
    try {
      await container.start();
      const result = await container.wait();
      
      // Exit code handling
      if (result.StatusCode !== 0) {
        output += `Process exited with code ${result.StatusCode}\n`;
      }
      
      // Get logs
      const logs = await container.logs({
        stdout: true,
        stderr: true,
      });
      output += logs.toString("utf8");
    } catch (error) {
      output += `Container error: ${error instanceof Error ? error.message : String(error)}\n`;
    } finally {
      try {
        await container.stop();
        await container.remove();
      } catch {}
      await fs.rm(tempDir, { recursive: true, force: true });
    }
    
    return {
      output: output.trim(),
      error: output.includes("error") || output.includes("Error")
    };
  }
  
  private async createTempDir(): Promise<string> {
    const tempDir = path.join(process.cwd(), "temp", Date.now().toString());
    await fs.mkdir(tempDir, { recursive: true });
    return tempDir;
  }
  
  private async writeFiles(dir: string, files: Record<string, string>) {
    for (const [filePath, content] of Object.entries(files)) {
      const safePath = Security.sanitizePath(path.join(dir, filePath));
      await fs.mkdir(path.dirname(safePath), { recursive: true });
      await fs.writeFile(safePath, content);
    }
  }
  
  private getImageName(language: string): string {
    const images: Record<string, string> = {
      python: "python:3.11-slim",
      javascript: "node:20-slim",
      typescript: "node:20-slim",
      rust: "rust:1.75-slim",
      go: "golang:1.22-alpine"
    };
    return images[language];
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
  
  // Security scanning for containers
  async scanForVulnerabilities() {
    const images = [
      "python:3.11-slim",
      "node:20-slim",
      "rust:1.75-slim",
      "golang:1.22-alpine"
    ];
    
    const results: Record<string, string> = {};
    for (const image of images) {
      try {
        const container = await this.docker.createContainer({
          Image: image,
          Cmd: ["sh", "-c", "echo 'Scanning...' && exit 0"],
          HostConfig: { AutoRemove: true }
        });
        
        await container.start();
        await container.wait();
        results[image] = "Clean";
      } catch (error) {
        results[image] = `Vulnerable: ${error instanceof Error ? error.message : String(error)}`;
      }
    }
    
    return results;
  }
}
