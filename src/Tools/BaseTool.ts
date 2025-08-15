export abstract class BaseTool {
  abstract name: string;
  abstract description: string;
  abstract schema: unknown;
  protected abstract _execute(args: any): Promise<string>;

  async execute(args: any): Promise<string> {
    return this._execute(args);
  }
}
