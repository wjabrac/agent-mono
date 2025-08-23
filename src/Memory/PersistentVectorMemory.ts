import { VectorMemory } from "./VectorMemory";
import { ChromaClient } from "chromadb";
import * as use from "@tensorflow-models/universal-sentence-encoder";
import * as tf from "@tensorflow/tfjs-node";
import fs from "fs";
import path from "path";

export class PersistentVectorMemory extends VectorMemory {
  private client: ChromaClient;
  private collection: any | null = null;
  private model: use.UniversalSentenceEncoder | null = null;
  private initialized = false;
  private storageDir: string;
  private memoryFile: string;
  private retrievedFile: string;

  constructor() {
    super();
    this.client = new ChromaClient({
      path: process.env.CHROMA_URL || "http://localhost:8000",
    });
    this.storageDir = path.join(process.cwd(), "data");
    this.memoryFile = path.join(this.storageDir, "memory.json");
    this.retrievedFile = path.join(this.storageDir, "retrieved.json");
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;
    await fs.promises.mkdir(this.storageDir, { recursive: true });

    try {
      this.model = await use.load();
      this.collection = await this.client.getOrCreateCollection({
        name: "agent-memory",
      });
    } catch (err) {
      console.warn("ChromaDB unavailable, falling back to file store.", err);
    }

    if (fs.existsSync(this.memoryFile)) {
      const data = JSON.parse(await fs.promises.readFile(this.memoryFile, "utf8"));
      for (const item of data) {
        await super.store(item);
      }
    }

    this.initialized = true;
  }

  async store(text: string): Promise<void> {
    if (!this.initialized) await this.initialize();

    await super.store(text);

    if (this.collection && this.model) {
      try {
        const embedding = await this.model.embed([text]);
        const embeddingArray = await embedding.array();
        await this.collection.add({
          ids: [Date.now().toString()],
          embeddings: embeddingArray[0],
          documents: [text],
        });
      } catch (err) {
        console.warn("Failed to store in ChromaDB", err);
      }
    }

    try {
      const existing = fs.existsSync(this.memoryFile)
        ? JSON.parse(await fs.promises.readFile(this.memoryFile, "utf8"))
        : [];
      existing.push(text);
      await fs.promises.writeFile(
        this.memoryFile,
        JSON.stringify(existing, null, 2)
      );
    } catch (err) {
      console.warn("Failed to persist memory to disk", err);
    }
  }

  async retrieveRelevant(query: string): Promise<string[]> {
    if (!this.initialized) await this.initialize();

    let results: string[] = [];
    if (this.collection && this.model) {
      try {
        const queryEmbedding = await this.model.embed([query]);
        const queryEmbeddingArray = await queryEmbedding.array();
        const response = await this.collection.query({
          queryEmbeddings: queryEmbeddingArray[0],
          nResults: 5,
        });
        results = response.documents[0] || [];
      } catch (err) {
        console.warn("Failed to query ChromaDB, using fallback", err);
      }
    }

    if (results.length === 0) {
      results = await super.retrieveRelevant(query);
    }

    try {
      const existing = fs.existsSync(this.retrievedFile)
        ? JSON.parse(await fs.promises.readFile(this.retrievedFile, "utf8"))
        : {};
      existing[query] = results;
      await fs.promises.writeFile(
        this.retrievedFile,
        JSON.stringify(existing, null, 2)
      );
    } catch (err) {
      console.warn("Failed to persist retrieved context", err);
    }

    return results;
  }
}
