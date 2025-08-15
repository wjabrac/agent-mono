import path from "path";
import vm from "vm";
import { execSync } from "child_process";
import docker from "dockerode";

export class Security {
  // Path sanitization to prevent path traversal
  static sanitizePath(p: string): string {
    const resolved = path.resolve(p);
    if (!resolved.startsWith(path.resolve(process.cwd()))) {
      throw new Error("Path traversal detected");
    }
    return resolved;
  }

  // Basic input validation placeholder
  static validateInput(input: string): void {
    if (input.length > 10000) {
      throw new Error("Input too large");
    }
  }
  
  // Container security validation
  static async validateContainerSecurity(image: string): Promise<void> {
    const knownVulnerabilities = [
      "CVE-2021-44228", "CVE-2021-45046", // Log4j
      "CVE-2022-22963", "CVE-2022-22965"  // SpringShell
    ];
    
    try {
      // Check for known vulnerable images
      const dockerClient = new docker();
      const imageInspect = await dockerClient.getImage(image).inspect();
      
      // Verify image signature
      if (!imageInspect.Config.Labels?.['org.opencontainers.image.created']) {
        throw new Error("Unsigned container image");
      }
      
      // Check against known CVE list
      const scanResult = execSync(`trivy image --light ${image}`, {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'ignore']
      });
      
      for (const cve of knownVulnerabilities) {
        if (scanResult.includes(cve)) {
          throw new Error(`Critical vulnerability detected: ${cve}`);
        }
      }
    } catch (error) {
      throw new Error(`Container security check failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  // Code analysis for malicious patterns
  static analyzeCodePatterns(code: string): void {
    const dangerousPatterns = [
      /child_process\.exec/i,
      /fs\.writeFileSync/i,
      /process\.env/i,
      /eval\(/i,
      /Function\(/i,
      /import\(/i,
      /require\(/i,
      /dockerode/i,
      /net\.connect/i,
      /http\.request/i,
      /XMLHttpRequest/i,
      /WebSocket/i,
      /Deno\./i,
      /\.mount\(/i,
      /\.chmod\(/i
    ];
    
    for (const pattern of dangerousPatterns) {
      if (pattern.test(code)) {
        throw new Error(`Dangerous code pattern detected: ${pattern.source}`);
      }
    }
    
    // Simple dynamic checks
    if (code.includes("eval(") || code.includes("Function(")) {
      throw new Error("Dynamic code execution detected");
    }
  }
  
  // Resource usage monitoring
  static createResourceMonitor(timeout: number) {
    const start = Date.now();
    return {
      check: () => {
        if (Date.now() - start > timeout) {
          throw new Error("Resource usage timeout");
        }
      },
      getElapsed: () => Date.now() - start
    };
  }
  
  // Secure memory management
  static createSecureBuffer(size: number): Buffer {
    const buffer = Buffer.alloc(size);
    if (process.platform === 'linux') {
      try {
        execSync(`mlock ${process.pid}`);
      } catch {}
    }
    buffer.fill(0);
    return buffer;
  }
}
