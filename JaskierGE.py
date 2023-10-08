from discord.ext import commands, tasks
import discord
from YTDLSource import YTDLSource
from table2ascii import table2ascii as t2a
import asyncio
import ctypes
import ctypes.util
import logging  # Import the logging module
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    filename='discord_bot.log',  # Log file name
    level=logging.ERROR,        # Log only error messages and above
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class JaskierGE(commands.Cog):
    queue = {}  # To store the song queue {("Queue No(int)" : "Title(str)")}
    current_id = 0  # Current index of song in the queue
    last_interaction_time = datetime.utcnow()  # Initialize with the current time (auto-updated upon message to bot)
    channel_id = ""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_inactivity.start()

    def guild_only(ctx):
        # Check if the command was invoked in a guild (server) channel
        return ctx.guild is not None

    @commands.command(name="join", help="Command to make the bot join the server which the user is connected to")
    async def join(self, ctx: commands.Context):
        try:
            channel = ctx.message.author.voice.channel
            self.channel_id = channel.id
            await channel.connect()
        except Exception as e:
            await ctx.send("You are not connected to a voice channel")
            logging.error(f'User is not connected to a voice channel: {e}')

    @commands.command(name="leave", help="Command to make the bot leave the server")
    @commands.check(guild_only)
    async def leave(self, ctx: commands.Context):
        try:
            channel = ctx.message.guild.voice_client
            if channel.is_connected():
                await channel.disconnect()
            else:
                await ctx.send("The bot is not connected to a voice channel.")
        except Exception as e:
            logging.error(f'An error occurred while leaving a voice channel: {e}')

    @commands.command(name="play", help="""Command to play a song or add a song to queue if song is already 
                                            playing\nUsage: /play (youtube-link/song-name)""")
    @commands.check(guild_only)
    async def play(self, ctx: commands.Context, *, url):
        try:
            ctypes.util.find_library('opus')
        except Exception as e:
            if not discord.opus.is_loaded():
                logging.error(f'Opus failed to load: {e}')

        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e)
                                        if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop=self.bot.loop))
            await ctx.send('Now playing: {}'.format(player.title))
        except Exception as e:
            logging.error(f'An error occurred while playing: {e}')
            await self.add_to_queue(ctx, player.title)

    @commands.command(name='pause', help='This command pauses the song')
    @commands.check(guild_only)
    async def pause(self, ctx: commands.Context):
        try:
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                voice_client.pause()
            else:
                await ctx.send("The bot is not playing anything at the moment.")
        except Exception as e:
            logging.error(f'An error occurred while pausing: {e}')

    @commands.command(name='resume', help='Resumes the song')
    @commands.check(guild_only)
    async def resume(self, ctx: commands.Context):
        try:
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_paused():
                voice_client.resume()
            else:
                await ctx.send("The bot was not playing anything before this.\
                                Use play or stream command")
        except Exception as e:
            logging.error(f'An error occurred while resuming: {e}')

    @commands.command(name='skip', help='Skip current song')
    @commands.check(guild_only)
    async def stop(self, ctx: commands.Context):
        try:
            voice_client = ctx.message.guild.voice_client
            JaskierGE.last_interaction_time = datetime.utcnow()  # Update the last interaction time
            if voice_client.is_playing():
                voice_client.stop()
            else:
                await ctx.send("The bot is not playing anything at the moment.")
        except Exception as e:
            logging.error(f'An error occurred while skipping: {e}')

    @commands.command(name="queue", help="View the queue")
    @commands.check(guild_only)
    async def view_queue(self, ctx: commands.Context):
        try:
            queue_items = [list(item) for item in self.queue.items()]
            output = t2a(header=["Queue No", "Song"],
                        body=queue_items,
                        first_col_heading=True)
            await ctx.send(f"Queue:\n```\n{output}\n```")
        except Exception as e:
            logging.error(f'An error occurred while viewing the queue: {e}')

    @commands.command(name="move", help="Move song in the queue(queue no  queue postion)")
    @commands.check(guild_only)
    async def move_song(self, ctx: commands.Context, queue_num: int, queue_pos: int):
        try:
            if queue_num == queue_pos:
                await ctx.send("FUCK OFF GERALT!!!")
            queue_items = []
            for id, title in list(self.queue.items()):
                if id == queue_pos:
                    if queue_pos < queue_num:
                        queue_items.append(self.queue[queue_num])
                        queue_items.append(title)
                    elif queue_pos > queue_num:
                        queue_items.append(title)
                        queue_items.append(self.queue[queue_num])
                    continue
                if id == queue_num:
                    continue
                queue_items.append(title)
            await self.repopulate_queue(queue_items)
            await ctx.send("Moved " + str(self.queue[queue_pos]) + " to queue position: " + str(queue_pos))
        except Exception as e:
            logging.error(f'An error occurred while moving a song in the queue: {e}')

    @commands.command(name="remove", help="Remove song in the queue(Song No)")
    @commands.check(guild_only)
    async def remove_song(self, ctx: commands.Context, song_num: int):
        try:
            if song_num > len(self.queue):
                await ctx.send("FUCK OFF GERALT!!!")
            queue_items = []
            removed_song = ""
            for id, title in list(self.queue.items()):
                if id == song_num:
                    removed_song = title
                    continue
                queue_items.append(title)
            self.repopulate_queue(queue_items)
            await ctx.send("Removed " + removed_song + " from queue")
        except Exception as e:
            logging.error(f'An error occurred while removing a song from the queue: {e}')

    # Event listener for the on_message event
    @commands.Cog.listener()
    async def on_message(self, message):
        # Update the last interaction time
        if message.author == self.bot.user:
            return
        else:
            self.last_interaction_time = datetime.utcnow()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission to use this command.")

    # Helper Methods
    async def add_to_queue(self, ctx: commands.Context, title):
        try:
            queuelen = len(self.queue)
            if queuelen >= 0:
                self.queue[queuelen] = title
                await ctx.send("Added to queue: {}".format(title))
        except Exception as e:
            logging.error(f'An error occurred while adding to the queue: {e}')

    async def remove_just_played(self):
        try:
            queue_items = []
            for id, title in list(self.queue.items()):
                if id == 0:
                    continue
                queue_items.append(title)
            await self.repopulate_queue(queue_items)
        except Exception as e:
            logging.error(f'An error occurred while removing just played: {e}')

    async def repopulate_queue(self, new_queue: list):
        try:
            self.queue.clear()
            ids = [*range(len(new_queue))]
            self.queue = dict(zip(ids, new_queue))
        except Exception as e:
            logging.error(f'An error occurred while repopulating the queue: {e}')

    async def play_next(self, ctx: commands.Context):
        try:
            if len(self.queue) > 0:
                await self.remove_just_played()
                url = self.queue[0]
                async with ctx.typing():
                    player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                    ctx.voice_client.play(player, after=lambda e:print('Player error: %s' % e)
                                          if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop=self.bot.loop))
                await ctx.send('Now playing: {}'.format(player.title))
            else:
                await ctx.send("Queue is empty")
        except Exception as e:
            logging.error(f'An error occurred while playing the next song: {e}')

    #Tasks
    @tasks.loop(minutes=10) 
    async def check_inactivity(self):
        inactive_duration = datetime.utcnow() - self.last_interaction_time
        if inactive_duration > timedelta(minutes=30):
            try:
                for voice_channel in self.bot.voice_clients:
                    if voice_channel.is_connected():
                        await self.bot.get_channel(self.channel_id).send("Bot has been inactive for too long, disconnecting now")
                        await voice_channel.disconnect()
            except Exception as e:
                logging.error(f'Bot could not auto-disconnect: {e}')


async def setup(bot: commands.Bot):
    await bot.add_cog(JaskierGE(bot))
