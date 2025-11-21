# Discord Music Bot 🎵

A feature-rich Discord music bot that can play music from YouTube, YouTube Music, or search queries. Built with Python, discord.py, and yt-dlp.

## Features

- 🎵 Play music from YouTube and YouTube Music links
- 🔍 Search and play music using keywords
- 📝 Queue system for multiple songs
- ⏯️ Playback controls (play, pause, resume, skip, stop)
- 🎼 Display now playing information with thumbnails
- 📋 View the current queue
- 🎚️ Auto-disconnect when done

## Commands

All commands use the `*` prefix:

- `*play <query>` - Play a song from YouTube URL or search query
- `*pause` - Pause the current song
- `*resume` - Resume the paused song
- `*skip` - Skip to the next song in queue
- `*stop` - Stop playing and clear the queue
- `*queue` - Display the current queue
- `*nowplaying` (or `*np`) - Show currently playing song
- `*disconnect` - Disconnect bot from voice channel

## Prerequisites

- Python 3.11 or higher
- FFmpeg installed on your system
- A Discord Bot Token
- Docker (optional, for containerized deployment)

## Setup Instructions

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (optional)
5. Copy your bot token (you'll need this later)
6. Go to "OAuth2" > "URL Generator"
7. Select scopes: `bot`
8. Select bot permissions:
   - Connect
   - Speak
   - Use Voice Activity
   - Send Messages
   - Embed Links
   - Read Message History
9. Copy the generated URL and open it in your browser to invite the bot to your server

### 2. Installation Methods

#### Method A: Local Installation (Without Docker)

1. **Clone or download this repository**

2. **Install FFmpeg and Opus** (if not already installed):
   
   **macOS:**
   ```bash
   brew install ffmpeg opus
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install ffmpeg libopus0 libopus-dev
   ```
   
   **Windows:**
   - Download FFmpeg from [FFmpeg official website](https://ffmpeg.org/download.html)
   - Add FFmpeg to your system PATH
   - Install Opus library

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root:
   ```bash
   cp .env.example .env
   ```

5. **Edit the `.env` file** and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_actual_bot_token_here
   ```

6. **Run the bot:**
   ```bash
   python bot.py
   ```

#### Method B: Docker Installation (Recommended for Production)

**Yes, this bot can be fully Dockerized!** 🐳

1. **Make sure Docker and Docker Compose are installed:**
   - [Install Docker](https://docs.docker.com/get-docker/)
   - [Install Docker Compose](https://docs.docker.com/compose/install/)

2. **Create a `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit the `.env` file** and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_actual_bot_token_here
   ```

4. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f
   ```

6. **Stop the bot:**
   ```bash
   docker-compose down
   ```

7. **Rebuild after code changes:**
   ```bash
   docker-compose up -d --build
   ```

## Usage Examples

1. **Play a YouTube video:**
   ```
   *play https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. **Play from YouTube Music:**
   ```
   *play https://music.youtube.com/watch?v=dQw4w9WgXcQ
   ```

3. **Search and play:**
   ```
   *play never gonna give you up
   ```

4. **Control playback:**
   ```
   *pause
   *resume
   *skip
   *stop
   ```

5. **Check what's playing:**
   ```
   *nowplaying
   *queue
   ```

## Troubleshooting

### Bot doesn't respond to commands
- Make sure the bot has been invited with the correct permissions
- Ensure "Message Content Intent" is enabled in the Discord Developer Portal
- Make sure you're using the correct prefix: `*play` not `/play`

### "FFmpeg not found" error
- Make sure FFmpeg is installed and in your system PATH
- For Docker: The Dockerfile already includes FFmpeg installation

### "OpusNotLoaded" error
- Make sure Opus library is installed (`brew install opus` on macOS)
- The bot will automatically try to load Opus from common locations
- For Docker: The Dockerfile already includes Opus installation

### "Could not connect to voice channel" error
- Make sure the bot has "Connect" and "Speak" permissions
- Check if the voice channel has user limits

### Audio quality issues
- This is usually due to network conditions or YouTube throttling
- The bot uses the best available audio quality from yt-dlp

### Docker container keeps restarting
- Check logs with `docker-compose logs -f`
- Verify your `.env` file has the correct token
- Make sure the token doesn't have extra spaces or quotes

## Project Structure

```
music-bot-discord/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment variables
├── .env               # Your actual environment variables (create this)
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── .gitignore        # Git ignore file
└── README.md         # This file
```

## Technical Details

- **Language:** Python 3.11+
- **Discord Library:** discord.py 2.3.2+
- **Audio Extraction:** yt-dlp
- **Audio Playback:** FFmpeg
- **Voice Support:** PyNaCl

## Security Notes

- Never commit your `.env` file or expose your bot token
- The `.gitignore` file is configured to prevent accidental token exposure
- Use environment variables for sensitive data

## Docker Benefits

✅ **Consistent environment** - Works the same everywhere  
✅ **Easy deployment** - One command to start  
✅ **Isolated dependencies** - No conflicts with system packages  
✅ **Auto-restart** - Automatically restarts if it crashes  
✅ **Easy updates** - Just rebuild and restart  

## License

This project is open source and available for personal and educational use.

## Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Make sure all prerequisites are installed
3. Verify your Discord bot token is correct
4. Check the bot has proper permissions in your Discord server

## Contributing

Feel free to fork this project and submit pull requests for improvements!

---

**Enjoy your music bot! 🎵🎉**

