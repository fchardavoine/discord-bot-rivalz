# Rivalz — Replit 24/7 (with Deferred Slash + Error Handler)

## Setup
1) Replit → Tools → Secrets: set `DISCORD_TOKEN` (and any others you use).
2) Shell:
```
pip install -r requirements.txt
```
3) Run. Open webview → `/health` should return healthy JSON.

## Test Commands
- Prefix: `!ping`
- Slash: `/hello` (we defer immediately to avoid timeouts).

If prefix commands fail: enable **Message Content Intent** in Discord Developer Portal and ensure
`intents.message_content = True` in code. If slash doesn't appear: invite bot with `applications.commands` scope.

Logs will show: `✅ Slash commands synced: N` when sync succeeds.
