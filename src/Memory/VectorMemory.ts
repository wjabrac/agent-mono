export class VectorMemory {
  private items: string[] = [];

  async initialize(): Promise<void> {
    // No-op for in-memory store
  }

  async retrieveRelevant(query: string): Promise<string[]> {
    return this.items
      .filter((s) => s.toLowerCase().includes(query.toLowerCase()))
      .slice(-5);
  }

  async store(text: string): Promise<void> {
    this.items.push(text);
  }
}
