# scorer.py
# =============================================================================
# LLM-Based Semantic Intent Scorer for aether-pulse-x
# =============================================================================
# "The LLM must understand intent, not match strings."
# — PULSE_X_DISCOVERY_CONTEXT.md
# =============================================================================

import json
from datetime import datetime, timezone
import anthropic
from config import ANTHROPIC_API_KEY, SCORE_THRESHOLD, RECENCY_HOURS_THRESHOLD

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Discovery Context — fed to Claude for semantic scoring
DISCOVERY_CONTEXT = """You are scoring X (Twitter) posts for relevance to AETHER, a self-educating agent framework by 864 Zeros LLC.

## Who We Are
864 Zeros LLC builds self-educating agent systems. AETHER's core thesis: agents are skills, not code. A skill lives in a 5-file capsule with identity, knowledge, and behavior. It verifies its own outputs. When it fails, it teaches itself — autonomously. The model is replaceable. The skill is the asset.

## The Gap We Fill
Most agent systems today are:
- Flat markdown files with instructions (no verification, no memory, no growth)
- Prompt wrappers around an LLM (tool routers, orchestrators, harnesses)
- Microservice chains pretending to be agents (stateless, fail the same way every time)
- RAG pipelines with no accountability layer

None answer: what happens when the agent is wrong? AETHER answers that.

## Intent Tiers (Score Accordingly)

T1 — DIRECT (Score: 0.95+)
Mentions AETHER, 864 Zeros, Jeff Conn, or cites our Zenodo/GitHub.

T2 — TECHNICAL MATCH (Score: 0.85-0.95)
Uses mechanisms we've built: verification layers, compiled knowledge graphs, self-education, agent capsules, accountability in agents.

T3 — PROBLEM MATCH (Score: 0.75-0.85)
Describes pain we solve:
- "My agents hallucinate and I can't stop it"
- "Agents fail the same way every time"
- "No way to audit what the agent actually knows"
- "LLM outputs are non-deterministic"
- "Vendor lock-in — one model goes down, everything breaks"

T4 — PHILOSOPHICAL ALIGNMENT (Score: 0.65-0.75)
Aligns with our worldview:
- "The future of AI is embodied, not orchestrated"
- "Agents should be roles, not scripts"
- "Intelligence should be in the system, not just the model"

T5 — ADJACENT DOMAIN (Score: 0.55-0.65)
Related fields: formal verification for AI, knowledge graphs for grounding, edge AI, AI governance.

T6 — COMPETITIVE (Score: 0.50-0.60)
Discussing LangChain, CrewAI, AutoGen, RAGAS limitations — opportunity for kind engagement.

BELOW T6 — NOT RELEVANT (Score: < 0.50)
General LLM hype, model benchmarks, AI art, crypto+AI, pure RAG optimization, bot/aggregator accounts.

## Pain Patterns (High Signal)
- Author frustrated that agents fail in repeatable ways
- Author cannot audit why an agent gave wrong answer
- Author rebuilding same verification logic across projects
- Author locked into one LLM provider
- Author's agent works in dev but drifts in production

## Architecture Patterns (High Signal)
- Author showing flat file structure for agents (markdown, JSON, YAML)
- Author describing orchestration layer with no grounding beneath
- Author building tool router and calling it an agent
- Author using RAG but no verification after retrieval

## Exclusion Patterns (Low/Zero Score)
- General LLM hype with no structural focus
- GPT vs Claude comparisons without architecture discussion
- AI art / generative media
- Crypto + AI
- Pure embedding/RAG tuning without verification discussion
- Posts from bots or aggregator accounts
- Praise for "flexibility" without accountability critique

## The Ideal Post
A builder, researcher, or AI practitioner who has identified a problem AETHER solves — without knowing AETHER exists. They're showing architecture, hitting a wall, or expressing frustration about agents, verification, reliability, or portability.
"""

SCORING_PROMPT = """Analyze this X post and score its relevance to AETHER.

POST BY @{author}:
"{text}"

Engagement: {likes} likes, {reposts} reposts, {replies} replies

Return a JSON object with exactly these fields:
{{
  "tier": "T1" | "T2" | "T3" | "T4" | "T5" | "T6" | "EXCLUDE",
  "score": 0.0-1.0,
  "reasoning": "One sentence explaining why this tier/score",
  "gap_identified": "The specific gap or pain point if any, else null",
  "is_builder": true/false
}}

Be strict. Most posts should score below 0.50. Only genuine builder pain or technical architecture discussions score above 0.65."""


def get_recency_bonus(created_at_str):
    """Calculate recency bonus/penalty based on post age."""
    if not created_at_str:
        return 0.0
    try:
        created = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        hours_old = (now - created).total_seconds() / 3600
        if hours_old <= 6:
            return 0.10    # Very fresh — bonus
        elif hours_old <= 24:
            return 0.05    # Fresh — small bonus
        elif hours_old <= RECENCY_HOURS_THRESHOLD:
            return 0.0     # Acceptable — no adjustment
        else:
            return -0.15   # Stale — penalty
    except Exception:
        return 0.0


def get_hours_old(created_at_str):
    """Return hours since post was created, or None if unknown."""
    if not created_at_str:
        return None
    try:
        created = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        return round((now - created).total_seconds() / 3600, 1)
    except Exception:
        return None


def score_post_with_llm(post):
    """
    Use Claude to semantically score a post for AETHER relevance.
    Returns dict with tier, score, reasoning, gap_identified, is_builder.
    """
    prompt = SCORING_PROMPT.format(
        author=post.get("author", "unknown"),
        text=post.get("text", ""),
        likes=post.get("like_count", 0),
        reposts=post.get("repost_count", 0),
        replies=post.get("reply_count", 0)
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=DISCOVERY_CONTEXT,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON from response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text)
        return result

    except Exception as e:
        print(f"LLM scoring error for @{post.get('author', 'unknown')}: {e}")
        return {
            "tier": "EXCLUDE",
            "score": 0.0,
            "reasoning": f"Scoring error: {str(e)}",
            "gap_identified": None,
            "is_builder": False
        }


def score_post(post):
    """
    Score a post using LLM semantic analysis + recency adjustment.
    Returns final score float.
    """
    # Get LLM semantic score
    llm_result = score_post_with_llm(post)

    # Store LLM analysis in post for later use
    post["tier"] = llm_result.get("tier", "EXCLUDE")
    post["reasoning"] = llm_result.get("reasoning", "")
    post["gap_identified"] = llm_result.get("gap_identified")
    post["is_builder"] = llm_result.get("is_builder", False)

    base_score = llm_result.get("score", 0.0)

    # Apply recency adjustment
    recency_bonus = get_recency_bonus(post.get("created_at", ""))
    post["hours_old"] = get_hours_old(post.get("created_at", ""))

    # Final score (clamped to [0, 1])
    final_score = max(0.0, min(1.0, base_score + recency_bonus))

    return round(final_score, 3)


def filter_qualifying_posts(posts, replied_posts, max_drafts):
    """
    Filter posts above threshold, not already replied to,
    sorted by score descending, limited to max_drafts.
    """
    scored = []

    for i, post in enumerate(posts):
        if post["id"] in replied_posts:
            continue

        print(f"  Scoring post {i+1}/{len(posts)} by @{post.get('author', 'unknown')}...")
        score = score_post(post)

        # Log for visibility
        tier = post.get("tier", "?")
        reasoning_preview = post.get('reasoning', '')[:50].encode('ascii', 'replace').decode('ascii')
        print(f"    -> Tier: {tier} | Score: {score} | {reasoning_preview}...")

        if score >= SCORE_THRESHOLD:
            post["score"] = score
            scored.append(post)

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Return top N
    return scored[:max_drafts]
