import path from "path";
import vm from "vm";

export class Security {
  static sanitizePath(userPath: string): string {
    const resolved = path.resolve(process.cwd(), userPath);
    if (!resolved.startsWith(process.cwd())) {
      throw new Error("Path traversal attempt blocked");
    }
    return resolved;
  }

  static validateInput(input: string): void {
    const blockedPatterns = [
      /child_process/i,
      /process\./i,
      /exec\(/i,
      /spawn\(/i,
      /fs\.write/i,
      /eval\(/i,
      /Function\(/i,
      /require\(/i,
      /import\(/i,
    ];

    for (const pattern of blockedPatterns) {
      if (pattern.test(input)) {
        throw new Error(
          `Security violation: Blocked pattern detected (${pattern.source})`
        );
      }
    }
  }

  static safeEval(code: string, context: object = {}): any {
    const sandbox = {
      ...context,
      console: undefined,
      process: undefined,
      require: undefined,
    };

    Object.freeze(sandbox);
    const script = new vm.Script(code);
    return script.runInNewContext(sandbox, { timeout: 500 });
  }

  static sanitizeHTML(input: string): string {
    return input.replace(/[&<>"']/g, (m) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[m]!)
    );
  }
}
