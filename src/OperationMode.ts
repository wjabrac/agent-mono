import { Security } from "./security";

type PlanStep = { tool: string; arguments: Record<string, unknown> };
type Plan = { steps: PlanStep[] };

const defaultRiskyKeywords = [
  "delete",
  "remove",
  "destroy",
  "drop",
  "truncate",
  "wipe",
  "erase",
  "overwrite",
];

const approvalToolsEnv = (process.env.AGENT_APPROVAL_TOOLS ?? "").toLowerCase();
const approvalTools = new Set(
  approvalToolsEnv
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
);

const approvalKeywordsEnv = (process.env.AGENT_APPROVAL_KEYWORDS ?? "").toLowerCase();
const approvalKeywords = new Set(
  approvalKeywordsEnv
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
);

const operationMode = (process.env.AGENT_OPERATION_MODE ?? "guided").toLowerCase();
const explorationRequiresApproval =
  (process.env.AGENT_EXPLORATION_AUTO_APPROVE ?? "false").toLowerCase() !== "true";

export type PlanAssessment = {
  mode: "guided" | "exploratory";
  requiresApproval: boolean;
  reasons: string[];
  plan: Plan;
};

function detectRiskySignals(content: string): string[] {
  const normalized = content.toLowerCase();
  const risks = new Set<string>();

  const addIfPresent = (keyword: string) => {
    if (normalized.includes(keyword)) {
      risks.add(keyword);
    }
  };

  defaultRiskyKeywords.forEach(addIfPresent);
  approvalKeywords.forEach(addIfPresent);

  return Array.from(risks);
}

export function assessPlan(userInput: string, plan: Plan): PlanAssessment {
  const safeInput = Security.validateInput(userInput);
  const serializedPlan = JSON.stringify(plan.steps).toLowerCase();

  const mode = operationMode === "exploratory" ? "exploratory" : "guided";
  const reasons: string[] = [];

  if (mode === "exploratory" && explorationRequiresApproval) {
    reasons.push("Exploratory mode requires approval before executing a new plan.");
  }

  const riskSignals = detectRiskySignals(`${safeInput}\n${serializedPlan}`);
  if (riskSignals.length) {
    reasons.push(`Risky intent detected (${riskSignals.join(", ")}) requiring approval.`);
  }

  const riskyTool = plan.steps.find((step) => approvalTools.has(step.tool.toLowerCase()));
  if (riskyTool) {
    reasons.push(`Tool ${riskyTool.tool} is gated for approval.`);
  }

  return { mode, requiresApproval: reasons.length > 0, reasons, plan };
}
