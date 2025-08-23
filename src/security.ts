import path from "path";
import fs from "fs";
import vm from "vm";

export class Security {
  static sanitizePath(userPath: string): string {
    const resolved = path.resolve(process.cwd(), userPath);
    const real = fs.existsSync(resolved) ? fs.realpathSync(resolved) : resolved;
    const relative = path.relative(process.cwd(), real);
    if (relative.startsWith("..") || path.isAbsolute(relative)) {
      throw new Error("Path traversal attempt blocked");
    }
    return real;
  }

  private static normalize(input: string): string {
    return input.normalize("NFKC").replace(/[\u200B-\u200D\uFEFF]/g, "");
  }

  static validateInput(input: string): string {
    const normalized = Security.normalize(input);
    const allowedPattern =
      /^[\p{L}\p{N}\s.,;:_\-()"'\+\*\/%={}\[\]<>:,]*$/u;
    const blockedPatterns = [
      /child_process/iu,
      /process\./iu,
      /exec\s*\(/iu,
      /spawn\s*\(/iu,
      /fs\.(write|read|append|unlink)/iu,
      /eval\s*\(/iu,
      /function\s*\(/iu,
      /require\s*\(/iu,
      /import\s*\(/iu,
      /constructor/iu,
      /__proto__/iu,
      /prototype/iu,
      /while\s*\(\s*true\s*\)/iu,
      /for\s*\(\s*;\s*;\s*\)/iu,
      /globalThis/iu,
      /setTimeout\s*\(/iu,
      /setInterval\s*\(/iu,
    ];

    if (!allowedPattern.test(normalized)) {
      throw new Error("Security violation: Disallowed characters detected");
    }

    for (const pattern of blockedPatterns) {
      if (pattern.test(normalized)) {
        throw new Error(
          `Security violation: Blocked pattern detected (${pattern.source})`
        );
      }
    }

    return normalized;
  }

  static analyzeToolInput(code: string): vm.Script {
    try {
      return new vm.Script(code);
    } catch {
      throw new Error("Security violation: Unparsable input");
    }
  }

  static safeEval(code: string, context: object = {}): any {
    const normalized = Security.validateInput(code);
    const script = Security.analyzeToolInput(normalized);
    const sandbox = {
      ...context,
      console: undefined,
      process: undefined,
      require: undefined,
    };

    Object.freeze(sandbox);
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
