# drafter.py
import anthropic
from config import ANTHROPIC_API_KEY, ZENODO_URL, POWER_WORDS, TAGLINES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# X counts every URL as exactly 23 characters
X_URL_LENGTH = 23

SYSTEM_PROMPT = """You are drafting a reply to an X (Twitter) post on behalf of Jeff Conn,
founder of 864 Zeros LLC and creator of AETHER — a self-verifying, self-educating agent framework.

Jeff's voice is: direct, technical, kind, curious. Never promotional. Never aggressive.
He engages as a peer, not a marketer.

AETHER key facts (use only these — never fabricate):
- Any .md file becomes a self-verifying, self-educating agent capsule
- Jefferson capsule: AEC score 0.143 → 0.889, zero human intervention
- 17 knowledge triples acquired autonomously
- Sub-millisecond verification. No embeddings. No vector DB. No GPU.
- 15 Python files, stdlib only, zero framework dependencies
- 33 self-educating capsules across 6 categories
- Intelligence is intrinsic to the system, not the model
- The model didn't change. The skill did.
- Paper: {zenodo_url}

POWER WORDS — use at least one in every reply:
- self-healing: agents recover from failure automatically
- self-educating: agents improve through failure automatically
- self-verifying: agent checks its own output before responding
- portable: copy the folder, copy the complete agent
- verified: deterministic output, not probabilistic guessing
- intrinsic: intelligence lives inside the agent, not outside
- capsule: the 5-file agent unit — the primitive
- grounded: every response verified against knowledge graph

TAGLINES — optionally close with one:
- "The model didn't change. The skill did."
- "Intelligence is intrinsic to the system, not the model."
- "Most systems are toolchains. This is an organization."

Reply rules:
1. Maximum 280 X-adjusted characters (every URL counts as 23 chars on X)
2. Start with one kind acknowledgment of what's interesting or valid
3. Identify the specific gap AETHER addresses — one sentence
4. One sentence on what AETHER does, using at least one POWER WORD
5. End with the Zenodo URL
6. No hashtags. No emojis. No exclamation points.
7. Never mention SAP or any employer
8. Never claim more than what the facts above support
""".format(zenodo_url=ZENODO_URL)


def get_x_adjusted_length(text):
    """
    Calculate X-adjusted character length.
    X counts every URL as exactly 23 characters regardless of actual length.
    """
    import re
    # Find all URLs in text
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)

    adjusted_length = len(text)
    for url in urls:
        # Subtract actual URL length, add X's 23-char count
        adjusted_length = adjusted_length - len(url) + X_URL_LENGTH

    return adjusted_length


def verify_power_word(draft):
    """Check if draft contains at least one power word."""
    draft_lower = draft.lower()
    return any(word in draft_lower for word in POWER_WORDS)


def draft_reply(post, retry_count=0):
    """
    Generate a reply draft for a qualifying post.
    Returns tuple of (draft string, x_adjusted_length).
    Ensures draft contains at least one power word.
    """
    # Add power word requirement on retry
    power_word_instruction = ""
    if retry_count > 0:
        power_word_instruction = f"\n\nIMPORTANT: Your previous draft did not contain a power word. You MUST include at least one of these words: {', '.join(POWER_WORDS)}"

    user_prompt = f"""Post by @{post['author']}:
"{post['text']}"

Post URL: {post['url']}
Likes: {post.get('like_count', 0)}
Score: {post.get('score', 0)}

Draft a reply that:
1. Acknowledges what's technically interesting about their approach
2. Identifies the specific verification or self-education gap
3. States what AETHER does about it — USE A POWER WORD
4. Ends with the paper URL: {ZENODO_URL}

Keep it under 280 X-adjusted characters (URL = 23 chars). Be kind and technical.{power_word_instruction}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    draft = message.content[0].text.strip()
    x_adjusted_length = get_x_adjusted_length(draft)

    # Enforce X-adjusted character limit
    if x_adjusted_length > 280:
        # Need to truncate — find safe truncation point
        # Remove URL if present, truncate, re-add URL
        import re
        url_pattern = r'https?://[^\s]+'
        draft_no_url = re.sub(url_pattern, '', draft).strip()
        # Calculate max chars for text (280 - 23 for URL - 1 for newline)
        max_text = 280 - X_URL_LENGTH - 1
        if len(draft_no_url) > max_text:
            draft_no_url = draft_no_url[:max_text-3] + "..."
        draft = f"{draft_no_url}\n{ZENODO_URL}"
        x_adjusted_length = get_x_adjusted_length(draft)

    # Verify power word is present
    if not verify_power_word(draft) and retry_count < 2:
        # Retry with explicit instruction
        return draft_reply(post, retry_count + 1)

    return draft, x_adjusted_length
