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

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_activity = {}
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

            # Check if the URL is a YouTube playlist
        if "youtube.com/playlist?list=" in url:
            await self.handle_playlist(ctx, url)
        else:
            # Existing logic for a single song
            await self.play_song(ctx, url)

    @commands.command(name='pause', help='This command pauses the song')
    @commands.check(guild_only)
    async def pause(self, ctx: commands.Context):
        try:
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                voice_client.pause()
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
            self.guild_activity[message.guild.id] = {
                'last_interaction_time': datetime.utcnow(),
                'channel_id': message.channel.id
            }
        
        await self.bot.process_commands(message)

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

    async def handle_playlist(self, ctx, playlist_url):
        print("here")
        try:
            print("here2")
            async with ctx.typing():
                playlist_dict = await self.bot.loop.run_in_executor(None, lambda: YTDLSource.extract_info(playlist_url, download=False))
                print(playlist_dict)
                if 'entries' in playlist_dict:
                    for video in playlist_dict['entries']:
                        # Assuming you want the song title for user feedback and queue management
                        song_title = video.get('title')
                        try:
                            player = await YTDLSource.from_url(song_title,
                                                            loop=self.bot.loop,
                                                            stream=True)
                            ctx.voice_client.play(player,
                                                after=lambda  # After audio is finished playing run the lambda function  # noqa
                                                e: logging.error('Player error: %s' % e) if e  # Log error if it occurs  # noqa
                                                else asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop=self.bot.loop))  # noqa
                            await ctx.send('Now playing: {}'.format(player.title))
                        except discord.ClientException as e:
                            await self.add_to_queue(ctx, player.title[:50])
                    await ctx.send(f"Added {len(playlist_dict['entries'])} songs from the playlist to the queue.")
                else:
                    await ctx.send("Could not retrieve any songs from the playlist.")
        except Exception as e:
            await ctx.send("An error occurred while processing the playlist.")
            logging.error(f'Error processing playlist {playlist_url}: {e}')

    async def join_server(self, ctx):
        try:
            ctypes.util.find_library('opus')
        except Exception as e:
            if not discord.opus.is_loaded():
                logging.error(f'Opus failed to load: {e}')

        try:
            channel = ctx.message.author.voice.channel
            await channel.connect()
            # Update guild activity to reflect the new voice channel connection
            self.guild_activity[ctx.guild.id] = {
                'last_interaction_time': datetime.utcnow(),
                'channel_id': ctx.channel.id  # This tracks the text channel, not voice channel; consider if this meets your needs
            }

        except Exception as e:
            await ctx.send("You are not connected to a voice channel")
            logging.error(f'User is not connected to a voice channel: {e}')

    # Tasks
    @tasks.loop(minutes=10)
    async def check_inactivity(self):
        current_time = datetime.utcnow()
        for guild_id, activity in list(self.guild_activity.items()):
            inactive_duration = current_time - activity['last_interaction_time']
            channel_id = activity['channel_id']
            if inactive_duration > timedelta(minutes=30):
                guild = self.bot.get_guild(guild_id)
                if guild and guild.voice_client and guild.voice_client.is_connected():
                    try:
                        # Attempt to send a message to the channel where the last interaction took place
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send("Bot has been inactive for too long, disconnecting now.")
                        await guild.voice_client.disconnect()
                    except Exception as e:
                        logging.error(f'Bot could not auto-disconnect from guild {guild_id}: {e}')
                    finally:
                        # Optionally remove the guild from activity tracking
                        del self.guild_activity[guild_id]


async def setup(bot: commands.Bot):
    await bot.add_cog(JaskierGE(bot))
