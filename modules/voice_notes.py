import datetime
import json
import logging
from pathlib import Path
import config

class VoiceNotesManager:
    """Manages dictated voice notes with AI-generated titles."""
    def __init__(self, llm, tts, data_dir: Path):
        self.llm = llm
        self.tts = tts
        self.notes_dir = data_dir / "voice_notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.log = logging.getLogger("Manu.VoiceNotes")

    def save_note(self, content: str) -> str:
        """Save a voice note with AI-generated title."""
        title_prompt = (
            f"Generate a short 3-5 word title for this note. "
            f"Reply with ONLY the title, nothing else:\n{content[:200]}"
        )
        ai_title = self.llm.chat(title_prompt).strip().replace("/", "-").replace("\\", "-")
        if not ai_title or len(ai_title) > 50:
            ai_title = f"Note {datetime.datetime.now().strftime('%b %d %I%M%p')}"

        timestamp = datetime.datetime.now().isoformat()
        note = {
            "title": ai_title, "content": content, "created_at": timestamp
        }

        filename = self.notes_dir / f"{ai_title.replace(' ', '_')[:30]}_{timestamp[:10]}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(note, f, indent=2)

        self.log.info(f"Voice note saved: {ai_title}")
        return f"Note saved as '{ai_title}'."

    def list_notes(self, limit: int = 5) -> str:
        files = sorted(self.notes_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files: return "No saved voice notes."

        notes = []
        for f in files[:limit]:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                notes.append(f"• {data['title']} — {data['created_at'][:10]}")
            except: continue

        return "Your recent notes:\n" + "\n".join(notes)

    def read_last_note(self) -> str:
        files = sorted(self.notes_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files: return "No notes found."

        with open(files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        return f"Your note '{data['title']}': {data['content']}"

    def search_notes(self, keyword: str) -> str:
        results = []
        for f in self.notes_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if keyword.lower() in data["content"].lower() or keyword.lower() in data["title"].lower():
                    results.append(f"• {data['title']} — {data['created_at'][:10]}")
            except: continue

        if not results: return f"No notes found for '{keyword}'."
        return f"Notes matching '{keyword}':\n" + "\n".join(results[:5])
