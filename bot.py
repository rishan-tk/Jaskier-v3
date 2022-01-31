import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("discord_token")

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='/',intents=intents)

if __name__ == "__main__":
    bot.load_extension("JaskierGE")
    bot.run(DISCORD_TOKEN)