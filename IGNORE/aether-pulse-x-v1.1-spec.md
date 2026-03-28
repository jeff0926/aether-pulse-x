# aether-pulse-x — V1.1 Update Specification
**Product:** aether-pulse-x
**Version:** 1.0 → 1.1
**Date:** 2026-03-26
**Owner:** 864 Zeros LLC
**Status:** Ready for Claude Code — start new conversation under AETHER project

---

## Context

aether-pulse-x v1.0 was built and is operational. Claude Code has reviewed the build
and identified 5 critical failures and proposed fixes. This document captures all
required updates plus one new feature (snapshot mode) to be built in a single pass.

Do not take any action until this document is fully read. Report back with understanding
and a build plan before writing a single line of code.

---

## V1.0 Critical Failures — All Must Fix

### Failure 1 — Character Count Wrong
**File:** `drafter.py`
**Problem:** drafter.py counts actual URL length. X counts every URL as exactly 23
characters regardless of length. A draft with a 40-char Zenodo URL that is 280 chars
raw would actually be 263 chars on X — fine. But we might truncate valid drafts.
**Fix:**
```python
# WRONG
if len(draft) > 280:
    draft = draft[:250] + f"\n{ZENODO_URL}"

# CORRECT
url_length_on_x = 23
actual_url_length = len(ZENODO_URL)
url_adjustment = actual_url_length - url_length_on_x
x_adjusted_length = len(draft) - url_adjustment
if x_adjusted_length > 280:
    # truncate
```

---

### Failure 2 — Recency Not Scored
**File:** `scorer.py`
**Problem:** Posts older than 48 hours get low visibility on X. We might draft replies
to stale posts that nobody will see.
**Fix:** Add recency scoring to score_post():
```python
from datetime import datetime, timezone

def get_recency_bonus(created_at_str):
    try:
        created = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        hours_old = (datetime.now(timezone.utc) - created).total_seconds() / 3600
        if hours_old <= 6:
            return 0.15    # Very fresh — bonus
        elif hours_old <= 24:
            return 0.10    # Fresh — small bonus
        elif hours_old <= 48:
            return 0.0     # Acceptable — no adjustment
        else:
            return -0.20   # Stale — penalty
    except:
        return 0.0
```
Add recency bonus/penalty to final score calculation.

---

### Failure 3 — Power Words Not Enforced
**File:** `drafter.py`
**Problem:** The playbook requires every reply to contain at least one power word.
drafter.py does not verify this. A draft could go to Telegram without any power word.
**Fix:** Add verification step after generation:
```python
POWER_WORDS = [
    "self-healing", "self-educating", "portable", "verified",
    "intrinsic", "capsule", "grounded", "self-verifying"
]

def verify_power_word(draft):
    draft_lower = draft.lower()
    return any(word in draft_lower for word in POWER_WORDS)

# In draft_reply():
draft = generate_draft(post)
if not verify_power_word(draft):
    # Regenerate with explicit instruction to include power word
    draft = regenerate_with_power_word(post, draft)
```

---

### Failure 4 — No Follow Reminder in Telegram
**File:** `notifier.py`
**Problem:** Jeff must follow every account he replies to. The Telegram message doesn't
remind him. This is a hard rule in the playbook that gets missed.
**Fix:** Add follow reminder and recency info to Telegram message:
```python
message = f"""🎯 <b>AETHER-PULSE-X</b>

<b>Post by @{post['author']}</b>
Score: {post.get('score', 0)} | Likes: {post.get('like_count', 0)}
⏰ Posted: {hours_old} hours ago

<b>Original:</b>
{post['text'][:300]}

<b>Post URL:</b>
{post['url']}

<b>Draft Reply (copy and post):</b>
<code>{draft}</code>

<i>Characters: {x_adjusted_length}/280</i>

✅ <b>After posting: Follow @{post['author']}</b>"""
```

---

### Failure 5 — kb.md Is Generic
**File:** `capsule/kb.md`
**Problem:** The capsule's knowledge base doesn't contain the proven engagement example,
key learnings, or the engagement log. This is the capsule's long-term memory and it's empty.
**Fix:** Replace generic kb.md with full playbook content including:
- All power words with definitions
- All 6 taglines
- All verified proof points
- All gap signals
- The proven @Suryanshti777 example with metrics
- Key learnings from 2026-03-26
- Engagement log (updated after every posted reply)

Full kb.md content is provided in Section: Updated kb.md below.

---

## V1.1 New Feature — Snapshot Mode

### What It Does
Jeff uploads a screenshot or PDF of a research paper or X post. The system extracts
the key claims, identifies the gap AETHER fills, and drafts a reply or standalone post.
Sends to Jeff via Telegram exactly like monitor mode.

### Why It Exists
On 2026-03-26 Jeff manually found the Google paper "Agentic AI and the next intelligence
explosion" (arXiv:2603.20639). The paper directly aligns with AETHER's architecture.
Rather than manually drafting a reply, Jeff should be able to upload the screenshot and
get a draft instantly.

### Three Input Modes for V1.1
```
aether-pulse-x input modes:

MODE 1: Monitor (existing v1.0)
  Input:  Apify scheduled run
  Output: Telegram draft reply to X post

MODE 2: Snapshot (new v1.1)
  Input:  Image file (screenshot of paper or X post)
  Output: Telegram draft reply or standalone post

MODE 3: URL (new v1.1)
  Input:  URL of paper (arXiv, Zenodo, blog post)
  Output: Telegram draft reply or standalone post
```

### Snapshot Mode Implementation

**New file: `snapshot.py`**
```python
# snapshot.py
import anthropic
import base64
from pathlib import Path
from config import ANTHROPIC_API_KEY, PROOF_POINTS, ZENODO_URL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SNAPSHOT_SYSTEM_PROMPT = """You are analyzing a research paper or social media post screenshot
on behalf of Jeff Conn, founder of 864 Zeros LLC and creator of AETHER.

Your job:
1. Extract the key claims or problem statements from the image
2. Identify which specific claim or gap AETHER addresses
3. Draft a reply or standalone post in Jeff's voice

Jeff's voice: direct, technical, kind, curious. Never promotional.

AETHER key facts (verified — never fabricate):
- Any .md file becomes a self-verifying, self-educating agent capsule
- Jefferson capsule: AEC score 0.143 → 0.889, zero human intervention
- Sub-millisecond verification. No embeddings. No vector DB.
- Intelligence is intrinsic to the system, not the model.
- The model didn't change. The skill did.
- Paper: {zenodo_url}

Power words to use: self-healing, self-educating, portable, verified, intrinsic, capsule, grounded

Output format:
CLAIM: [the specific claim or problem from the image]
GAP: [what's missing that AETHER addresses]
DRAFT: [the reply or post — under 280 chars including URL counted as 23 chars]
TYPE: [reply or standalone]
""".format(zenodo_url=ZENODO_URL)

def process_snapshot(image_path):
    """
    Process a screenshot or image and generate a draft post.
    Returns dict with claim, gap, draft, and type.
    """
    image_data = Path(image_path).read_bytes()
    base64_image = base64.standard_b64encode(image_data).decode('utf-8')

    # Detect media type
    suffix = Path(image_path).suffix.lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(suffix, 'image/jpeg')

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SNAPSHOT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_image
                    }
                },
                {
                    "type": "text",
                    "text": "Analyze this image and produce a CLAIM, GAP, DRAFT, and TYPE."
                }
            ]
        }]
    )

    response = message.content[0].text
    return parse_snapshot_response(response)

def parse_snapshot_response(response):
    """Parse the structured response from Claude."""
    result = {}
    for line in response.split('\n'):
        for key in ['CLAIM', 'GAP', 'DRAFT', 'TYPE']:
            if line.startswith(f'{key}:'):
                result[key.lower()] = line[len(key)+1:].strip()
    return result

def process_url(url):
    """
    Fetch a URL and generate a draft post.
    Uses web fetch to get content then processes like snapshot.
    """
    import urllib.request
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')[:5000]  # First 5000 chars
    except Exception as e:
        return {"error": str(e)}

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SNAPSHOT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this content and produce a CLAIM, GAP, DRAFT, and TYPE:\n\n{content}"
        }]
    )

    return parse_snapshot_response(message.content[0].text)
```

**Update pulse_x.py to add CLI modes:**
```python
# pulse_x.py — updated entry point
import sys
from snapshot import process_snapshot, process_url
from notifier import send_snapshot_draft_to_telegram

def run_monitor_mode():
    # existing v1.0 logic
    pass

def run_snapshot_mode(image_path):
    result = process_snapshot(image_path)
    send_snapshot_draft_to_telegram(result)

def run_url_mode(url):
    result = process_url(url)
    send_snapshot_draft_to_telegram(result)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_monitor_mode()
    elif sys.argv[1] == '--snapshot':
        run_snapshot_mode(sys.argv[2])
    elif sys.argv[1] == '--url':
        run_url_mode(sys.argv[2])
```

**Usage:**
```bash
# Monitor mode (existing)
python pulse_x.py

# Snapshot mode (new)
python pulse_x.py --snapshot /path/to/screenshot.png

# URL mode (new)
python pulse_x.py --url https://arxiv.org/abs/2603.20639
```

**Update notifier.py — add snapshot Telegram format:**
```python
def send_snapshot_draft_to_telegram(result):
    message = f"""📸 <b>AETHER-PULSE-X SNAPSHOT</b>

<b>Claim detected:</b>
{result.get('claim', 'N/A')}

<b>Gap AETHER fills:</b>
{result.get('gap', 'N/A')}

<b>Draft ({result.get('type', 'reply').upper()}) — copy and post:</b>
<code>{result.get('draft', 'N/A')}</code>

✅ <b>Remember to follow the author after posting</b>"""

    asyncio.run(send_telegram_async(message))
```

---

## Updated capsule/kb.md

Replace the existing generic kb.md with this complete version:

```markdown
# AETHER Pulse X — Knowledge Base
**Version:** 1.1
**Updated:** 2026-03-26

## What AETHER Is
AETHER is a self-verifying, self-educating agent framework. Every agent is a 5-file
capsule with its own typed knowledge graph that compiles into deterministic verification
logic at load time. When verification fails, the agent self-educates — researches the gap,
validates new knowledge, and integrates it. The model is replaceable. The skill is the asset.

## Power Words (Use In Every Reply)
- self-healing: agents recover from failure automatically
- self-educating: agents improve through failure automatically
- portable: copy the folder, copy the complete agent
- verified: deterministic output, not probabilistic guessing
- intrinsic: intelligence lives inside the agent, not outside
- capsule: the 5-file agent unit — the primitive
- grounded: every response verified against knowledge graph
- self-verifying: agent checks its own output before responding

## Taglines (Close Every Reply With One)
- "The model didn't change. The skill did."
- "Intelligence is intrinsic to the system, not the model."
- "Most systems are toolchains. This is an organization."
- "Agents aren't wrappers. They're roles. The difference is knowledge."
- "The model is replaceable. The expertise is not."
- "The system is the product. The proof is in production."

## Verified Proof Points (Never Fabricate)
- Jefferson capsule: AEC score 0.143 → 0.889, zero human intervention
- 17 knowledge triples acquired autonomously
- Sub-millisecond verification — no embeddings, no vector DB, no GPU
- frontend-design SKILL.md → 73-node verification engine in one CLI pass
- 15 Python files, stdlib only, zero framework dependencies
- 33 self-educating capsules across 6 categories
- Paper: https://zenodo.org/records/19212829
- Repo: https://github.com/jeff0926/aether

## Gap Signals (These Mean AETHER Is Relevant)
- flat markdown
- prompt wrapper
- tool router
- microservice agents
- agent harness
- fragmented context
- scattered skills
- hallucination
- no memory
- fails the same way
- unreliable
- stateless
- chaining tools
- orchestrating
- middleware

## Reply Formula
[1 sentence — acknowledge the specific problem they named]
[1 sentence — name the root cause using AETHER framing]
[1 sentence — what AETHER does, use power words]
[Paper URL]
Total must be under 280 X-adjusted characters (every URL = 23 chars on X)

## Proven Example — Gold Standard (2026-03-26)
Post: @Suryanshti777 showing .claude/agents/ flat markdown files
279 likes, 19K impressions on original post

Reply sent:
"Interesting architecture. The missing layer: what happens when
these agents fail? Without verification and self-education,
they fail the same way every time.
We built that layer. Any .md file becomes a self-verifying,
self-educating agent.
zenodo.org/records/19212829"

Result: 750 impressions, 200 engagements, 131 link clicks, 18% CTR
This is the benchmark. Every draft should aspire to this quality.

## Engagement Log
| Date | Author | Topic | Post Likes | Our Impressions | Link Clicks | CTR |
|------|--------|-------|-----------|-----------------|-------------|-----|
| 2026-03-26 | @Suryanshti777 | .claude/agents flat markdown | 279 | 750 | 131 | 18% |
| 2026-03-26 | @sydneyrunkle | Agent harness middleware | High | 129 | TBD | TBD |
| 2026-03-26 | @ihtesham2005 | OpenViking fragmented context | 1100 | TBD | TBD | TBD |

## Key Learnings
- Replying to others' posts outperforms own thread for discovery
- 18% CTR is the benchmark — quality over quantity
- "Self-healing, self-educating" resonates immediately with AI builders
- Zenodo card renders on X — paper title visible without clicking
- Must address the specific problem in the post — not generic AETHER pitch
- Posts over 48hrs old get significantly less reply visibility
- Follow every account you reply to immediately after posting
- Max 3 replies per day — enforced by system
```

---

## Updated config.py

Add all missing playbook vocabulary:

```python
# Add to config.py

RECENCY_HOURS_THRESHOLD = 48  # Posts older than this get score penalty

POWER_WORDS = [
    "self-healing",
    "self-educating",
    "self-verifying",
    "portable",
    "verified",
    "intrinsic",
    "capsule",
    "grounded"
]

TAGLINES = [
    "The model didn't change. The skill did.",
    "Intelligence is intrinsic to the system, not the model.",
    "Most systems are toolchains. This is an organization.",
    "Agents aren't wrappers. They're roles. The difference is knowledge.",
    "The model is replaceable. The expertise is not.",
    "The system is the product. The proof is in production."
]

# Add missing gap signals
GAP_SIGNALS = [
    "flat markdown",
    "prompt wrapper",
    "tool router",
    "microservice",
    "agent harness",
    "fragmented context",
    "scattered skills",
    "hallucin",
    "no memory",
    "fails",
    "unreliable",
    "stateless",
    "chaining",
    "orchestrat",
    "middleware",
    "no verification",
    "no learning",
    "stale"
]
```

---

## Build Order for Claude Code

Execute in this exact order. No skipping. No combining steps.

1. Update `config.py` — add POWER_WORDS, TAGLINES, GAP_SIGNALS, RECENCY_HOURS_THRESHOLD
2. Update `scorer.py` — add recency scoring with get_recency_bonus()
3. Update `drafter.py` — fix URL character math, add power word verification
4. Update `notifier.py` — add follow reminder, recency info, X-adjusted char count
5. Update `capsule/kb.md` — replace with full playbook content above
6. Create `snapshot.py` — new file, snapshot and URL modes
7. Update `pulse_x.py` — add CLI argument handling for --snapshot and --url modes
8. Run all tests — confirm existing tests still pass
9. Add new tests for recency scoring and power word verification
10. Report back with test results before marking complete

---

## Done Criteria for V1.1

- [ ] Character counting uses X's 23-char URL rule
- [ ] Posts older than 48 hours receive score penalty
- [ ] Every draft contains at least one power word — verified programmatically
- [ ] Telegram message includes "Remember to follow @{author}"
- [ ] Telegram message shows "Posted X hours ago"
- [ ] Telegram message shows X-adjusted character count
- [ ] kb.md contains proven example, engagement log, key learnings
- [ ] `python pulse_x.py --snapshot image.png` works end to end
- [ ] `python pulse_x.py --url https://arxiv.org/...` works end to end
- [ ] All existing v1.0 tests still pass
- [ ] New tests for recency and power word verification pass

---

## Never Do

- Never auto-post to X
- Never fabricate engagement metrics
- Never skip the 0.65 score threshold
- Never reply to same post twice
- Never exceed 280 X-adjusted characters
- Never send more than 3 drafts per day
- Never mention SAP or employer in any draft
- Never add frameworks — stdlib + apify-client + anthropic + python-telegram-bot only
