"""
Email Hook - Full Email Client for Gmail, Outlook and more

Features:
- IMAP/SMTP email access
- Read, send, search emails
- Manage labels/folders
- OAuth2 support for Gmail
"""

import os
import json
import re
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path


class EmailHook:
    """Email client for reading, sending, and managing emails."""
    
    def __init__(self):
        self.storage_dir = Path.home() / ".opencode_chat" / "email"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.storage_dir / "config.json"
        self.cache_file = self.storage_dir / "cache.json"
        self.config = self._load_config()
        self.cache = self._load_cache()
    
    def _load_config(self) -> dict:
        """Load email configuration."""
        try:
            if self.config_file.exists():
                return json.loads(self.config_file.read_text())
        except:
            pass
        return {}
    
    def _save_config(self):
        """Save email configuration."""
        try:
            self.config_file.write_text(json.dumps(self.config, indent=2))
        except:
            pass
    
    def _load_cache(self) -> dict:
        """Load email cache."""
        try:
            if self.cache_file.exists():
                return json.loads(self.cache_file.read_text())
        except:
            pass
        return {"emails": [], "last_sync": None}
    
    def _save_cache(self):
        """Save email cache."""
        try:
            self.cache_file.write_text(json.dumps(self.cache, indent=2))
        except:
            pass
    
    def run(self, action: str = None, **kwargs) -> dict:
        """
        Execute email actions.
        
        Actions:
            - setup: Configure email account
            - status: Check connection status
            - list: List recent emails
            - read: Read specific email
            - send: Send email
            - reply: Reply to email
            - forward: Forward email
            - search: Search emails
            - labels: List labels/folders
            - sync: Sync emails
            - compose: Compose new email
            - delete: Delete email
            - draft: Save draft
            - mark: Mark as read/unread/starred
        """
        actions = {
            "setup": self._setup_account,
            "status": self._check_status,
            "list": self._list_emails,
            "ls": self._list_emails,
            "inbox": self._list_emails,
            "read": self._read_email,
            "show": self._read_email,
            "send": self._send_email,
            "compose": self._compose_email,
            "reply": self._reply_email,
            "forward": self._forward_email,
            "search": self._search_emails,
            "labels": self._list_labels,
            "folders": self._list_labels,
            "sync": self._sync_emails,
            "delete": self._delete_email,
            "draft": self._save_draft,
            "mark": self._mark_email,
            "attachments": self._list_attachments,
            "help": self._show_help,
        }
        
        if action is None:
            return self._show_help()
        
        if action not in actions:
            return {"error": f"Unknown action: {action}", "available": list(actions.keys())}
        
        return actions[action](**kwargs)
    
    def _show_help(self) -> dict:
        """Show email hook help."""
        return {
            "help": """
╔════════════════════════════════════════════════════════════════════════════╗
║                         EMAIL HOOK HELP                                ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  SETUP:                                                                 ║
║    /email setup provider=gmail                                           ║
║    /email setup provider=outlook                                         ║
║    /email setup provider=yahoo                                           ║
║                                                                            ║
║  READ EMAILS:                                                           ║
║    /email list              - List recent emails (inbox)                  ║
║    /email list folder=INBOX - List specific folder                       ║
║    /email list limit=20     - List with custom limit                    ║
║    /email read id=<number>   - Read specific email                       ║
║                                                                            ║
║  SEND EMAILS:                                                           ║
║    /email send to=<addr> subject=<sub> body=<msg>                       ║
║    /email compose            - Interactive compose                       ║
║    /email reply id=<num> body=<msg> - Reply to email                   ║
║    /email forward id=<num> to=<addr> - Forward email                    ║
║                                                                            ║
║  SEARCH:                                                                ║
║    /email search query="from:boss subject:report"                       ║
║    /email search query="has:attachment"                                ║
║                                                                            ║
║  MANAGE:                                                                ║
║    /email labels             - List all folders                        ║
║    /email sync               - Sync emails from server                  ║
║    /email mark id=<num> read=true - Mark as read                        ║
║    /email delete id=<num>     - Delete email                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

CONFIGURATION (IMAP/SMTP):

1. Gmail:
   export EMAIL_USER=your@gmail.com
   export EMAIL_PASSWORD='xxxx xxxx xxxx xxxx'  (App Password)
   /email setup provider=gmail

2. Outlook:
   export EMAIL_USER=your@outlook.com
   export EMAIL_PASSWORD=your_password
   /email setup provider=outlook

Get Gmail App Password:
  1. myaccount.google.com → Security
  2. 2-Step Verification → ON
  3. App passwords → Generate
"""
        }
    
    def _setup_account(self, provider: str = None, **kwargs) -> dict:
        """Setup email account."""
        if not provider:
            if self.config:
                return {
                    "error": "Already configured",
                    "current": self.config.get("provider"),
                    "user": self.config.get("user"),
                    "message": "To reconfigure, use: /email setup provider=gmail"
                }
            return {
                "error": "Provider required",
                "providers": ["gmail", "outlook", "yahoo"],
                "example": '/email setup provider=gmail'
            }
        
        provider = provider.lower()
        
        user = os.environ.get("EMAIL_USER") or os.environ.get("GMAIL_USER") or os.environ.get("OUTLOOK_USER")
        password = os.environ.get("EMAIL_PASSWORD") or os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("OUTLOOK_PASSWORD")
        
        if not user or not password:
            return {
                "error": "Email credentials not set",
                "required_env": {
                    "EMAIL_USER": "your@email.com",
                    "EMAIL_PASSWORD": "your_password_or_app_password"
                },
                "instructions": """
Set environment variables first:

  export EMAIL_USER=your@gmail.com
  export EMAIL_PASSWORD='xxxx xxxx xxxx xxxx'
  
  Then run: /email setup provider=gmail
"""
            }
        
        configs = {
            "gmail": {
                "provider": "gmail",
                "user": user,
                "imap_host": "imap.gmail.com",
                "imap_port": 993,
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 465,
            },
            "outlook": {
                "provider": "outlook",
                "user": user,
                "imap_host": "outlook.office365.com",
                "imap_port": 993,
                "smtp_host": "smtp.office365.com",
                "smtp_port": 587,
            },
            "yahoo": {
                "provider": "yahoo",
                "user": user,
                "imap_host": "imap.mail.yahoo.com",
                "imap_port": 993,
                "smtp_host": "smtp.mail.yahoo.com",
                "smtp_port": 587,
            },
        }
        
        if provider not in configs:
            return {"error": f"Unknown provider: {provider}", "available": list(configs.keys())}
        
        self.config = configs[provider]
        self.config["password"] = password
        self._save_config()
        
        result = self._test_connection()
        if result.get("success"):
            return {
                "success": True,
                "message": f"Email configured: {user}",
                "provider": provider,
                "status": "ready"
            }
        else:
            return result
    
    def _test_connection(self) -> dict:
        """Test IMAP connection."""
        try:
            import imaplib
            
            mail = imaplib.IMAP4_SSL(
                self.config["imap_host"],
                self.config["imap_port"]
            )
            mail.login(self.config["user"], self.config["password"])
            mail.logout()
            
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_status(self, **kwargs) -> dict:
        """Check email connection status."""
        if not self.config:
            return {
                "configured": False,
                "message": "No email account configured",
                "suggestion": "Run /email setup provider=gmail"
            }
        
        result = self._test_connection()
        
        return {
            "configured": True,
            "provider": self.config.get("provider"),
            "user": self.config.get("user"),
            "status": "connected" if result.get("success") else "error",
            "last_error": result.get("error"),
            "last_sync": self.cache.get("last_sync")
        }
    
    def _connect_imap(self):
        """Connect to IMAP server."""
        import imaplib
        return imaplib.IMAP4_SSL(
            self.config["imap_host"],
            self.config["imap_port"]
        )
    
    def _connect_smtp(self):
        """Connect to SMTP server."""
        import smtplib
        
        if self.config.get("provider") == "gmail":
            return smtplib.SMTP_SSL(self.config["smtp_host"], self.config["smtp_port"])
        else:
            server = smtplib.SMTP(self.config["smtp_host"], self.config["smtp_port"])
            server.starttls()
            return server
    
    def _list_emails(self, folder: str = "INBOX", limit: int = 20, **kwargs) -> dict:
        """List recent emails."""
        if not self.config:
            return {"error": "Email not configured. Run /email setup first."}
        
        try:
            import imaplib
            import email
            from email.header import decode_header
            
            mail = self._connect_imap()
            mail.login(self.config["user"], self.config["password"])
            mail.select(folder)
            
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            
            if not email_ids:
                mail.logout()
                return {"folder": folder, "emails": [], "count": 0}
            
            recent_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            emails = []
            
            for eid in reversed(recent_ids):
                try:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = self._decode_header(msg.get("Subject", "(no subject)"))
                    sender = self._decode_header(msg.get("From", ""))
                    date = msg.get("Date", "")
                    
                    emails.append({
                        "id": eid.decode(),
                        "subject": subject,
                        "from": sender,
                        "date": self._format_date(date),
                        "folder": folder,
                        "has_attachments": self._has_attachments(msg)
                    })
                except Exception:
                    continue
            
            mail.logout()
            
            self.cache["emails"] = emails[:50]
            self.cache["last_sync"] = datetime.now().isoformat()
            self._save_cache()
            
            return {
                "folder": folder,
                "emails": emails,
                "count": len(emails),
                "total_in_folder": len(email_ids)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _read_email(self, email_id: str = None, **kwargs) -> dict:
        """Read specific email."""
        if not email_id:
            return {"error": "Email ID required", "usage": "/email read id=<number>"}
        
        if not self.config:
            return {"error": "Email not configured"}
        
        try:
            import imaplib
            import email
            from email.header import decode_header
            
            mail = self._connect_imap()
            mail.login(self.config["user"], self.config["password"])
            mail.select("INBOX")
            
            status, msg_data = mail.fetch(email_id.encode(), "(RFC822)")
            if status != "OK":
                mail.logout()
                return {"error": f"Could not fetch email {email_id}"}
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = self._decode_header(msg.get("Subject", ""))
            sender = self._decode_header(msg.get("From", ""))
            to = self._decode_header(msg.get("To", ""))
            cc = self._decode_header(msg.get("Cc", ""))
            date = msg.get("Date", "")
            
            body = self._get_email_body(msg)
            attachments = self._get_attachments(msg)
            
            mail.logout()
            
            return {
                "id": email_id,
                "subject": subject,
                "from": sender,
                "to": to,
                "cc": cc,
                "date": date,
                "body": body,
                "html": msg.is_multipart() and any(p.get_content_type() == "text/html" for p in msg.walk()),
                "attachments": attachments,
                "headers": dict(msg.items())
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _send_email(self, to: str = None, subject: str = None, body: str = None, 
                   cc: str = None, bcc: str = None, **kwargs) -> dict:
        """Send email."""
        if not all([to, subject, body]):
            missing = []
            if not to: missing.append("to")
            if not subject: missing.append("subject")
            if not body: missing.append("body")
            return {
                "error": f"Missing required parameters: {', '.join(missing)}",
                "usage": '/email send to="user@example.com" subject="Hello" body="Message"'
            }
        
        if not self.config:
            return {"error": "Email not configured"}
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import smtplib
            
            msg = MIMEMultipart()
            msg['From'] = self.config["user"]
            msg['To'] = to
            if cc:
                msg['Cc'] = cc
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            msg.attach(MIMEText(body, 'plain'))
            
            recipients = [to]
            if cc:
                recipients.extend([e.strip() for e in cc.split(",")])
            if bcc:
                recipients.extend([e.strip() for e in bcc.split(",")])
            
            server = self._connect_smtp()
            server.login(self.config["user"], self.config["password"])
            server.send_message(msg, self.config["user"], recipients)
            server.quit()
            
            return {
                "success": True,
                "message": "Email sent successfully",
                "to": to,
                "subject": subject
            }
            
        except Exception as e:
            return {"error": f"Failed to send email: {str(e)}"}
    
    def _compose_email(self, **kwargs) -> dict:
        """Interactive compose help."""
        return {
            "message": "Use the send command with parameters:",
            "usage": """
/email send to="recipient@example.com" subject="Subject" body="Your message"

Or reply/forward existing emails:
/email reply id=<num> body="Your reply"
/email forward id=<num> to="someone@example.com"
"""
        }
    
    def _reply_email(self, email_id: str = None, body: str = None, **kwargs) -> dict:
        """Reply to an email."""
        if not email_id or not body:
            return {"error": "Email ID and body required", "usage": "/email reply id=<num> body=<message>"}
        
        original = self._read_email(email_id)
        if "error" in original:
            return original
        
        to = original.get("from", "").split("<")[-1].split(">")[0] if "<" in original.get("from", "") else original.get("from", "")
        subject = original.get("subject", "")
        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"
        
        reply_header = f"\n\n--- Original message ---\n{original.get('from', '')}\n{original.get('date', '')}\n\n"
        full_body = body + reply_header + original.get("body", "")[:500]
        
        return self._send_email(to=to, subject=subject, body=full_body)
    
    def _forward_email(self, email_id: str = None, to: str = None, body: str = None, **kwargs) -> dict:
        """Forward an email."""
        if not email_id or not to:
            return {"error": "Email ID and recipient required", "usage": "/email forward id=<num> to=<addr>"}
        
        original = self._read_email(email_id)
        if "error" in original:
            return original
        
        subject = original.get("subject", "")
        if not subject.startswith("Fwd:"):
            subject = f"Fwd: {subject}"
        
        forward_header = f"""
---------- Forwarded message ----------
From: {original.get('from', '')}
Date: {original.get('date', '')}
Subject: {original.get('subject', '')}
To: {original.get('to', '')}
-----------------------------------------

"""
        full_body = (body or "") + forward_header + original.get("body", "")
        
        return self._send_email(to=to, subject=subject, body=full_body)
    
    def _search_emails(self, query: str = None, folder: str = "INBOX", limit: int = 20, **kwargs) -> dict:
        """Search emails."""
        if not query:
            return {"error": "Query required", "usage": '/email search query="from:boss"'}
        
        if not self.config:
            return {"error": "Email not configured"}
        
        try:
            import imaplib
            import email
            
            mail = self._connect_imap()
            mail.login(self.config["user"], self.config["password"])
            mail.select(folder)
            
            search_criteria = self._build_search_query(query)
            status, messages = mail.search(None, search_criteria)
            email_ids = messages[0].split() if messages[0] else []
            
            results = []
            for eid in email_ids[:limit]:
                try:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    if status == "OK":
                        msg = email.message_from_bytes(msg_data[0][1])
                        results.append({
                            "id": eid.decode(),
                            "subject": self._decode_header(msg.get("Subject", "(no subject)")),
                            "from": self._decode_header(msg.get("From", "")),
                            "date": self._format_date(msg.get("Date", "")),
                            "snippet": self._get_email_body(msg)[:100]
                        })
                except:
                    continue
            
            mail.logout()
            
            return {
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _build_search_query(self, query: str) -> str:
        """Build IMAP search query from natural language."""
        query = query.lower().strip()
        
        if "from:" in query:
            match = re.search(r'from:(\S+)', query)
            if match:
                return f'FROM "{match.group(1)}"'
        
        if "subject:" in query:
            match = re.search(r'subject:(\S+)', query)
            if match:
                return f'SUBJECT "{match.group(1)}"'
        
        if "to:" in query:
            match = re.search(r'to:(\S+)', query)
            if match:
                return f'TO "{match.group(1)}"'
        
        if "has:attachment" in query or "attachment" in query:
            return 'UNSEEN'
        
        if "unread" in query:
            return 'UNSEEN'
        
        if "flagged" in query or "starred" in query:
            return 'FLAGGED'
        
        return f'ALL'
    
    def _list_labels(self, **kwargs) -> dict:
        """List all folders/labels."""
        if not self.config:
            return {"error": "Email not configured"}
        
        try:
            import imaplib
            
            mail = self._connect_imap()
            mail.login(self.config["user"], self.config["password"])
            
            status, folders = mail.list()
            
            labels = []
            for folder in folders:
                if isinstance(folder, bytes):
                    folder = folder.decode()
                name = folder.split('"."')[-1].strip('"') if '".' in folder else folder.split()[-1]
                if name:
                    labels.append({"name": name, "raw": folder.decode() if isinstance(folder, bytes) else folder})
            
            mail.logout()
            
            return {
                "labels": labels,
                "count": len(labels)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _sync_emails(self, folder: str = "INBOX", **kwargs) -> dict:
        """Sync emails from server."""
        return self._list_emails(folder=folder, limit=50)
    
    def _delete_email(self, email_id: str = None, **kwargs) -> dict:
        """Delete email."""
        if not email_id:
            return {"error": "Email ID required", "usage": "/email delete id=<number>"}
        
        if not self.config:
            return {"error": "Email not configured"}
        
        try:
            import imaplib
            
            mail = self._connect_imap()
            mail.login(self.config["user"], self.config["password"])
            mail.select("INBOX")
            
            mail.store(email_id.encode(), '+FLAGS', '\\Deleted')
            mail.expunge()
            mail.logout()
            
            return {"success": True, "message": f"Email {email_id} deleted"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _save_draft(self, to: str = None, subject: str = None, body: str = None, **kwargs) -> dict:
        """Save email as draft."""
        if not all([to, subject, body]):
            return {"error": "to, subject, and body required for draft"}
        
        drafts_file = self.storage_dir / "drafts.json"
        try:
            drafts = json.loads(drafts_file.read_text()) if drafts_file.exists() else []
        except:
            drafts = []
        
        draft = {
            "id": len(drafts) + 1,
            "to": to,
            "subject": subject,
            "body": body,
            "created": datetime.now().isoformat()
        }
        
        drafts.append(draft)
        drafts_file.write_text(json.dumps(drafts, indent=2))
        
        return {"success": True, "message": "Draft saved", "draft_id": draft["id"]}
    
    def _mark_email(self, email_id: str = None, read: bool = None, flagged: bool = None, **kwargs) -> dict:
        """Mark email as read/unread/flagged."""
        if not email_id:
            return {"error": "Email ID required"}
        
        if not self.config:
            return {"error": "Email not configured"}
        
        try:
            import imaplib
            
            mail = self._connect_imap()
            mail.login(self.config["user"], self.config["password"])
            mail.select("INBOX")
            
            flags = []
            if read is not None:
                flags.append("\\Seen" if read else "\\Seen")
            if flagged is not None:
                flags.append("\\Flagged" if flagged else "\\Flagged")
            
            if flags:
                flag_action = '+FLAGS' if read or flagged else '-FLAGS'
                mail.store(email_id.encode(), flag_action, ' '.join(flags))
            
            mail.logout()
            
            return {"success": True, "message": f"Email {email_id} marked"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _list_attachments(self, email_id: str = None, **kwargs) -> dict:
        """List attachments of an email."""
        if not email_id:
            return {"error": "Email ID required"}
        
        email = self._read_email(email_id)
        if "error" in email:
            return email
        
        return {
            "email_id": email_id,
            "subject": email.get("subject"),
            "attachments": email.get("attachments", [])
        }
    
    # ==================== Helpers ====================
    
    def _decode_header(self, header) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        decoded_parts = []
        try:
            parts = email.header.decode_header(header)
            for content, charset in parts:
                if isinstance(content, bytes):
                    charset = charset or 'utf-8'
                    try:
                        decoded_parts.append(content.decode(charset, errors='replace'))
                    except:
                        decoded_parts.append(content.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(content)
        except:
            return str(header)
        
        return ''.join(decoded_parts)
    
    def _get_email_body(self, msg) -> str:
        """Extract email body."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='replace')
                        break
                    except:
                        pass
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except:
                body = str(msg.get_payload())
        
        return body
    
    def _has_attachments(self, msg) -> bool:
        """Check if email has attachments."""
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                return True
        return False
    
    def _get_attachments(self, msg) -> List[Dict]:
        """Get list of attachments."""
        attachments = []
        
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    if isinstance(filename, bytes):
                        filename = self._decode_header(filename)
                    attachments.append({
                        "filename": filename,
                        "content_type": part.get_content_type(),
                        "size": len(part.get_payload(decode=True) or b'')
                    })
        
        return attachments
    
    def _format_date(self, date_str: str) -> str:
        """Format email date."""
        if not date_str:
            return ""
        
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            now = datetime.now()
            
            if dt.date() == now.date():
                return dt.strftime("%H:%M")
            elif dt.year == now.year:
                return dt.strftime("%b %d")
            else:
                return dt.strftime("%Y-%m-%d")
        except:
            return date_str[:16]


if __name__ == "__main__":
    hook = EmailHook()
    result = hook.run("help")
    print(result.get("help", str(result)))
