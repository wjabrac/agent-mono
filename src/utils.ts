export function parseNumberEnv(envVar: string | undefined, defaultValue: number): number {
  if (envVar === undefined || envVar === "") return defaultValue;

  const parsed = Number.parseFloat(envVar);
  return Number.isNaN(parsed) ? defaultValue : parsed;
}

export function applyTemplate(template: string, values: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? values[key] : ""
  );
}
