# Discord Bot Project

## Overview
This project is a feature-rich Discord bot, built with Python and the discord.py library, designed for continuous uptime on Replit. It offers a wide range of entertainment, utility, and information commands, emphasizing user-friendly interactions through rich embeds and robust error handling. The bot includes a comprehensive moderation system, server management tools, entertainment features, and advanced interactive components. A key ambition is to provide a complete Discord bot suite with over 150 slash commands, covering 100% of Discord API functionality, and advanced features like AI integration (ChatGPT and Gemini), a streamlined welcome system, and a sophisticated interactive timer system.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes (September 21, 2025)
✅ **COMPLETED:** Twitch game filtering system
- Implemented comprehensive game filtering for Twitch stream notifications to reduce spam
- Enhanced `/twitch add` command with optional `games` parameter for comma-separated game list  
- Updated notification logic with intelligent game matching (exact match + substring matching)
- Added filtered_games database column with safe migration for new installations
- Enhanced `/twitch list` command to display game filters with smart formatting
- Fixed critical notification bug preventing false positives from empty game names
- Added robust edge case handling and detailed logging for game filter operations
- **Current status:** Game filtering fully operational and production-ready

## Previous Changes (September 16, 2025)
✅ **COMPLETED:** Welcome & goodbye message customization
- Enhanced welcome messages with bold "Hey", member names, and waving emoji (👋)
- Added bold formatting to "Welcome to RIVALZ MLB THE SHOW" text
- Updated both Discord embeds and generated welcome images to include proper emoji display
- Created customizable goodbye settings system (goodbye_settings.json) matching welcome system
- Removed duplicate member name line under avatar in welcome images
- Removed "Rivalz Bot Welcome" branding text from welcome messages
- Bot loads welcome settings for 1 guild and goodbye settings for 1 guild on startup

✅ **COMPLETED:** Auto-restart system and role assignment
- Implemented automatic crash recovery system with up to 100 restart attempts
- Added progressive delay backoff (10s + 2s per restart, max 60s)
- Configured Reserved VM deployment for enhanced uptime
- Added automatic "Waiting List" role assignment for new members
- Corrected goodbye message system to show member info instead of server stats
- **Current status:** Bot runs in AUTO-RESTART MODE with robust crash recovery

## System Architecture
The bot is built with Python 3.x using the discord.py library and deployed on Replit with a Flask-based keep-alive mechanism. It follows a modular design with clear separation of concerns, comprising `main.py` for orchestration, `bot.py` for core bot logic, `commands.py` for command definitions, `utils.py` for shared utilities, and `keep_alive.py` for uptime maintenance.

**Core Components:**
- **Bot Core (`bot.py`):** Extends `discord.py`'s `commands.Bot` with enhanced intent configuration (message content and member intents), comprehensive event handlers (lifecycle, member join/leave with automated messages), status management, and automatic slash command syncing.
- **Command System (`commands.py`):** Supports both traditional text commands and modern slash commands, categorized into basic, fun, information, and moderation. It includes new features like a poll system with reaction voting and admin message management. All command outputs use rich embeds for consistent visual formatting.
- **Utility Layer (`utils.py`):** Provides flexible command prefixing, standardized embed factories for various message types, and human-readable time conversion utilities.
- **Keep-Alive System (`keep_alive.py`):** A Flask web server running in a background thread to provide HTTP endpoints, ensuring the Replit instance remains active.
- **Welcome System:** A streamlined welcome system that generates professional Discord-style welcome images with clean black theme aesthetic for new members joining the server.
- **Interactive Timer System:** Features a streamlined 4-button control layout, automatic user rotation with tagging, real-time progress bars, and dynamic embed updates. It supports up to 10 users in rotation and offers various timer command types suitable for games, meetings, and presentations.
- **Discord-Style Image Generation:** Advanced welcome image creation that mimics professional Discord designs, featuring specific layouts (800x400), high-quality circular avatars, dynamic text rendering, and PNG output optimization.
- **Message Editing System:** Comprehensive bot message management with commands to edit regular messages (`!editmsg`), edit embed messages (`!editembed`), and delete bot messages (`!delmsg`). All commands include proper permission checks and error handling.
- **Mass Notification System:** Admin-only commands for server-wide announcements with `!everyone` and `!here` commands, plus file sharing with mass notifications (`!sendfile_everyone`, `!sendfile_here`), including proper permission validation and error handling.
- **Twitch Game Filtering System:** Advanced notification filtering that allows users to specify specific games for stream alerts, reducing notification spam. Features intelligent game matching with exact and substring matching, empty game detection, database schema safety with automatic migrations, and comprehensive edge case handling. Supports both individual streamer filtering and server-wide notification management.

**Technical Implementations & System Design Choices:**
- **Deployment:** Utilizes a multi-service architecture where a Flask web server (port 5000) acts as the primary process for HTTP health checks, with the Discord bot running as a background thread.
- **UI/UX Decisions:** Emphasizes rich embeds and professional Discord-style image generation for welcome messages. Aesthetic details like clean black theme, centered layout, and minimalist design are prioritized for a polished user experience.
- **Data Flow:** Bot initialization loads environment variables, command processing triggers execution, responses are generated as rich embeds, and the Flask server maintains uptime via HTTP requests.

## External Dependencies
- `discord.py`: The primary library for Discord API interaction.
- `flask`: Used for the web server to maintain Replit's always-on functionality and provide health check endpoints.
- `asyncio`: Python's built-in library for asynchronous programming.
- `logging`: Python's built-in logging framework for application logs.
- `threading`: Python's built-in module for multi-threading support.
- **Discord API:** Authenticates via `DISCORD_TOKEN` environment variable, utilizes gateway intents for message content and guild access, and supports webhooks for external monitoring.
- **Environment Variables:** `DISCORD_TOKEN` is managed via Replit's secrets.
- **AI Integration:** Implements support for both ChatGPT and Gemini APIs, including image analysis capabilities.