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

## Authentication and connected accounts

Users create an account or sign in to the web application. GitHub, X, and LinkedIn are then
connected through each provider's official OAuth login page; users never enter an OAuth client
secret or personal access token in the UI. Connector tokens are encrypted and stored against the
authenticated application user.

```env
APP_SECRET_KEY=<stable-random-production-secret>
FRONTEND_APP_URL=https://your-frontend.example
OAUTH_CALLBACK_BASE_URL=https://your-backend.example/api/v1/connectors
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
X_CLIENT_ID=
X_CLIENT_SECRET=
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
```

Register these exact callback URLs in the corresponding provider applications:

```text
https://your-backend.example/api/v1/connectors/github/callback
https://your-backend.example/api/v1/connectors/x/callback
https://your-backend.example/api/v1/connectors/linkedin/callback
```

Configure the frontend deployment with the server-only backend origin:

```env
BACKEND_URL=https://your-backend.example
```

The frontend proxies API requests through its own origin so the application session stays in a
secure HTTP-only cookie. Keep `APP_SECRET_KEY` stable across deployments because it signs user
sessions and encrypts stored connector credentials.

## Per-user LLM API keys

After signing in, each user must open **Settings**, choose Google Gemini or OpenAI, and save
their own API key. The key is encrypted at rest with `APP_SECRET_KEY`, is scoped to that user,
and is never returned by the API; the UI only receives the last four characters. If a user has
not configured a key, AI workflows use their deterministic fallback rather than a shared
production credential.

Changing `APP_SECRET_KEY` after users have saved connector or LLM credentials makes the stored
encrypted values unreadable. Keep it stable, backed up, and available only to the backend.

## Render with Neon Postgres

Do not copy the local `.env` file wholesale into Render: its database URLs intentionally point
to `localhost`, which means the Render container itself. In the backend service's Render
Environment settings, set `DATABASE_URL` to Neon's complete externally reachable connection
string. A `postgresql://` Neon URL is accepted and normalized to the async psycopg driver.

If `CHECKPOINT_DATABASE_URL` is set, it must also be a reachable Postgres connection string;
otherwise leave it empty. Production startup rejects a `DATABASE_URL` whose host is
`localhost`, `127.0.0.1`, or `::1` and reports the configuration error directly.
