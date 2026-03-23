"""
Meeting Assistant Hook - AI-powered meeting management

Provides:
- Meeting scheduling and notes
- Action items tracking
- Meeting summaries
- Calendar integration templates
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict


class MeetingAssistantHook:
    """AI-powered meeting assistant for managing meetings and notes."""
    
    def __init__(self):
        self.meetings: List[Dict] = []
        self.current_meeting: Optional[Dict] = None
        self.storage_file = Path.home() / ".opencode_chat_meetings.json"
        self.load_meetings()
    
    def run(self, action: str = None, **kwargs) -> dict:
        """
        Execute meeting actions.
        
        Actions:
            - new: Create a new meeting
            - notes: Add notes to current meeting
            - summary: Generate meeting summary
            - action: Add action item
            - list: List all meetings
            - current: Get/set current meeting
            - extract: Extract action items from text
        """
        actions = {
            "new": self._create_meeting,
            "notes": self._add_notes,
            "summary": self._generate_summary,
            "action": self._add_action_item,
            "list": self._list_meetings,
            "current": self._get_current_meeting,
            "extract": self._extract_action_items,
            "agenda": self._create_agenda,
            "template": self._get_template,
        }
        
        if action is None:
            return {"available_actions": list(actions.keys())}
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available": list(actions.keys())}
        
        return actions[action](**kwargs)
    
    def load_meetings(self):
        """Load meetings from storage file."""
        try:
            if self.storage_file.exists():
                data = json.loads(self.storage_file.read_text())
                self.meetings = data.get("meetings", [])
        except:
            self.meetings = []
    
    def save_meetings(self):
        """Save meetings to storage file."""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            self.storage_file.write_text(json.dumps({"meetings": self.meetings}, indent=2))
        except:
            pass
    
    def _create_meeting(self, title: str = None, participants: str = None, 
                        duration: int = 60, **kwargs) -> dict:
        """Create a new meeting."""
        if not title:
            return {"error": "Meeting title is required"}
        
        participants_list = []
        if participants:
            participants_list = [p.strip() for p in participants.split(",")]
        
        meeting = {
            "id": len(self.meetings) + 1,
            "title": title,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "scheduled": kwargs.get("scheduled", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "duration_minutes": duration,
            "participants": participants_list,
            "notes": [],
            "action_items": [],
            "decisions": [],
            "status": "in_progress"
        }
        
        self.meetings.append(meeting)
        self.current_meeting = meeting
        self.save_meetings()
        
        return {
            "success": True,
            "meeting": meeting,
            "message": f"Meeting '{title}' created. Use /hook meeting notes=... to add notes."
        }
    
    def _add_notes(self, notes: str = None, **kwargs) -> dict:
        """Add notes to current meeting."""
        if not self.current_meeting:
            return {"error": "No active meeting. Create one first with /hook meeting new title='...'", "suggestion": "Use: /hook meeting new title='Weekly Standup'"}
        
        if not notes:
            return {"error": "Notes content is required"}
        
        self.current_meeting["notes"].append({
            "timestamp": datetime.now().strftime("%H:%M"),
            "content": notes
        })
        
        self.save_meetings()
        
        return {
            "success": True,
            "total_notes": len(self.current_meeting["notes"]),
            "recent_note": notes[:100] + "..." if len(notes) > 100 else notes
        }
    
    def _generate_summary(self, **kwargs) -> dict:
        """Generate a summary of the current meeting."""
        if not self.current_meeting:
            return {"error": "No active meeting"}
        
        meeting = self.current_meeting
        
        summary_parts = []
        summary_parts.append(f"# Meeting Summary: {meeting['title']}")
        summary_parts.append(f"\n**Date:** {meeting['created']}")
        summary_parts.append(f"**Duration:** {meeting['duration_minutes']} minutes")
        
        if meeting["participants"]:
            summary_parts.append(f"**Participants:** {', '.join(meeting['participants'])}")
        
        summary_parts.append("\n## Notes")
        for note in meeting["notes"]:
            summary_parts.append(f"- [{note['timestamp']}] {note['content']}")
        
        if meeting["action_items"]:
            summary_parts.append("\n## Action Items")
            for i, item in enumerate(meeting["action_items"], 1):
                summary_parts.append(f"{i}. [{item['assignee'] or 'Unassigned'}] {item['task']} (Due: {item.get('due', 'Not set')})")
        
        if meeting["decisions"]:
            summary_parts.append("\n## Decisions Made")
            for decision in meeting["decisions"]:
                summary_parts.append(f"- {decision}")
        
        return {
            "summary": "\n".join(summary_parts),
            "stats": {
                "total_notes": len(meeting["notes"]),
                "total_actions": len(meeting["action_items"]),
                "total_decisions": len(meeting["decisions"])
            }
        }
    
    def _add_action_item(self, task: str = None, assignee: str = None, 
                         due: str = None, priority: str = "medium", **kwargs) -> dict:
        """Add an action item to current meeting."""
        if not self.current_meeting:
            return {"error": "No active meeting"}
        
        if not task:
            return {"error": "Task description is required"}
        
        action_item = {
            "id": len(self.current_meeting["action_items"]) + 1,
            "task": task,
            "assignee": assignee,
            "due": due or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "priority": priority,
            "status": "pending",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        self.current_meeting["action_items"].append(action_item)
        self.save_meetings()
        
        return {
            "success": True,
            "action_item": action_item,
            "total_items": len(self.current_meeting["action_items"])
        }
    
    def _list_meetings(self, status: str = None, **kwargs) -> dict:
        """List all meetings."""
        meetings = self.meetings
        
        if status:
            meetings = [m for m in meetings if m.get("status") == status]
        
        meeting_list = []
        for m in reversed(meetings[-20:]):
            meeting_list.append({
                "id": m["id"],
                "title": m["title"],
                "date": m["created"],
                "status": m["status"],
                "action_count": len(m.get("action_items", [])),
                "notes_count": len(m.get("notes", []))
            })
        
        return {
            "meetings": meeting_list,
            "total": len(meeting_list)
        }
    
    def _get_current_meeting(self, **kwargs) -> dict:
        """Get or set current meeting."""
        if not self.current_meeting:
            return {
                "current": None,
                "message": "No active meeting",
                "suggestion": "Use /hook meeting new title='Meeting Title'"
            }
        
        return {
            "current": {
                "id": self.current_meeting["id"],
                "title": self.current_meeting["title"],
                "created": self.current_meeting["created"],
                "notes_count": len(self.current_meeting["notes"]),
                "action_items_count": len(self.current_meeting["action_items"])
            }
        }
    
    def _extract_action_items(self, text: str = None, **kwargs) -> dict:
        """Extract action items from text using patterns."""
        if not text:
            return {"error": "Text is required"}
        
        patterns = [
            r"@(\w+)\s+(.+?)(?:\s+by\s+|\s+during\s+|\s+before\s+|\s+until\s+)(.+?)(?:\.|$)",
            r"(?:TODO|FIXME|NEED TO|MUST|ACTION):\s*(.+?)(?:\s+-\s*|\s+@)(.+?)(?:\.|$)",
            r"(\w+)\s+(?:will|should|must|to)\s+(.+?)(?:\.|$)",
        ]
        
        items = []
        
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if any(keyword in line.upper() for keyword in ["TODO", "ACTION", "FIXME", "TODO:", "ACTION:"]):
                clean_line = re.sub(r"^[\s\-\*\d\.]+", "", line)
                assignee = re.search(r"@(\w+)", clean_line)
                items.append({
                    "type": "code_comment",
                    "task": re.sub(r"@\w+", "", clean_line).strip(),
                    "assignee": assignee.group(1) if assignee else None
                })
            
            deadline_match = re.search(r"(?:by|before|until|due|deadline)[:\s]+(\d{4}-\d{2}-\d{2}|\w+\s+\d+)", line, re.I)
            if deadline_match:
                due = deadline_match.group(1)
            else:
                due = None
            
            action_match = re.search(r"(?:@(\w+))?\s*(?:will|should|must|to|needs? to)\s+(.+)", line, re.I)
            if action_match:
                items.append({
                    "type": "implied",
                    "assignee": action_match.group(1),
                    "task": action_match.group(2).strip().rstrip("."),
                    "due": due
                })
        
        return {
            "extracted_items": items,
            "count": len(items),
            "suggestion": "Use /hook meeting action task='...' assignee='...' to add items"
        }
    
    def _create_agenda(self, topics: str = None, duration: int = 60, **kwargs) -> dict:
        """Create a meeting agenda from topics."""
        if not topics:
            return {"error": "Topics are required"}
        
        topic_list = [t.strip() for t in topics.split("|")]
        topic_count = len(topic_list)
        time_per_topic = max(5, duration // max(topic_count, 1))
        
        agenda_lines = []
        agenda_lines.append(f"# Meeting Agenda ({duration} min)")
        agenda_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        agenda_lines.append("\n## Agenda\n")
        
        for i, topic in enumerate(topic_list, 1):
            start_min = (i-1) * time_per_topic
            start_time = f"{start_min} min"
            agenda_lines.append(f"{i}. **{topic}** - {time_per_topic} min ({start_time})")
        
        agenda_lines.append("\n## Notes\n_(Space for taking notes during meeting)_\n")
        agenda_lines.append("\n## Action Items\n- [ ] \n")
        
        return {
            "agenda": "\n".join(agenda_lines),
            "topics": topic_list,
            "time_per_topic": time_per_topic
        }
    
    def _get_template(self, template_type: str = "standard", **kwargs) -> dict:
        """Get meeting templates."""
        templates = {
            "standard": """# Meeting Notes

**Date:** {date}
**Attendees:** 
**Location:** 

## Agenda
1. 
2. 
3. 

## Discussion Points


## Decisions Made


## Action Items
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
|      |       |          |        |

## Next Steps
""",
            "standup": """# Daily Standup - {date}

**Team:**

## Yesterday
- 

## Today
- 

## Blockers
- 

## Notes
""",
            "retro": """# Retrospective - {date}

## What Went Well
-

## What Could Be Improved
-

## Action Items
1. 
2. 
3. 

## Team Kudos
- 
""",
            "one_on_one": """# 1:1 Meeting - {date}

**With:**
**Topics to Discuss:**

## Updates/Status


## Challenges/Support Needed


## Career Development


## Action Items
-
"""
        }
        
        template = templates.get(template_type, templates["standard"])
        template = template.format(date=datetime.now().strftime("%Y-%m-%d"))
        
        return {
            "template": template,
            "type": template_type,
            "available_templates": list(templates.keys())
        }
    
    def help(self) -> str:
        return """
Meeting Assistant Hook - AI-powered meeting management
======================================================
Usage: /hook meeting action="new" title="Meeting Title"

Actions:
  new       - Create a new meeting
  notes     - Add notes to current meeting
  summary   - Generate meeting summary
  action    - Add action item
  list      - List all meetings
  current   - Get current meeting
  extract   - Extract action items from text
  agenda    - Create meeting agenda
  template  - Get meeting templates

Examples:
  /hook meeting new title="Sprint Planning" participants="John, Jane" duration=90
  /hook meeting notes="Discussed timeline and resources"
  /hook meeting action task="Update docs" assignee="John" priority="high"
  /hook meeting extract text="We need to fix the login bug @developer"
  /hook meeting agenda topics="Intro|Discussion| wrap up" duration=60
  /hook meeting template template_type="retro"
"""


if __name__ == "__main__":
    hook = MeetingAssistantHook()
    
    result = hook.run(action="template", template_type="standup")
    print(result["template"])
