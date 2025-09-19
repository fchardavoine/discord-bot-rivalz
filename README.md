# Discord Bot

A feature-rich Discord bot built with Python and discord.py, designed to run on Replit with continuous uptime.

## Features

- 🎮 **Fun Commands**: Roll dice, flip coins, magic 8-ball
- 📊 **Information Commands**: Server info, user info, bot statistics
- 🛠️ **Utility Commands**: Clear messages, ping check
- 🎨 **Rich Embeds**: Beautiful formatted responses
- 🔒 **Permission System**: Role-based command access
- 📝 **Comprehensive Logging**: Detailed logs for debugging
- ⚡ **Error Handling**: Graceful error management
- 🚀 **Replit Ready**: Configured for Replit deployment

## Commands

### Basic Commands
- `!hello` - Greet the bot
- `!ping` - Check bot latency
- `!info` - Display bot information
- `!help` - Show all available commands

### Fun Commands
- `!roll [max]` - Roll a dice (default 1-6, or specify max)
- `!coinflip` - Flip a coin
- `!8ball <question>` - Ask the magic 8-ball

### Information Commands
- `!serverinfo` - Get server information
- `!userinfo [@user]` - Get user information

### Moderation Commands (Admin only)
- `!clear [amount]` - Clear messages (requires Manage Messages permission)

## Setup Instructions

### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Copy the bot token (keep this secret!)
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (optional)

### 2. Set Up on Replit

1. Fork or import this repository to Replit
2. In your Replit project, go to the "Secrets" tab (lock icon in sidebar)
3. Add a new secret:
   - Key: `DISCORD_TOKEN`
   - Value: Your bot token from step 1

### 3. Invite Bot to Your Server

1. In the Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select scopes: `bot` and `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Read Message History
   - Manage Messages (for clear command)
   - Use Slash Commands
   - Add Reactions
   - Embed Links
4. Copy the generated URL and open it to invite your bot

### 4. Run the Bot

1. Click the "Run" button in Replit
2. Your bot should come online in Discord
3. Test with `!hello` in a server where the bot is present

## Configuration

### Environment Variables (Replit Secrets)

- `DISCORD_TOKEN` - Your Discord bot token (required)
- `BOT_PREFIX` - Custom command prefix (optional, defaults to !, ?, .)
- `BOT_OWNER_ID` - Your Discord user ID for owner-only commands (optional)
- `DEBUG` - Enable debug logging (optional)

### Customization

You can easily customize the bot by modifying:

- **Commands**: Edit `commands.py` to add/modify commands
- **Prefixes**: Modify `get_prefix()` in `utils.py`
- **Permissions**: Adjust command decorators in `commands.py`
- **Responses**: Customize embed colors and messages

## File Structure

