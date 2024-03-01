import os
from dotenv import load_dotenv
import asyncio
import discord
from discord.ext import commands

load_dotenv()

# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("discord_token")

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='/', intents=intents)


async def run():
    async with bot:
        await bot.load_extension("JaskierGE")
        #await bot.load_extension("ErrorHandler")
        print("Jaskier Loaded")
        await bot.start(DISCORD_TOKEN)

asyncio.run(run())
