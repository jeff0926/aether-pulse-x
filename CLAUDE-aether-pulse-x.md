# aether-pulse-x — Claude Project Instructions

**Product:** aether-pulse-x — Social Engagement Monitor & Draft Engine
**Company:** 864 Zeros LLC
**Parent Framework:** AETHER (Adaptive Embodied Thinking : Holistic Evolutionary Runtime)
**Parent Department:** GTM Office (SIGNAL role)
**Version:** 1.0
**Date:** 2026-03-26

---

## What Is aether-pulse-x

aether-pulse-x is a standalone feature brick that monitors X (Twitter) for high-engagement posts
in the AI agent space, scores them for relevance, drafts a reply in Jeff Conn's voice, and delivers
the draft to Jeff via Telegram. Jeff reviews, copies, and posts. One human action. Everything else
autonomous.

This brick is the X adapter of the aether-pulse social engagement framework. It is one of:

```
aether-pulse              ← core brick (platform agnostic)
├── aether-pulse-x        ← this brick
├── aether-pulse-reddit   ← future
├── aether-pulse-linkedin ← future
└── aether-pulse-hn       ← future
```

aether-pulse-x mirrors the abstraction pattern of llm.py in the AETHER core framework.
The core logic — monitor, score, draft, notify — is identical across all platforms.
Only the adapter changes.

---

## Why This Exists

On 2026-03-26, Jeff manually found a post by @Suryanshti777 showing a .claude/agents/
directory of flat markdown agent files. He replied with a single technical observation:

> "Interesting architecture. The missing layer: what happens when these agents fail?
> Without verification and self-education, they fail the same way every time.
> We built that layer. Any .md file becomes a self-verifying, self-educating agent."

Result: 735 impressions, 200 engagements, 131 link clicks, 18% CTR.

That pattern is repeatable. This brick automates the discovery and drafting.
Jeff remains the only one who posts.

---

## The Proven Pattern

```
TRIGGER:     Post about AI agents, agent frameworks, or agent architecture
             with 50+ likes, in English, not a retweet

OBSERVATION: Identify the specific technical gap AETHER addresses
             (no verification, no self-education, flat prompts, microservice wrappers)

REPLY FORMAT:
  [Kind acknowledgment of what's interesting]
  [The missing layer or alternative assumption — one sentence]
  [What we built — one sentence]
  [Zenodo link: https://zenodo.org/records/19212829]

TONE:        Kind. Technical. Curious. Never promotional. Never aggressive.

RESULT:      Telegram message to Jeff with drafted reply + original post URL
             Jeff copies reply. Jeff posts. Done.
```

---

## Proof Points to Include in Drafts

These are the verified, citable facts that can appear in replies:

- "Any .md file becomes a self-verifying, self-educating agent"
- "Jefferson capsule: AEC score 0.143 → 0.889, zero human intervention"
- "Sub-millisecond verification. No embeddings. No vector DB."
- "The model didn't change. The skill did."
- "Intelligence is intrinsic to the system, not the model."
- "Most systems are toolchains. This is an organization."
- Zenodo DOI: https://zenodo.org/records/19212829
- GitHub: https://github.com/jeff0926/aether

Never claim more than what is proven. Never fabricate metrics.

---

## Keywords to Monitor

```python
KEYWORDS = [
    '"AI agents" min_faves:50 lang:en -filter:retweets',
    '"agentic AI" min_faves:50 lang:en -filter:retweets',
    '".claude/agents" min_faves:50 lang:en',
    '"SKILL.md" min_faves:50 lang:en',
    '"agent framework" min_faves:50 lang:en -filter:retweets',
    '"LLM verification" min_faves:50 lang:en',
    '"agent harness" min_faves:50 lang:en',
    '"building agents" min_faves:50 lang:en -filter:retweets',
    '"microservice" "agents" min_faves:50 lang:en',
    '"prompt wrapper" min_faves:50 lang:en'
]
```

---

## Scoring Model

Each post is scored 0.0 — 1.0 for relevance before drafting:

| Signal | Weight | Description |
|--------|--------|-------------|
| Keyword match | 0.30 | How many target keywords appear |
| Engagement level | 0.25 | Likes + reposts + replies normalized |
| Technical depth | 0.20 | Does the post discuss architecture, not just tools |
| Gap signal | 0.15 | Does the post reveal the absence of verification/education |
| Author relevance | 0.10 | Is the author a builder, researcher, or AI practitioner |

**Threshold: 0.65** — only posts scoring 0.65+ get a draft generated.
Posts below threshold are logged but no draft is sent.

---

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| X scraping | Apify — Tweet Scraper V2 | $29/mo Starter |
| Scheduling | Apify scheduled runs | Included |
| Draft generation | Claude API (claude-sonnet) | Pay per use |
| Notification | Telegram Bot API | Free |
| Learning log | SQLite local | Free |
| Runtime | Python 3.11+ | Free |

---

## AETHER Integration

aether-pulse-x is both a standalone tool AND an AETHER capsule.

**As standalone:** Runs independently. Monitors X. Drafts replies. Sends Telegrams.

**As AETHER capsule:** Composes with other pulse agents under a parent orchestrator.
On completion of each cycle, broadcasts a DAI Pulse to the 864 Zeros dashboard:

```json
{
  "phase": "complete",
  "source": "aether-pulse-x",
  "content": {
    "posts_scored": "14",
    "drafts_sent": "3",
    "top_post_score": "0.87",
    "top_post_url": "https://x.com/...",
    "telegram_delivered": "yes"
  }
}
```

This pulse renders on the GTM Office wall of the 864 Zeros operational dashboard.
The company is visibly alive.

---

## Learning Loop

Every Telegram draft that Jeff posts becomes a training signal.
Every draft Jeff ignores is a negative signal.
Engagement results (CTR, impressions, link clicks) feed back into scoring weights.

```
Draft sent → Jeff posts → engagement logged → scoring weights updated
Draft sent → Jeff ignores → negative signal logged → draft quality improves
```

The capsule self-educates. The GTM agent gets smarter through every cycle.

---

## 864 Zeros Philosophy

- **KISS** — Monitor, score, draft, notify. Four steps. No more.
- **Human in the loop** — Jeff always posts. Never auto-post. Never.
- **Feature brick** — Standalone and composable. Clean input/output edges.
- **Vanilla** — Python stdlib + Apify client + Telegram API. No heavy frameworks.
- **Learning org** — Every success and failure feeds the next cycle.

---

## Hard Rules

- **NEVER auto-post to X** — Telegram draft only. Jeff posts manually. Always.
- **NEVER fabricate metrics** — Only use verified proof points listed above.
- **NEVER post more than 3 drafts per day** — Quality over quantity.
- **NEVER reply to the same post twice** — Log all replied post IDs.
- **NEVER be aggressive or confrontational** — Kind, technical, curious only.
- **NEVER include SAP in any draft** — No employer references anywhere.
- **NEVER skip the scoring threshold** — 0.65 minimum. No exceptions.

---

## File Structure

```
aether-pulse-x/
├── CLAUDE.md                    ← this file
├── claude-build.md              ← build specification
├── pulse_x.py                   ← main entry point
├── scraper.py                   ← Apify X scraper adapter
├── scorer.py                    ← post relevance scoring engine
├── drafter.py                   ← Claude API reply draft generator
├── notifier.py                  ← Telegram notification delivery
├── logger.py                    ← learning loop + engagement log
├── config.py                    ← keywords, thresholds, API keys
├── capsule/                     ← AETHER capsule files
│   ├── manifest.json
│   ├── definition.json
│   ├── persona.json
│   ├── kb.md
│   └── kg.jsonld
├── data/
│   ├── engagement_log.db        ← SQLite learning log
│   └── replied_posts.json       ← deduplication registry
├── .env                         ← API keys (gitignored)
└── tests/
    ├── test_scraper.py
    ├── test_scorer.py
    ├── test_drafter.py
    └── test_notifier.py
```

---

## Environment Variables

```
APIFY_API_TOKEN=
ANTHROPIC_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ZENODO_URL=https://zenodo.org/records/19212829
GITHUB_URL=https://github.com/jeff0926/aether
SCORE_THRESHOLD=0.65
MAX_DRAFTS_PER_DAY=3
RUN_INTERVAL_HOURS=6
```

---

## Success Criteria

- Finds 5+ qualifying posts per day
- Drafts 1-3 replies per day scoring above threshold
- Delivers drafts to Telegram within 5 minutes of qualifying post detection
- Jeff posts at least 1 reply per day from drafts
- Engagement log captures CTR and impressions for every posted reply
- Learning loop updates scoring weights weekly

---

## Out of Scope for v1

- Auto-posting to X
- Reddit, LinkedIn, HN adapters (future aether-pulse-* bricks)
- Dashboard rendering (future — feeds DAI Pulse)
- Multi-account management
- Image or media attachment in replies
- Thread creation (replies only, not new threads)
