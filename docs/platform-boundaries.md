# Platform Roles and Boundaries

Last reviewed against official documentation: 2026-09-13.

This document records planning constraints, not a final legal or integration review. Platform products, permissions, prices, metrics, and policies can change; they must be rechecked before implementation and release.

## First-version connection model

The product connects three real external apps: GitHub, X, and LinkedIn. “Connect” means using a platform-supported authorization or another permitted user-controlled source. It does not mean driving the website with an automated browser.

Supported input modes may include:

- official connected-account access with the minimum necessary permissions;
- public data obtained through an official allowed interface;
- an account data export supplied by the user;
- links, text, screenshots, files, or analytics supplied by the user;
- manual confirmation when a platform does not expose the required data.

All input records keep their access method and source-specific usage and retention rules.

## Responsibility matrix

| Capability | GitHub | X | LinkedIn |
| --- | --- | --- | --- |
| Establish user identity and history | Repositories and contribution evidence | Profile and past public voice | Professional history and positioning |
| Capture ongoing work | Commits, pull requests, issues, releases, documentation | User-reported or connected post activity | User-reported or connected post activity |
| Analyze own content | Project attention and contribution outcomes | Available owned-post analytics and visible interactions | Available member-post analytics and visible interactions |
| Research ecosystem | Public repositories, issues, releases, discussions | Permitted public post search, topics, and conversations | Only through approved/permitted access or user-supplied material |
| Recommend actions | Build, document, contribute, improve portfolio | Posts, comments, replies, reposts, relationships | Professional posts, comments, relationships, career positioning |
| Execute in version one | User performs repository changes separately | User manually publishes and interacts | User manually publishes and interacts |

## GitHub

### Intended use

GitHub is the main evidence source for technical work. The agent can use selected repository contents and activity to identify projects, contributions, technologies, decisions, failures, lessons, documentation gaps, and possible public stories.

### Access approach

Prefer a GitHub App with read-only, repository-specific permissions because GitHub Apps support more granular access than broad OAuth scopes. Ask the user to choose the repositories included. Private repositories and organization resources require explicit access and stricter publication boundaries.

### Interpretation boundaries

- A repository does not prove that the user wrote every line.
- A commit count does not measure skill or impact.
- A merged contribution does not prove sole ownership.
- A dependency in a manifest does not prove expertise.
- A project description does not prove production use or business results.
- Private code, issue discussion, secrets, and employer material must not become public content without explicit permission.

Official references:

- [GitHub: Differences between GitHub Apps and OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps)
- [GitHub: Authorizing OAuth apps](https://docs.github.com/en/apps/oauth-apps/using-oauth-apps/authorizing-oauth-apps)

## X

### Intended use

X supports technical discovery, short-form posts, real-time discussions, public relationship building, and analysis of the user's own content. Permitted public search can help identify relevant topics, conversations, questions, and visible participants.

X documents public post metrics such as impressions, likes, reposts, replies, quotes, and bookmarks. User-context access may provide owned-post metrics such as clicks and engagements, with time limits for some private, organic, and promoted metrics.

### First-version action boundary

The agent drafts and recommends; the user manually posts, replies, comments, follows, and reposts. The product does not script the X website, automatically post about trends, auto-like, bulk-follow, or send repetitive replies.

### AI and data boundary

X's current developer guidance prohibits using X data to train AI or machine-learning models outside its allowed exceptions. This product should use permitted data at inference time to prepare recommendations and maintain scoped operational strategy records. It must not use X data to train or fine-tune a foundation model. Any long-term storage, derived data, off-X matching, display, or deletion behavior needs a policy review before implementation.

Official references:

- [X API: Metrics](https://docs.x.com/x-api/fundamentals/metrics)
- [X: Automation rules](https://help.x.com/en/rules-and-policies/x-automation)
- [X: Developer Guidelines](https://docs.x.com/developer-guidelines)
- [X Developer Policy](https://docs.x.com/developer-terms/policy)

## LinkedIn

### Intended use

LinkedIn supports professional profile analysis, positioning, long-form professional posts, visible professional interactions, and the user's own post analytics where approved access is available.

LinkedIn's current member-post analytics documentation lists metrics including impressions, members reached, reshares, reactions, comments, saves, sends, link clicks, followers gained from content, and profile views from content. Availability depends on approval, product tier, permissions, and the exact user/account scenario.

### Access and automation boundary

LinkedIn prohibits third-party crawlers, bots, browser extensions, and other software that scrape the site or automate activity. The product must not automate the LinkedIn website. Connected functionality must use approved APIs and permissions; otherwise the user supplies links, exports, screenshots, or manual context and acts manually.

### Member-data boundary

LinkedIn's Marketing API restricted-use guidance places strict limits on member data and its derivatives, including purpose, combination with other data, display, and short storage periods for some social activity and profile data. It also prohibits using that API member data for recruiting, sales prospecting, lead creation, and similar uses.

Therefore:

- the product must not build a cross-platform prospect database from LinkedIn API member data;
- LinkedIn-derived member data must not be silently combined with GitHub and X to enrich profiles;
- job or founder outreach recommendations must not depend on prohibited LinkedIn API prospecting;
- opportunity discovery should use allowed sources, user-supplied context, and native user activity;
- source-specific retention and display restrictions must remain attached to LinkedIn-derived records and derivatives;
- exact use cases require review during the LinkedIn app approval process.

Official references:

- [LinkedIn: Prohibited software and extensions](https://www.linkedin.com/help/linkedin/answer/a1341387/prohibited-software-and-extensions?lang=en)
- [LinkedIn: Community Management overview](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview?view=li-lms-2026-04)
- [LinkedIn: Member Post Statistics](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics?view=li-lms-2026-08)
- [LinkedIn: Restricted Uses of Marketing APIs and Data](https://learn.microsoft.com/en-us/linkedin/marketing/restricted-use-cases?view=li-lms-2026-06)

## Public research and visible engagement

Public posts, comments, replies, likes, reactions, and reposts can help the agent understand topics and visible participants when the platform and access method permit that use. They do not reveal every viewer.

The system must not infer sensitive attributes, friendship, hiring interest, purchasing intent, or private motivation from visible engagement. Repeated useful interaction may support a “repeated interaction” record; it does not automatically establish a personal relationship.

## Manual action and truthful status

The first version separates:

- agent recommended;
- user approved;
- content copied or platform opened;
- user reported action performed;
- action verified through an allowed source;
- outcome measured.

This separation protects analytics and strategy from treating drafts as published content.

## Pre-implementation review checklist

Before building each connector, verify:

- currently available APIs, products, pricing, and approval requirements;
- exact read and write permissions;
- whether the use case is allowed for individual profiles;
- storage and deletion requirements for raw and derived data;
- display, redistribution, and cross-platform combination rules;
- analytics definitions and availability windows;
- rate limits and operational cost;
- user consent, revocation, export, and deletion behavior;
- whether AI inference, memory, or model training has additional restrictions;
- which features require a manual user-supplied fallback.

If a platform denies the needed permission, the feature should degrade to user-supplied evidence or manual activity rather than unauthorized scraping or browser automation.
