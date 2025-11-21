import discord
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
        super().__init__(command_prefix='*', intents=intents)
        self.queues = {}  # Guild-specific queues
        self.current_song = {}  # Currently playing song per guild


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
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="*play"))


@bot.command(name="play")
async def play(ctx, *, query: str):
    """Play a song from YouTube or YouTube Music"""
    
    # Check if user is in a voice channel
    if not ctx.author.voice:
        await ctx.send("❌ You need to be in a voice channel to use this command!")
        return
    
    # Connect to voice channel if not already connected
    voice_channel = ctx.author.voice.channel
    voice_client = ctx.guild.voice_client
    
    if not voice_client:
        try:
            voice_client = await voice_channel.connect()
        except Exception as e:
            await ctx.send(f"❌ Could not connect to voice channel: {str(e)}")
            return
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)
    
    # Initialize queue for this guild if it doesn't exist
    if ctx.guild.id not in bot.queues:
        bot.queues[ctx.guild.id] = deque()
    
    # Add to queue
    bot.queues[ctx.guild.id].append((query, ctx.channel))
    
    # If nothing is playing, start playing
    if not voice_client.is_playing():
        await ctx.send("🔍 Searching and loading...")
        await play_next(ctx.guild.id)
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
            embed.add_field(name="Position in queue", value=str(len(bot.queues[ctx.guild.id])))
            await ctx.send(embed=embed)
        except:
            await ctx.send(f"✅ Added to queue (Position: {len(bot.queues[ctx.guild.id])})")


@bot.command(name="skip")
async def skip(ctx):
    """Skip the currently playing song"""
    
    voice_client = ctx.guild.voice_client
    
    if not voice_client or not voice_client.is_playing():
        await ctx.send("❌ Nothing is playing right now!")
        return
    
    voice_client.stop()
    await ctx.send("⏭️ Skipped!")


@bot.command(name="stop")
async def stop(ctx):
    """Stop the music and clear the queue"""
    
    voice_client = ctx.guild.voice_client
    
    if not voice_client:
        await ctx.send("❌ I'm not in a voice channel!")
        return
    
    # Clear the queue
    if ctx.guild.id in bot.queues:
        bot.queues[ctx.guild.id].clear()
    
    # Stop playing
    if voice_client.is_playing():
        voice_client.stop()
    
    await ctx.send("⏹️ Stopped playing and cleared the queue!")


@bot.command(name="pause")
async def pause(ctx):
    """Pause the currently playing song"""
    
    voice_client = ctx.guild.voice_client
    
    if not voice_client or not voice_client.is_playing():
        await ctx.send("❌ Nothing is playing right now!")
        return
    
    voice_client.pause()
    await ctx.send("⏸️ Paused!")


@bot.command(name="resume")
async def resume(ctx):
    """Resume the paused song"""
    
    voice_client = ctx.guild.voice_client
    
    if not voice_client or not voice_client.is_paused():
        await ctx.send("❌ Nothing is paused right now!")
        return
    
    voice_client.resume()
    await ctx.send("▶️ Resumed!")


@bot.command(name="queue")
async def queue(ctx):
    """Display the current queue"""
    
    if ctx.guild.id not in bot.queues or len(bot.queues[ctx.guild.id]) == 0:
        if ctx.guild.id in bot.current_song:
            current = bot.current_song[ctx.guild.id]
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{current.title}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("📭 The queue is empty!")
        return
    
    embed = discord.Embed(
        title="🎵 Music Queue",
        color=discord.Color.blue()
    )
    
    # Show currently playing
    if ctx.guild.id in bot.current_song:
        current = bot.current_song[ctx.guild.id]
        embed.add_field(name="Now Playing", value=f"**{current.title}**", inline=False)
    
    # Show queue
    queue_list = list(bot.queues[ctx.guild.id])
    if queue_list:
        queue_text = "\n".join([f"{i+1}. {url}" for i, (url, _) in enumerate(queue_list[:10])])
        if len(queue_list) > 10:
            queue_text += f"\n... and {len(queue_list) - 10} more"
        embed.add_field(name="Up Next", value=queue_text, inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="disconnect")
async def disconnect(ctx):
    """Disconnect from voice channel"""
    
    voice_client = ctx.guild.voice_client
    
    if not voice_client:
        await ctx.send("❌ I'm not in a voice channel!")
        return
    
    # Clear the queue
    if ctx.guild.id in bot.queues:
        bot.queues[ctx.guild.id].clear()
    
    await voice_client.disconnect()
    await ctx.send("👋 Disconnected from voice channel!")


@bot.command(name="nowplaying", aliases=["np"])
async def nowplaying(ctx):
    """Display the currently playing song"""
    
    if ctx.guild.id not in bot.current_song:
        await ctx.send("❌ Nothing is playing right now!")
        return
    
    current = bot.current_song[ctx.guild.id]
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
    
    await ctx.send(embed=embed)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your Discord bot token.")
        exit(1)
    
    bot.run(DISCORD_TOKEN)

