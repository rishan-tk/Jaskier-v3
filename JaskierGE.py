import discord
from discord.ext import commands
from YTDLSource import YTDLSource
import asyncio

class JaskierGE(commands.Cog):
    queue = {}
    current_id = 0

    def __init__(self, bot : commands.Bot):
        self.bot = bot

    @commands.command(name="join", help="Tells the bot to join")
    async def join(self, ctx):
        channel = ctx.message.author.voice.channel
        await channel.connect()

    @commands.command(name="leave", help="Tells the bot to leave")
    async def leave(self, ctx):
        channel = ctx.message.guild.voice_client
        if channel.is_connected():
            await channel.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.command(name="playL")
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(query))

    @commands.command(name="play")
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command(name="stream")
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""
        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop=self.bot.loop))

            await ctx.send('Now playing: {}'.format(player.title))
        except Exception as e:
            await self.add_to_queue(ctx, url, player.title)

    @commands.command(name='pause', help='This command pauses the song')
    async def pause(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.command(name='resume', help='Resumes the song')
    async def resume(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
        else:
            await ctx.send("The bot was not playing anything before this. Use play or stream command")

    @commands.command(name='stop', help='Stops the song')
    async def stop(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.stop()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.command(name="queue", help="View the queue")

    async def add_to_queue(self, ctx, url, title):
        queuelen = len(self.queue)
        if queuelen >= 0:
            self.queue[queuelen] = url
            await ctx.send("Added to queue: {}".format(title))

    async def play_next(self, ctx):
        if len(self.queue) > 0:
            url = self.queue[self.current_id]
            self.current_id = self.current_id+1
            try:
                async with ctx.typing():
                    player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                    ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop=self.bot.loop))

                await ctx.send('Now playing: {}'.format(player.title))
            except Exception as e:
                await ctx.send("Exception " + e)
        else:
            await ctx.send("Queue is empty")

def setup(bot: commands.Bot):
    bot.add_cog(JaskierGE(bot))