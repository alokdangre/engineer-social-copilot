# AI Social Media Manager for Tech Professionals

This repository contains the product and workflow plan for an AI agent that helps a developer become known for credible technical work, build relationships with founders and maintainers, find career opportunities, and grow toward a DevRel role.

The first version connects three external apps:

- **GitHub** supplies evidence of projects, contributions, technologies, and technical progress.
- **X** supports fast technical conversation, trend discovery, public interaction, and relationship building.
- **LinkedIn** supports professional positioning, founder and recruiter visibility, career context, and longer professional posts.

The agent analyzes, researches, recommends, drafts, and learns. The user reviews every recommendation and manually publishes, comments, replies, or reposts during the first version.

## Documentation map

- [Coordinating workflow](docs/00-coordinating-workflow.md): complete system graph, shared rules, cadence, and workflow contracts.
- [Workflow A — Establish the user baseline](docs/workflows/A-user-baseline.md)
- [Workflow B — Capture daily life and learning](docs/workflows/B-daily-capture.md)
- [Workflow C — Research the ecosystem](docs/workflows/C-ecosystem-research.md)
- [Workflow D — Recommend useful actions](docs/workflows/D-recommendations.md)
- [Workflow E — Review and manual execution](docs/workflows/E-review-and-execution.md)
- [Workflow F — Analyze outcomes](docs/workflows/F-outcome-analysis.md)
- [Structured memory](docs/memory-system.md): how facts, evidence, preferences, experiences, and relationships remain separate but connected.
- [Strategy learning](docs/strategy-learning.md): how the agent turns research and results into controlled strategy updates.
- [Platform boundaries](docs/platform-boundaries.md): data sources, permissions, anti-bot constraints, privacy, and first-version integration boundaries.
- [Product decisions](docs/product-decisions.md): why the current three apps were chosen and why Notion, Canva, Instagram, blogging, and SEO/AEO integrations are deferred.
- [Recommended technical stack](docs/technical-stack.md): LangGraph architecture, backend and frontend stack, persistence, connectors, model roles, observability, evaluation, and deployment direction.

## Core product rule

The agent must help the user become more visible without fabricating expertise, experiences, opinions, relationships, or results. Every personal claim should trace to evidence or explicit user confirmation, and every external action remains under the user's control.
