import datetime
import random
import logging
import requests
import config

QUOTES = [
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Small steps every day lead to big results.", "Anonymous"),
    ("Your only limit is your mind.", "Anonymous"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
]

class DailyBriefing:
    """Generates Manu's morning briefing summary."""
    def __init__(self, memory):
        self.memory = memory
        self.log = logging.getLogger("Manu.Briefing")

    def generate(self, user_name: str) -> str:
        """Generate and return the full briefing text."""
        now = datetime.datetime.now()
        today = now.strftime("%A, %B %d, %Y")
        hour = now.hour

        period = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
        quote, author = random.choice(QUOTES)

        reminders = self.memory.list_reminders()
        reminder_section = ""
        if reminders:
            r_lines = ", ".join(r["title"] for r in reminders[:3])
            reminder_section = f" You have {len(reminders)} reminders: {r_lines}."

        weather_str = self._get_weather()

        briefing = (
            f"Good {period}, {user_name}! Today is {today}. "
            f"{weather_str}"
            f"{reminder_section} "
            f"Thought for the day: \"{quote}\" — {author}. "
            f"Ready to get started?"
        )
        return briefing

    def _get_weather(self) -> str:
        """Fetch weather from wttr.in (optional)."""
        try:
            city = self.memory.get_setting("city", "London")
            url = f"https://wttr.in/{city}?format=3"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                return f"{resp.text.strip()}. "
        except: pass
        return ""
