from discord.ext import commands, tasks
import discord

import asyncio
import ctypes
import ctypes.util
import logging  # Import the logging module
from datetime import datetime, timedelta
from table2ascii import table2ascii as t2a

from YTDLSource import YTDLSource
from musicqueue import MusicQueue

# Configure logging
logging.basicConfig(
    filename='discord_bot.log',  # Log file name
    level=logging.ERROR,        # Log only error messages and above
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class JaskierGE(commands.Cog):
    musicQueue = MusicQueue()
    last_interaction_time = datetime.utcnow()  # Initialize with the current time (auto-updated upon message to bot)  # noqa
    channel_id = ""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_inactivity.start()

    def guild_only(ctx):
        # Check if the command was invoked in a guild (server) channel
        return ctx.guild is not None

    @commands.command(name="join", help="Command to make the bot join the server which the user is connected to")  # noqa
    async def join(self, ctx: commands.Context):
        await self.join_server(ctx)

    @commands.command(name="leave", help="Command to make the bot leave the server")  # noqa
    @commands.check(guild_only)
    async def leave(self, ctx: commands.Context):
        try:
            channel = ctx.message.guild.voice_client
            if channel.is_connected():
                await channel.disconnect()
            else:
                await ctx.send("The bot is not connected to a voice channel.")
        except Exception as e:
            logging.error(f'An error occurred while leaving a voice\
                          channel: {e}')

    @commands.command(name="play", help="Command to play a song or add a song to queue if song is already playing\nUsage: /play (youtube-link/song-name)")  # noqa
    @commands.check(guild_only)
    async def play(self, ctx: commands.Context, *, url):
        # Check if bot is connected to a voice channel, if not join one first
        if len(self.bot.voice_clients) == 0:
            await self.join_server(ctx)

        try:
            ctypes.util.find_library('opus')
        except Exception as e:
            if not discord.opus.is_loaded():
                logging.error(f'Opus failed to load: {e}')

        await self.play_song(ctx, url)

    @commands.command(name='pause', help='This command pauses the song')
    @commands.check(guild_only)
    async def pause(self, ctx: commands.Context):
        try:
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                voice_client.pause()
            else:
                await ctx.send("The bot is not playing anything at \
                               the moment.")
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
                                Use play command")
        except Exception as e:
            logging.error(f'An error occurred while resuming: {e}')

    @commands.command(name='skip', help='Skip current song')
    @commands.check(guild_only)
    async def skip(self, ctx: commands.Context):
        try:
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                voice_client.stop()
            else:
                await ctx.send("The bot is not playing anything at \
                               the moment.")
        except Exception as e:
            logging.error(f'An error occurred while skipping: {e}')

    @commands.command(name="queue", help="View the queue")
    @commands.check(guild_only)
    async def view_queue(self, ctx: commands.Context):
        try:
            await ctx.send(self.musicQueue.view_queue())
        except Exception as e:
            logging.error(f'An error occurred while viewing the queue: {e}')

    @commands.command(name="move", help="Move song in the queue(song no  new position)")  # noqa
    @commands.check(guild_only)
    async def move_song(self, ctx: commands.Context,
                        song_index: int, new_pos: int):
        new_pos -= 1  # Numbers shown to user are larger by 1
        song_index -= 1  # Numbers shown to user are larger by 1

        try:
            if song_index == new_pos:
                await ctx.send("You are referencing the same song twice.")
                return

            song_moved = self.musicQueue.move_song_i(song_index, new_pos)

            if song_moved is True:
                await ctx.send("Moved to queue position: " + str(new_pos+1))
            else:
                await ctx.send(song_moved)  # Return error message
        except Exception as e:
            logging.error(f'An error occurred while moving a song \
                          in the queue: {e}')

    @commands.command(name="remove", help="Remove song in the queue(Song No)")
    @commands.check(guild_only)
    async def remove_song(self, ctx: commands.Context, song_num: int):
        song_num -= 1  # Numbers shown to user are larger by 1
        try:
            if song_num > self.musicQueue.size() or song_num < 0:
                await ctx.send("Number longer than queue length")
                return

            removed_song = self.musicQueue.queue[song_num]
            self.musicQueue.remove_from_queue_i(song_num)
            await ctx.send("Removed " + removed_song + " from queue")
        except Exception as e:
            logging.error(f'An error occurred while removing a song \
                          from the queue: {e}')

    # Event listener for the on_message event
    @commands.Cog.listener()
    async def on_message(self, message):
        # Update the last interaction time
        if message.author == self.bot.user:
            return
        else:
            self.last_interaction_time = datetime.utcnow()

    # Error message handle for CheckFailure error
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Sorry, you don't have permission \
                           to use this command.")

    # Helper Methods
    async def add_to_queue(self, ctx: commands.Context, title):
        try:
            await self.musicQueue.add_to_queue(title)
            await ctx.send("Added to queue: {}".format(title))
        except Exception as e:
            logging.error(f'An error occurred while adding to the queue: {e}')

    async def play_next(self, ctx: commands.Context):
        try:
            if self.musicQueue.size() > 0:
                songName = self.musicQueue.remove_next()
                await self.play_song(ctx, songName)
            else:
                await ctx.send("Queue is currently empty")
        except Exception as e:
            logging.error(f'An error occurred while playing the \
                          next song: {e}')

    async def play_song(self, ctx, songName):
        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(songName,
                                                   loop=self.bot.loop,
                                                   stream=True)
                ctx.voice_client.play(player,
                                    after=lambda  # After audio is finished playing run the lambda function  # noqa
                                    e: logging.error('Player error: %s' % e) if e  # Log error if it occurs  # noqa
                                    else asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop=self.bot.loop))  # noqa
                await ctx.send('Now playing: {}'.format(player.title))
        except discord.ClientException as e:
            await self.add_to_queue(ctx, player.title[:50])
        except Exception as e:
            logging.error(f'An error occurred while playing: {e}')

    async def join_server(self, ctx):
        try:
            channel = ctx.message.author.voice.channel
            self.channel_id = channel.id
            await channel.connect()
        except Exception as e:
            await ctx.send("You are not connected to a voice channel")
            logging.error(f'User is not connected to a voice channel: {e}')

    # Tasks
    @tasks.loop(minutes=10)
    async def check_inactivity(self):
        inactive_duration = datetime.utcnow() - self.last_interaction_time
        if inactive_duration > timedelta(minutes=30):
            try:
                for voice_channel in self.bot.voice_clients:
                    if voice_channel.is_connected():
                        await self.bot.get_channel(self.channel_id).send("Bot has been inactive for too long, disconnecting now")  # noqa
                        await voice_channel.disconnect()
            except Exception as e:
                logging.error(f'Bot could not auto-disconnect: {e}')


async def setup(bot: commands.Bot):
    await bot.add_cog(JaskierGE(bot))
