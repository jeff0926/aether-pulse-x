# tests/test_scorer.py
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scorer import score_post, filter_qualifying_posts, get_recency_bonus, get_hours_old
from drafter import verify_power_word, get_x_adjusted_length


def test_high_relevance_post():
    """Test that posts about AI agents with high engagement score above threshold."""
    post = {
        "id": "test1",
        "text": "Building AI agents with flat markdown as the framework. The architecture uses LLM reasoning for verification. Agent pipeline fails without proper grounding and self-education.",
        "author": "airesearcher",
        "like_count": 500,
        "repost_count": 100,
        "reply_count": 50,
        "view_count": 10000
    }
    score = score_post(post)
    assert score >= 0.65, f"Expected score >= 0.65, got {score}"


def test_low_relevance_post():
    """Test that off-topic posts score below threshold."""
    post = {
        "id": "test2",
        "text": "Great weather today in San Francisco",
        "author": "randomuser",
        "like_count": 5,
        "repost_count": 0,
        "reply_count": 1,
        "view_count": 100
    }
    score = score_post(post)
    assert score < 0.65, f"Expected score < 0.65, got {score}"


def test_deduplication():
    """Test that already-replied posts are filtered out."""
    replied = {"post123"}
    posts = [
        {"id": "post123", "text": "AI agents framework architecture",
         "like_count": 100, "repost_count": 20, "reply_count": 5,
         "view_count": 2000, "author": "dev"},
        {"id": "post456", "text": "agent harness architecture pipeline LLM",
         "like_count": 200, "repost_count": 50, "reply_count": 15,
         "view_count": 5000, "author": "mleng"}
    ]
    qualifying = filter_qualifying_posts(posts, replied, 3)
    assert not any(p["id"] == "post123" for p in qualifying), "Already-replied post should be filtered"


def test_max_drafts_limit():
    """Test that max_drafts limit is enforced."""
    replied = set()
    posts = [
        {"id": f"post{i}", "text": "AI agents framework architecture LLM reasoning",
         "like_count": 200, "repost_count": 50, "reply_count": 15,
         "view_count": 5000, "author": "aidev"}
        for i in range(10)
    ]
    qualifying = filter_qualifying_posts(posts, replied, 3)
    assert len(qualifying) <= 3, f"Expected max 3 posts, got {len(qualifying)}"


def test_score_range():
    """Test that scores are always between 0 and 1."""
    posts = [
        {"id": "1", "text": "", "author": "", "like_count": 0, "repost_count": 0, "reply_count": 0},
        {"id": "2", "text": "AI agents framework architecture LLM reasoning verification self-education",
         "author": "airesearcher", "like_count": 10000, "repost_count": 5000, "reply_count": 1000},
    ]
    for post in posts:
        score = score_post(post)
        assert 0 <= score <= 1, f"Score {score} out of range [0, 1]"


# V1.1 Tests — Recency Scoring

def test_recency_bonus_fresh():
    """Test that very fresh posts (< 6 hours) get bonus."""
    now = datetime.now(timezone.utc)
    fresh_time = (now - timedelta(hours=2)).isoformat()
    bonus = get_recency_bonus(fresh_time)
    assert bonus == 0.15, f"Expected 0.15 bonus for 2hr old post, got {bonus}"


def test_recency_bonus_medium():
    """Test that medium-fresh posts (6-24 hours) get small bonus."""
    now = datetime.now(timezone.utc)
    medium_time = (now - timedelta(hours=12)).isoformat()
    bonus = get_recency_bonus(medium_time)
    assert bonus == 0.10, f"Expected 0.10 bonus for 12hr old post, got {bonus}"


def test_recency_bonus_acceptable():
    """Test that acceptable posts (24-48 hours) get no adjustment."""
    now = datetime.now(timezone.utc)
    acceptable_time = (now - timedelta(hours=36)).isoformat()
    bonus = get_recency_bonus(acceptable_time)
    assert bonus == 0.0, f"Expected 0.0 for 36hr old post, got {bonus}"


def test_recency_penalty_stale():
    """Test that stale posts (> 48 hours) get penalty."""
    now = datetime.now(timezone.utc)
    stale_time = (now - timedelta(hours=72)).isoformat()
    bonus = get_recency_bonus(stale_time)
    assert bonus == -0.20, f"Expected -0.20 penalty for 72hr old post, got {bonus}"


def test_recency_empty_string():
    """Test that empty created_at returns 0."""
    bonus = get_recency_bonus("")
    assert bonus == 0.0, f"Expected 0.0 for empty string, got {bonus}"


def test_hours_old():
    """Test hours_old calculation."""
    now = datetime.now(timezone.utc)
    test_time = (now - timedelta(hours=5)).isoformat()
    hours = get_hours_old(test_time)
    assert 4.9 <= hours <= 5.1, f"Expected ~5 hours, got {hours}"


# V1.1 Tests — Power Word Verification

def test_power_word_present():
    """Test that power word detection works."""
    draft_with_power = "Great approach. AETHER makes agents self-educating. zenodo.org/records/123"
    assert verify_power_word(draft_with_power), "Should detect 'self-educating'"


def test_power_word_absent():
    """Test that missing power word is detected."""
    draft_without_power = "Great approach. AETHER does something. zenodo.org/records/123"
    assert not verify_power_word(draft_without_power), "Should not find power word"


def test_power_word_case_insensitive():
    """Test that power word detection is case-insensitive."""
    draft = "AETHER provides VERIFIED output. zenodo.org/records/123"
    assert verify_power_word(draft), "Should detect 'VERIFIED' case-insensitively"


# V1.1 Tests — X-Adjusted Character Length

def test_x_adjusted_length_no_url():
    """Test character count with no URL."""
    text = "This is a simple test message."
    length = get_x_adjusted_length(text)
    assert length == len(text), f"Expected {len(text)}, got {length}"


def test_x_adjusted_length_with_url():
    """Test that URLs are counted as 23 characters."""
    url = "https://zenodo.org/records/19212829"
    text = f"Check this out: {url}"
    length = get_x_adjusted_length(text)
    expected = len("Check this out: ") + 23  # URL = 23 chars on X
    assert length == expected, f"Expected {expected}, got {length}"


def test_x_adjusted_length_long_url():
    """Test that long URLs still count as 23 characters."""
    long_url = "https://example.com/very/long/path/to/something/really/specific?query=value&more=stuff"
    text = f"Link: {long_url}"
    length = get_x_adjusted_length(text)
    expected = len("Link: ") + 23
    assert length == expected, f"Expected {expected}, got {length}"


if __name__ == "__main__":
    # Original v1.0 tests
    test_high_relevance_post()
    print("test_high_relevance_post passed")

    test_low_relevance_post()
    print("test_low_relevance_post passed")

    test_deduplication()
    print("test_deduplication passed")

    test_max_drafts_limit()
    print("test_max_drafts_limit passed")

    test_score_range()
    print("test_score_range passed")

    # V1.1 recency tests
    test_recency_bonus_fresh()
    print("test_recency_bonus_fresh passed")

    test_recency_bonus_medium()
    print("test_recency_bonus_medium passed")

    test_recency_bonus_acceptable()
    print("test_recency_bonus_acceptable passed")

    test_recency_penalty_stale()
    print("test_recency_penalty_stale passed")

    test_recency_empty_string()
    print("test_recency_empty_string passed")

    test_hours_old()
    print("test_hours_old passed")

    # V1.1 power word tests
    test_power_word_present()
    print("test_power_word_present passed")

    test_power_word_absent()
    print("test_power_word_absent passed")

    test_power_word_case_insensitive()
    print("test_power_word_case_insensitive passed")

    # V1.1 X-adjusted length tests
    test_x_adjusted_length_no_url()
    print("test_x_adjusted_length_no_url passed")

    test_x_adjusted_length_with_url()
    print("test_x_adjusted_length_with_url passed")

    test_x_adjusted_length_long_url()
    print("test_x_adjusted_length_long_url passed")

    print("\nAll tests passed!")
