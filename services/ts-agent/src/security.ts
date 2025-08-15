import path from 'path';
import vm from 'vm';

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
      /child_process/,
      /fs\.write/,
      /process\.exit/,
      /eval\(/,
      /Function\(/
    ];

    for (const pattern of blockedPatterns) {
      if (pattern.test(input)) {
        throw new Error("Blocked operation detected");
      }
    }
  }

  static safeEval(code: string, context: object = {}): any {
    const sandbox = { ...context };
    const script = new vm.Script(code);
    return script.runInNewContext(sandbox, { timeout: 500 });
  }
}
