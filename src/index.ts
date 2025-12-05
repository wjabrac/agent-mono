import readline from "readline";
import { createDefaultAgent } from "./setupAgent";

const { agent, memory } = createDefaultAgent();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

async function main() {
  console.log('Agent initialized. Type your query or "exit" to quit.');

  while (true) {
    const input = await new Promise<string>((resolve) =>
      rl.question("\nUser: ", resolve)
    );

    if (input.toLowerCase() === "exit") break;

    try {
      process.stdout.write("Agent: ");
      const response = await agent.executeTask(input);

      for (const char of response) {
        process.stdout.write(char);
        await new Promise((resolve) => setTimeout(resolve, 20));
      }
      process.stdout.write("\n");
    } catch (error) {
      console.error(`\nError: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  rl.close();
  console.log("Session ended");
}

memory.initialize().then(() => {
  main().catch(console.error);
});
