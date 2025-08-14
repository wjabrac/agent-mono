import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'doc',
      label: 'Welcome to AutoAgent',
      id: 'Get-Started/welcome-to-autoagent',
    }, 
    {
      type: "category",
      label: "Get started",
      items: [
        "Get-Started/get-started-installation",
        "Get-Started/get-started-quickstart",
      ],
    },
    {
      type: "category",
      label: "Starter Projects",
      items: [
        "Starter-Projects/starter-projects-auto-deep-research",
        "Starter-Projects/starter-projects-nl-to-agent",
        "Starter-Projects/starter-projects-agentic-rag",
      ],
    },
    {
      type: "category",
      label: "User Guideline",
      items: [
        "User-Guideline/user-guide-daily-tasks",
        "User-Guideline/user-guide-how-to-create-agent",
      ],
    },
    {
      type: "category",
      label: "Developer Guideline",
      items: [
        "Dev-Guideline/dev-guide-create-tools",
        "Dev-Guideline/dev-guide-create-agent",
        "Dev-Guideline/dev-guide-edit-mem",
        "Dev-Guideline/dev-guide-build-your-project",
        "Dev-Guideline/dev-guide-architecture",
        "Dev-Guideline/dev-guide-temporal-async",
        "Dev-Guideline/dev-guide-integration-n8n-crewai",
        "Dev-Guideline/dev-guide-project-policy",
      ],
    },
  ],
};

export default sidebars;
