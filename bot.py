import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
import os
from dotenv import load_dotenv
from collections import deque

# Load environment variables
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}


class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix='!', intents=intents)
        self.queues = {}  # Guild-specific queues
        self.current_song = {}  # Currently playing song per guild
    
    async def setup_hook(self):
        """Sync slash commands with Discord"""
        await self.tree.sync()
        print("Slash commands synced!")


bot = MusicBot()


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(YDL_OPTIONS).extract_info(url, download=not stream))
        except Exception as e:
            raise Exception(f"Error extracting info: {str(e)}")

        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else yt_dlp.YoutubeDL(YDL_OPTIONS).prepare_filename(data)
        
        try:
            return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)
        except Exception as e:
            raise Exception(f"Error creating audio source: {str(e)}")


async def play_next(guild_id: int):
    """Play the next song in the queue"""
    if guild_id not in bot.queues or len(bot.queues[guild_id]) == 0:
        bot.current_song.pop(guild_id, None)
        return

    guild = bot.get_guild(guild_id)
    if not guild:
        return

    voice_client = guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return

    url, channel = bot.queues[guild_id].popleft()
    
    try:
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        bot.current_song[guild_id] = player
        
        def after_playing(error):
            if error:
                print(f"Player error: {error}")
                asyncio.run_coroutine_threadsafe(channel.send(f"❌ Playback error: {error}"), bot.loop)
            asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop)
        
        voice_client.play(player, after=after_playing)
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{player.title}**",
            color=discord.Color.green()
        )
        if player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)
        if player.duration:
            minutes, seconds = divmod(player.duration, 60)
            embed.add_field(name="Duration", value=f"{int(minutes)}:{int(seconds):02d}")
        
        await channel.send(embed=embed)
        
    except Exception as e:
        print(f"Error in play_next: {str(e)}")
        import traceback
        traceback.print_exc()
        await channel.send(f"❌ Error playing song: {str(e)}")
        await play_next(guild_id)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="music"))


@bot.tree.command(name="play", description="Play a song from YouTube or YouTube Music")
@app_commands.describe(query="YouTube URL, YouTube Music URL, or search terms")
async def play(interaction: discord.Interaction, query: str):
    """Play a song from YouTube or YouTube Music"""
    
    # Check if user is in a voice channel
    if not interaction.user.voice:
        await interaction.response.send_message("❌ You need to be in a voice channel to use this command!")
        return
    
    # Defer the response since this might take a while
    await interaction.response.defer()
    
    # Connect to voice channel if not already connected
    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    
    if not voice_client:
        try:
            voice_client = await voice_channel.connect()
        except Exception as e:
            await interaction.followup.send(f"❌ Could not connect to voice channel: {str(e)}")
            return
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)
    
    # Initialize queue for this guild if it doesn't exist
    if interaction.guild.id not in bot.queues:
        bot.queues[interaction.guild.id] = deque()
    
    # Add to queue
    bot.queues[interaction.guild.id].append((query, interaction.channel))
    
    # If nothing is playing, start playing
    if not voice_client.is_playing():
        await interaction.followup.send("🔍 Searching and loading...")
        await play_next(interaction.guild.id)
    else:
        # Get song info for queue message
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(YDL_OPTIONS).extract_info(query, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            
            embed = discord.Embed(
                title="📝 Added to Queue",
                description=f"**{data.get('title', 'Unknown')}**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Position in queue", value=str(len(bot.queues[interaction.guild.id])))
            await interaction.followup.send(embed=embed)
        except:
            await interaction.followup.send(f"✅ Added to queue (Position: {len(bot.queues[interaction.guild.id])})")


@bot.tree.command(name="skip", description="Skip the currently playing song")
async def skip(interaction: discord.Interaction):
    """Skip the currently playing song"""
    
    voice_client = interaction.guild.voice_client
    
    if not voice_client or not voice_client.is_playing():
        await interaction.response.send_message("❌ Nothing is playing right now!")
        return
    
    voice_client.stop()
    await interaction.response.send_message("⏭️ Skipped!")


@bot.tree.command(name="stop", description="Stop the music and clear the queue")
async def stop(interaction: discord.Interaction):
    """Stop the music and clear the queue"""
    
    voice_client = interaction.guild.voice_client
    
    if not voice_client:
        await interaction.response.send_message("❌ I'm not in a voice channel!")
        return
    
    # Clear the queue
    if interaction.guild.id in bot.queues:
        bot.queues[interaction.guild.id].clear()
    
    # Stop playing
    if voice_client.is_playing():
        voice_client.stop()
    
    await interaction.response.send_message("⏹️ Stopped playing and cleared the queue!")


@bot.tree.command(name="pause", description="Pause the currently playing song")
async def pause(interaction: discord.Interaction):
    """Pause the currently playing song"""
    
    voice_client = interaction.guild.voice_client
    
    if not voice_client or not voice_client.is_playing():
        await interaction.response.send_message("❌ Nothing is playing right now!")
        return
    
    voice_client.pause()
    await interaction.response.send_message("⏸️ Paused!")


@bot.tree.command(name="resume", description="Resume the paused song")
async def resume(interaction: discord.Interaction):
    """Resume the paused song"""
    
    voice_client = interaction.guild.voice_client
    
    if not voice_client or not voice_client.is_paused():
        await interaction.response.send_message("❌ Nothing is paused right now!")
        return
    
    voice_client.resume()
    await interaction.response.send_message("▶️ Resumed!")


@bot.tree.command(name="queue", description="Display the current queue")
async def queue(interaction: discord.Interaction):
    """Display the current queue"""
    
    if interaction.guild.id not in bot.queues or len(bot.queues[interaction.guild.id]) == 0:
        if interaction.guild.id in bot.current_song:
            current = bot.current_song[interaction.guild.id]
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{current.title}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("📭 The queue is empty!")
        return
    
    embed = discord.Embed(
        title="🎵 Music Queue",
        color=discord.Color.blue()
    )
    
    # Show currently playing
    if interaction.guild.id in bot.current_song:
        current = bot.current_song[interaction.guild.id]
        embed.add_field(name="Now Playing", value=f"**{current.title}**", inline=False)
    
    # Show queue
    queue_list = list(bot.queues[interaction.guild.id])
    if queue_list:
        queue_text = "\n".join([f"{i+1}. {url}" for i, (url, _) in enumerate(queue_list[:10])])
        if len(queue_list) > 10:
            queue_text += f"\n... and {len(queue_list) - 10} more"
        embed.add_field(name="Up Next", value=queue_text, inline=False)
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="disconnect", description="Disconnect from voice channel")
async def disconnect(interaction: discord.Interaction):
    """Disconnect from voice channel"""
    
    voice_client = interaction.guild.voice_client
    
    if not voice_client:
        await interaction.response.send_message("❌ I'm not in a voice channel!")
        return
    
    # Clear the queue
    if interaction.guild.id in bot.queues:
        bot.queues[interaction.guild.id].clear()
    
    await voice_client.disconnect()
    await interaction.response.send_message("👋 Disconnected from voice channel!")


@bot.tree.command(name="nowplaying", description="Display the currently playing song")
async def nowplaying(interaction: discord.Interaction):
    """Display the currently playing song"""
    
    if interaction.guild.id not in bot.current_song:
        await interaction.response.send_message("❌ Nothing is playing right now!")
        return
    
    current = bot.current_song[interaction.guild.id]
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**{current.title}**",
        color=discord.Color.green()
    )
    
    if current.thumbnail:
        embed.set_thumbnail(url=current.thumbnail)
    
    if current.duration:
        minutes, seconds = divmod(current.duration, 60)
        embed.add_field(name="Duration", value=f"{int(minutes)}:{int(seconds):02d}")
    
    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your Discord bot token.")
        exit(1)
    
    bot.run(DISCORD_TOKEN)

