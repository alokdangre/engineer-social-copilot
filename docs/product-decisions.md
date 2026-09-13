# Product Decisions and Deferred Scope

This document preserves the reasoning that led to the current product scope. These are product decisions, not permanent limitations.

## Target user

The first product is a social media and career manager for an individual technical professional. Its job is to help that person become known for credible technical work, connect with founders and maintainers, improve job prospects, and develop DevRel capability.

It is not initially a multi-brand marketing suite or a tool for managing a company's campaign calendar.

## Three compulsory external apps

The first version uses:

1. **GitHub** for evidence of what the user builds, learns, maintains, and contributes.
2. **X** for fast-moving technical discussion, trends, public comments and replies, reposts with opinions, and relationship building.
3. **LinkedIn** for professional identity, career visibility, founder and recruiter context, and longer professional content.

These three form one loop: GitHub supplies proof; X exposes the user to technical conversations; LinkedIn develops professional reputation; outcomes on X and LinkedIn influence what the user should explain, learn, or build next.

## Why X is included

X is useful for the product because many technical conversations happen in public and evolve quickly. It gives the agent opportunities to recommend timely replies, precise comments, useful reposts, and interaction with developers, founders, maintainers, and DevRel practitioners.

The agent should use trends selectively. It should never post about an unrelated trend simply for reach or automate engagement to force exposure.

## Why the user acts manually at first

The product drafts and recommends actions, while the user manually publishes and interacts. This preserves final judgment, helps the agent learn the user's real voice from edits, reduces accidental posts or replies, and avoids beginning the product with high-risk platform automation.

Approval and execution remain separate states so the learning system never treats an approved draft as a published result.

## Why Notion is not required

The user should be able to tell the agent what happened directly. The agent's own structured memory stores goals, skills, projects, reading, hackathons, opinions, relationships, drafts, feedback, and strategy as separate linked records.

Notion would duplicate that core function and make the user maintain a second system. A future export or optional Notion integration could help users who already organize their work there, but it is not a dependency.

## Why Canva is not required

Strong niche relevance, a clear idea, real evidence, and useful timing matter more than elaborate design. The agent can recommend simple text posts, screenshots, diagrams, code excerpts, or straightforward images when they improve understanding.

Canva or another design tool can be added later for repeatable visual systems, carousels, event material, or brand-heavy content. It is not required to validate whether the core research and recommendation loop works.

## Why Instagram is deferred

Instagram can provide marketing reach, but its strongest technical-discovery strategy often depends on a consistent visual or short-video workflow. The product does not currently aim to generate artificial-looking AI Reels or require the user to produce regular video.

Instagram becomes a good later addition if the user wants to record real demos, event clips, screen walkthroughs, or face-to-camera explanations. The system can then repurpose authentic source material rather than fabricate a video persona.

## Why a blog platform is deferred

Long-form writing remains valuable for technical credibility, search visibility, explanations, and portfolio evidence. In the first version, the agent may research existing blogs, recommend an article, and prepare a draft, but publishing can remain manual on the user's existing site or preferred platform.

A blog or CMS connector should be added when long-form publishing becomes frequent enough to justify a fourth integration. The choice should consider ownership, portability, search indexing, API availability, and the user's existing audience rather than selecting a platform merely because it is popular.

## SEO, AEO, and trusted coverage

The earlier SEO and answer-engine idea is valid, but it is a later product layer. A known technical professional needs a discoverable body of trustworthy material beyond social posts:

- a clear personal site and project pages;
- useful articles answering real technical questions;
- consistent identity and topic signals across profiles;
- original projects, benchmarks, documentation, talks, and case studies;
- legitimate mentions, interviews, podcasts, guest posts, and community contributions on relevant sites;
- accurate structured information that search and answer systems can understand.

The agent can later recommend which topic deserves a durable article, which existing work should become a case study, where a genuine expert contribution fits, and which missing proof weakens discoverability.

Paid placement or a high-authority mention does not guarantee ranking or AI citation. Outreach must seek relevant editorial value and disclose sponsorship where required. The system should measure discoverability, branded search, citations, referral traffic, and qualified outcomes instead of promising a rank.

Possible later integrations include a user-owned blog or CMS, an SEO/AEO research service, search analytics, and a PR or media-research service. They are additions to the core three-app loop, not replacements for it.

## No permanent app limit

Three apps are compulsory for the first coherent product, not a permanent maximum. Add another app only when it owns a distinct job that the current system cannot handle cleanly and its access rules support that use.

## Content production position

- Simple posts and images are acceptable when they match the niche and give the target audience something useful.
- AI-assisted images can be used when they clarify an idea and the user approves them.
- The agent should not invent personal photos, project evidence, events, testimonials, or results.
- Video should preferably come from authentic demonstrations, talks, screen recordings, or the user rather than a fully fabricated persona.
- Content quality comes from specificity, truth, usefulness, and perspective before visual polish.
