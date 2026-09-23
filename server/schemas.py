from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UsageStatsItem(BaseModel):
    """App usage details from UsageStatsManager (or desktop tracker)."""
    package_name: str = Field(..., description="App package or binary name (e.g. com.instagram.android or chrome.exe)")
    app_name: str = Field(..., description="Human-readable app name (e.g. Instagram)")
    usage_minutes_today: int = Field(0, description="Total minutes spent on app today")
    goal_minutes_daily: Optional[int] = Field(None, description="Configured daily limit goal in minutes")


class HealthDataItem(BaseModel):
    """Health metrics snapshot from Health Connect."""
    sleep_hours_last_night: Optional[float] = Field(None, description="Hours of sleep recorded last night")
    steps_today: Optional[int] = Field(None, description="Step count today")
    active_calories_today: Optional[int] = Field(None, description="Active energy burned today")


class LocationContext(BaseModel):
    """Geofence or location state."""
    place_tag: str = Field("unknown", description="Place classification (e.g. office, home, gym, library)")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    duration_at_location_minutes: Optional[int] = None


class CalendarEvent(BaseModel):
    """Calendar event item."""
    title: str
    start_time: str
    end_time: str
    category: Optional[str] = Field("general", description="Event type: study, work, personal, exercise")


class NotificationItem(BaseModel):
    """Captured notification alert from NotificationListenerService."""
    package_name: str
    title: Optional[str] = None
    text: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class TelemetrySyncRequest(BaseModel):
    """Unified telemetry payload synced from mobile (Android) or desktop (Windows) clients."""
    client_id: str = Field("android_mobile", description="Device identifier or client type")
    platform: str = Field("android", description="android or windows")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    usage_stats: List[UsageStatsItem] = Field(default_factory=list)
    health_data: Optional[HealthDataItem] = None
    location_context: Optional[LocationContext] = None
    upcoming_calendar_events: List[CalendarEvent] = Field(default_factory=list)
    recent_notifications: List[NotificationItem] = Field(default_factory=list)
    
    # Skill / Goal progress tracking (days elapsed since last practice)
    skill_inactivity_days: Dict[str, int] = Field(
        default_factory=dict,
        description="Map of skill goal name to days since last practice (e.g. {'ML interview prep': 3, 'GCP certification': 1})"
    )


class NudgeItem(BaseModel):
    """Individual actionable AI coaching nudge."""
    id: str
    category: str = Field(..., description="Category: app_limit, focus_window, skill_practice, geofenced_goal, health")
    message: str = Field(..., description="User-facing personalized nudge text")
    priority: str = Field("medium", description="high, medium, low")
    suggested_action: Optional[str] = Field(None, description="Suggested quick action (e.g. block_notifications, open_app, start_timer)")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class NudgeResponse(BaseModel):
    """API response containing generated nudges."""
    status: str = "success"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    nudges: List[NudgeItem] = Field(default_factory=list)
    total: int = 0
