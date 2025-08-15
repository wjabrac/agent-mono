import path from "path";
import vm from "vm";

export class Security {
  // Path sanitization to prevent traversal outside CWD
  static sanitizePath(userPath: string): string {
    const resolved = path.resolve(process.cwd(), userPath);
    if (!resolved.startsWith(process.cwd())) {
      throw new Error("Path traversal attempt blocked");
    }
    return resolved;
  }

  // Basic input validation with pattern blocking
  static validateInput(input: string): void {
    const blocked = [
      /child_process/i,
      /process\./i,
      /exec\(/i,
      /spawn\(/i,
      /fs\.write/i,
      /eval\(/i,
      /Function\(/i,
      /require\(/i,
      /import\(/i
    ];
    for (const pat of blocked) {
      if (pat.test(input)) {
        throw new Error(`Security violation: blocked pattern (${pat.source})`);
      }
    }
    if (input.length > 10000) {
      throw new Error("Input too large");
    }
  }

  // Minimal safe evaluation helper
  static safeEval(code: string, context: object = {}): any {
    const sandbox = {
      ...context,
      console: undefined,
      process: undefined,
      require: undefined
    };
    Object.freeze(sandbox);
    const script = new vm.Script(code);
    return script.runInNewContext(sandbox, { timeout: 500 });
  }

  // Simple HTML sanitizer
  static sanitizeHTML(input: string): string {
    return input.replace(/[&<>"']/g, (m) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" } as const)[m]!
    );
  }

  // Optional container validation - imports inside function to avoid hard deps
  static async validateContainerSecurity(image: string): Promise<void> {
    try {
      const { execSync } = await import("child_process");
      const Docker = (await import("dockerode")).default as any;

      const dockerClient = new Docker();
      const imageInspect = await dockerClient.getImage(image).inspect();
      if (!imageInspect.Config?.Labels?.["org.opencontainers.image.created"]) {
        throw new Error("Unsigned container image");
      }

      const scan = execSync(`trivy image --light ${image}`, {
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "ignore"]
      });
      const criticalCVEs = ["CVE-2021-44228", "CVE-2021-45046", "CVE-2022-22963", "CVE-2022-22965"];
      if (criticalCVEs.some((c) => scan.includes(c))) {
        throw new Error("Critical vulnerability detected");
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      throw new Error(`Container security check failed: ${msg}`);
    }
  }
}
