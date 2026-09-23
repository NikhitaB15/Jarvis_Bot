import uuid
from datetime import datetime
from typing import List, Optional

from server.schemas import TelemetrySyncRequest, NudgeItem
try:
    from commands.groq_chat import GroqChat
except ImportError:
    GroqChat = None


class AICoachNudgeEngine:
    """Intelligent AI Coach engine that converts multi-sensor mobile & desktop context

    (UsageStats, Health Connect, Location, Calendar, Notifications) into actionable,
    goal-oriented personalized nudges.
    """

    def __init__(self, groq_client: Optional[any] = None, use_llm: bool = True):
        self.groq_client = groq_client
        if use_llm and self.groq_client is None and GroqChat:
            try:
                self.groq_client = GroqChat()
            except Exception:
                self.groq_client = None
        elif not use_llm:
            self.groq_client = None

    def generate_nudges(self, telemetry: TelemetrySyncRequest) -> List[NudgeItem]:
        nudges: List[NudgeItem] = []

        # 1. App Limit Overuse Nudges (UsageStatsManager)
        for app in telemetry.usage_stats:
            goal = app.goal_minutes_daily or 30  # Default 30 min limit if target app
            if app.goal_minutes_daily and app.usage_minutes_today > app.goal_minutes_daily:
                hours = app.usage_minutes_today // 60
                mins = app.usage_minutes_today % 60
                duration_str = f"{hours} hour {mins} minutes" if hours > 0 else f"{mins} minutes"
                
                nudge_text = (
                    f"You've spent {duration_str} on {app.app_name} today, "
                    f"exceeding your {app.goal_minutes_daily}-minute goal."
                )
                nudges.append(
                    NudgeItem(
                        id=str(uuid.uuid4()),
                        category="app_limit",
                        message=nudge_text,
                        priority="high",
                        suggested_action="set_app_timer",
                    )
                )

        # 2. Optimal Focus Window Optimization (Calendar & Study Habit Pattern)
        current_hour = datetime.now().hour
        # Default study window: 8 PM to 10 PM (20:00 - 22:00)
        is_evening_study_window = 20 <= current_hour <= 22
        if is_evening_study_window:
            nudges.append(
                NudgeItem(
                    id=str(uuid.uuid4()),
                    category="focus_window",
                    message="You usually study best between 8–10 PM. Shall I block notifications?",
                    priority="high",
                    suggested_action="block_notifications",
                )
            )

        # 3. Skill Practice Inactivity Reminders (Goal Tracking)
        for skill_name, days_inactive in telemetry.skill_inactivity_days.items():
            if days_inactive >= 3:
                nudges.append(
                    NudgeItem(
                        id=str(uuid.uuid4()),
                        category="skill_practice",
                        message=f"You haven't worked on {skill_name} for {days_inactive} days. Let's do one interview question now.",
                        priority="medium",
                        suggested_action="start_practice_session",
                    )
                )

        # 4. Geofenced Goal Nudges (Location Context)
        if telemetry.location_context and telemetry.location_context.place_tag.lower() == "office":
            nudges.append(
                NudgeItem(
                    id=str(uuid.uuid4()),
                    category="geofenced_goal",
                    message="You're at the office. Want to spend 30 minutes on your GCP certification after work?",
                    priority="medium",
                    suggested_action="schedule_certification_block",
                )
            )

        # Optional LLM Enhancement: If Groq is active and nudges were generated, polish them with AI tone
        if self.groq_client and nudges:
            nudges = self._enhance_nudges_with_llm(nudges, telemetry)

        return nudges

    def _enhance_nudges_with_llm(self, nudges: List[NudgeItem], telemetry: TelemetrySyncRequest) -> List[NudgeItem]:
        """Optionally enhance nudge phrasing using Groq LLM for natural tone."""
        try:
            prompt = (
                f"You are Jarvis, an AI Coach. Enhance the following notification nudge to be encouraging, "
                f"concise (1 sentence), and clear:\n"
                f"Original: {nudges[0].message}"
            )
            enhanced_msg = self.groq_client.chat(prompt)
            if enhanced_msg and len(enhanced_msg) > 10 and "trouble connecting" not in enhanced_msg:
                # Retain key numbers/facts, update message
                nudges[0].message = enhanced_msg
        except Exception:
            pass  # Fallback gracefully to deterministic prompt
        return nudges
