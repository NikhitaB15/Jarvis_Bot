import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from server.schemas import (
    TelemetrySyncRequest,
    UsageStatsItem,
    LocationContext,
    HealthDataItem,
)
from server.nudge_engine import AICoachNudgeEngine
from server.database import DatabaseManager


def test_app_limit_nudge():
    """Verify Instagram overuse generates target app limit nudge."""
    engine = AICoachNudgeEngine(groq_client=None)  # Test deterministic rule engine
    payload = TelemetrySyncRequest(
        client_id="android_test",
        platform="android",
        usage_stats=[
            UsageStatsItem(
                package_name="com.instagram.android",
                app_name="Instagram",
                usage_minutes_today=105,  # 1 hour 45 minutes
                goal_minutes_daily=30,
            )
        ],
    )
    nudges = engine.generate_nudges(payload)
    app_limit_nudges = [n for n in nudges if n.category == "app_limit"]
    
    assert len(app_limit_nudges) >= 1
    assert "Instagram" in app_limit_nudges[0].message
    assert "1 hour 45 minutes" in app_limit_nudges[0].message
    assert "exceeding your 30-minute goal" in app_limit_nudges[0].message
    print("[PASS] test_app_limit_nudge passed!")


def test_skill_practice_inactivity_nudge():
    """Verify 3-day inactivity generates practice reminder."""
    engine = AICoachNudgeEngine(groq_client=None)
    payload = TelemetrySyncRequest(
        client_id="android_test",
        platform="android",
        skill_inactivity_days={"ML interview prep": 3},
    )
    nudges = engine.generate_nudges(payload)
    skill_nudges = [n for n in nudges if n.category == "skill_practice"]
    
    assert len(skill_nudges) >= 1
    assert "ML interview prep" in skill_nudges[0].message
    assert "3 days" in skill_nudges[0].message
    print("[PASS] test_skill_practice_inactivity_nudge passed!")


def test_geofenced_office_nudge():
    """Verify office location triggers GCP certification prompt."""
    engine = AICoachNudgeEngine(groq_client=None)
    payload = TelemetrySyncRequest(
        client_id="android_test",
        platform="android",
        location_context=LocationContext(place_tag="office"),
    )
    nudges = engine.generate_nudges(payload)
    geo_nudges = [n for n in nudges if n.category == "geofenced_goal"]
    
    assert len(geo_nudges) >= 1
    assert "office" in geo_nudges[0].message
    assert "GCP certification" in geo_nudges[0].message
    print("[PASS] test_geofenced_office_nudge passed!")


def test_database_persistence():
    """Verify database logging of telemetry sync and nudges."""
    db = DatabaseManager(db_path="data/test_jarvis.db")
    db.save_telemetry_sync("client_1", "android", "2026-08-05T20:00:00", '{"test": true}')
    db.save_nudge(
        nudge_id="nudge_123",
        category="app_limit",
        message="Test nudge message",
        priority="high",
        suggested_action="test_action",
        ts="2026-08-05T20:00:00",
    )
    recent = db.get_recent_nudges(limit=5)
    assert len(recent) > 0
    assert recent[0]["id"] == "nudge_123"
    print("[PASS] test_database_persistence passed!")


if __name__ == "__main__":
    test_app_limit_nudge()
    test_skill_practice_inactivity_nudge()
    test_geofenced_office_nudge()
    test_database_persistence()
    print("\nAll AI Coach tests completed successfully!")
