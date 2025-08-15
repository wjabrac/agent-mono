import { ChromaClient } from 'chromadb';
import * as use from '@tensorflow-models/universal-sentence-encoder';
import * as tf from '@tensorflow/tfjs-node';

export class VectorMemory {
  private client: any;
  private collection: any;
  private model: any = null;
  private isInitialized = false;

  constructor() {
    this.client = new ChromaClient();
  }

  async initialize() {
    if (this.isInitialized) return;

    // Load TensorFlow model
    this.model = await use.load();

    // Setup ChromaDB collection
    this.collection = await this.client.createCollection({
      name: 'agent-memory'
    });

    this.isInitialized = true;
  }

  async store(observation: string) {
    if (!this.isInitialized) await this.initialize();

    const embedding = await this.model!.embed([observation]);
    const embeddingArray = await embedding.array();

    await this.collection.add({
      ids: [Date.now().toString()],
      embeddings: embeddingArray[0],
      documents: [observation]
    });
  }

  async retrieveRelevant(query: string, topK = 5): Promise<string[]> {
    if (!this.isInitialized) await this.initialize();

    const queryEmbedding = await this.model!.embed([query]);
    const queryEmbeddingArray = await queryEmbedding.array();

    const results = await this.collection.query({
      queryEmbeddings: queryEmbeddingArray[0],
      nResults: topK
    });

    return results.documents[0] || [];
  }
}
