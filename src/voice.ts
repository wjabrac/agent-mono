import fs from "fs/promises";
import os from "os";
import path from "path";
import readline from "readline";
import { exec as execCallback } from "child_process";
import { promisify } from "util";
import { PlanAssessment } from "./OperationMode";
import { createDefaultAgent } from "./setupAgent";
import { applyTemplate, escapeShellArg, parseNumberEnv } from "./utils";

const exec = promisify(execCallback);

const recordSeconds = parseNumberEnv(process.env.VOICE_RECORD_SECONDS, 6);
const recordCommandTemplate =
  process.env.VOICE_RECORD_COMMAND ??
  `ffmpeg -hide_banner -loglevel error -f alsa -i default -t ${recordSeconds} -ac 1 -ar 16000 {file}`;
const sttCommandTemplate = process.env.VOICE_STT_COMMAND;
const ttsCommandTemplate = process.env.VOICE_TTS_COMMAND;
const commandTimeoutMs = parseNumberEnv(process.env.VOICE_COMMAND_TIMEOUT_MS, 20000);

async function requestApproval(assessment: PlanAssessment): Promise<boolean> {
  console.log(`\n${assessment.mode.toUpperCase()} mode requires approval.`);
  console.log(`Reasons: ${assessment.reasons.join("; ")}`);
  console.log(`Planned steps: ${JSON.stringify(assessment.plan.steps, null, 2)}`);

  const answer = await ask("Approve plan? (y/N): ");
  return answer.trim().toLowerCase().startsWith("y");
}

const { agent, memory } = createDefaultAgent(requestApproval);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

async function runCommand(command: string, description: string) {
  try {
    return await exec(command, { timeout: commandTimeoutMs });
  } catch (error) {
    const execError = error as Error & { stdout?: string; stderr?: string };
    const output = execError.stderr || execError.stdout || "";
    const message = [description, output || execError.message].filter(Boolean).join(": ");
    throw new Error(message);
  }
}

async function recordAudio(): Promise<string> {
  const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "agent-voice-"));
  const filePath = path.join(tmpDir, "input.wav");
  const command = applyTemplate(recordCommandTemplate, { file: filePath });

  await runCommand(command, "Recording failed");
  return filePath;
}

async function transcribeAudio(filePath: string): Promise<string> {
  if (!sttCommandTemplate) {
    throw new Error(
      "Set VOICE_STT_COMMAND to a command that prints the transcription (include {file} placeholder)."
    );
  }

  if (!sttCommandTemplate.includes("{file}")) {
    throw new Error("VOICE_STT_COMMAND must include {file} to point at the WAV recording");
  }

  const command = applyTemplate(sttCommandTemplate, { file: filePath });
  const { stdout } = await runCommand(command, "Transcription failed");
  return stdout.trim();
}

async function speak(text: string): Promise<void> {
  if (!ttsCommandTemplate) return;

  const command = applyTemplate(ttsCommandTemplate, { text: escapeShellArg(text) });
  try {
    await runCommand(command, "Speech playback failed");
  } catch (error) {
    console.warn((error as Error).message);
  }
}

async function captureUtterance(): Promise<string> {
  const filePath = await recordAudio();
  try {
    return await transcribeAudio(filePath);
  } finally {
    await fs.rm(path.dirname(filePath), { recursive: true, force: true });
  }
}

async function ask(prompt: string): Promise<string> {
  return new Promise((resolve) => rl.question(prompt, resolve));
}

async function main() {
  console.log(
    'Voice assistant ready. Press Enter to speak, or type text. Type "exit" to quit.'
  );

  if (!sttCommandTemplate) {
    console.warn("VOICE_STT_COMMAND is not set; speech capture will fail until configured.");
  }

  console.log(
    `Config: record ${recordSeconds}s clips, command timeout ${commandTimeoutMs}ms${
      ttsCommandTemplate ? "" : "; TTS disabled"
    }.`
  );

  while (true) {
    const userInput = await ask("\nYou (Enter to talk): ");

    if (userInput.toLowerCase() === "exit") break;

    let message = userInput.trim();

    if (!message) {
      try {
        message = await captureUtterance();
      } catch (error) {
        console.error(
          `Capture failed: ${error instanceof Error ? error.message : String(error)}. ` +
            "Type instead to continue."
        );
        continue;
      }
    }

    if (!message) {
      console.log("No speech detected; try again.");
      continue;
    }

    try {
      console.log("Agent thinking...");
      const response = await agent.executeTask(message);
      console.log(`Agent: ${response}`);

      await speak(response);
    } catch (error) {
      console.error(
        `Agent error: ${error instanceof Error ? error.message : String(error)}. Continuing...`
      );
    }
  }

  rl.close();
  console.log("Session ended");
}

memory.initialize().then(() => {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
});
