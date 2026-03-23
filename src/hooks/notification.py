"""
Notification Hook - Send notifications via various channels

Supports:
- Terminal notifications (macOS, Linux, Windows)
- Webhook notifications
- Email notifications
- Slack notifications
"""

import os
import json
import subprocess
import webbrowser
from typing import Optional
try:
    import httpx
except ImportError:
    import subprocess as sp
    sp.check_call([sp.sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx


class NotificationHook:
    """Send notifications via various channels."""
    
    def run(self, message: str, channel: str = "terminal", title: str = "OpenCode Chat", **kwargs) -> dict:
        """
        Send a notification.
        
        Args:
            message: Notification message
            channel: "terminal", "macos", "webhook", "slack", "email", "open_url"
            title: Notification title
            **kwargs: Channel-specific options
        
        Returns:
            dict with result
        """
        if channel == "terminal":
            return self._notify_terminal(message, title)
        elif channel == "macos":
            return self._notify_macos(message, title)
        elif channel == "webhook":
            return self._notify_webhook(message, title, **kwargs)
        elif channel == "slack":
            return self._notify_slack(message, title, **kwargs)
        elif channel == "email":
            return self._notify_email(message, title, **kwargs)
        elif channel == "open_url":
            return self._open_url(message, **kwargs)
        else:
            return {"error": f"Unknown channel: {channel}"}
    
    def _notify_terminal(self, message: str, title: str) -> dict:
        """Print notification to terminal."""
        print(f"\n{'='*60}")
        print(f"📢 {title}")
        print(f"{'='*60}")
        print(f"   {message}")
        print(f"{'='*60}\n")
        return {"success": True, "channel": "terminal"}
    
    def _notify_macos(self, message: str, title: str) -> dict:
        """Send macOS notification using osascript."""
        script = f'display notification "{message}" with title "{title}"'
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return {"success": True, "channel": "macos"}
        except Exception as e:
            return {"success": False, "error": str(e), "channel": "macos"}
    
    def _notify_webhook(self, message: str, title: str, url: str = None, **kwargs) -> dict:
        """Send webhook notification."""
        webhook_url = url or os.environ.get("WEBHOOK_URL")
        
        if not webhook_url:
            return {"error": "WEBHOOK_URL not set"}
        
        payload = {
            "text": f"**{title}**\n{message}",
            "username": "OpenCode Chat",
            **kwargs
        }
        
        try:
            response = httpx.post(webhook_url, json=payload, timeout=10)
            return {
                "success": response.status_code == 200,
                "channel": "webhook",
                "status_code": response.status_code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _notify_slack(self, message: str, title: str, webhook_url: str = None, channel: str = None, **kwargs) -> dict:
        """Send Slack notification."""
        slack_webhook = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        
        if not slack_webhook:
            return {"error": "SLACK_WEBHOOK_URL not set"}
        
        payload = {
            "text": f"*{title}*\n{message}"
        }
        
        if channel:
            payload["channel"] = channel
        
        try:
            response = httpx.post(slack_webhook, json=payload, timeout=10)
            return {
                "success": response.status_code == 200,
                "channel": "slack"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _notify_email(self, message: str, title: str, to: str = None, **kwargs) -> dict:
        """Send email notification (requires SMTP config)."""
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_port = os.environ.get("SMTP_PORT", "587")
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        
        if not all([smtp_host, smtp_user, smtp_pass]):
            return {"error": "SMTP configuration incomplete (SMTP_HOST, SMTP_USER, SMTP_PASS required)"}
        
        to_email = to or os.environ.get("NOTIFICATION_EMAIL")
        
        if not to_email:
            return {"error": "No recipient email specified"}
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = title
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            return {"success": True, "channel": "email"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _open_url(self, url: str, **kwargs) -> dict:
        """Open URL in browser."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        try:
            webbrowser.open(url)
            return {"success": True, "channel": "open_url", "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def batch_notify(self, notifications: list) -> dict:
        """Send multiple notifications."""
        results = []
        for notif in notifications:
            result = self.run(**notif)
            results.append(result)
        
        success_count = sum(1 for r in results if r.get("success", False))
        
        return {
            "total": len(notifications),
            "success": success_count,
            "failed": len(notifications) - success_count,
            "results": results
        }
    
    def help(self) -> str:
        return """
Notification Hook
=================
Usage: /hook notification message="Hello!" channel="terminal"

Channels:
- terminal: Print to console (default)
- macos: macOS notification center
- webhook: Generic webhook (requires WEBHOOK_URL)
- slack: Slack (requires SLACK_WEBHOOK_URL)
- email: Email (requires SMTP_* vars)
- open_url: Open URL in browser

Examples:
  /hook notification message="Build complete!" channel="macos"
  /hook notification message="New task" channel="slack" channel_name="#devops"
  /hook notification url="https://github.com" channel="open_url"
"""


if __name__ == "__main__":
    hook = NotificationHook()
    
    result = hook.run("Test notification", channel="terminal")
    print(json.dumps(result, indent=2))
