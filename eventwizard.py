import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
import gspread
from google.oauth2.service_account import Credentials
import asyncio
import re
from discord.ui import Modal, TextInput, View, Button
from discord import ButtonStyle
from typing import Optional
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
import collections
import traceback

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    if "monopoly" not in bot.extensions:
        try:
            await bot.load_extension("monopoly")
            print("✅ Loaded extension: monopoly")
        except Exception as e:
            print(f"❌ Failed to load extension: monopoly - {e}")
            traceback.print_exc()
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Command sync failed: {e}")

bot.run(os.getenv("BOT_TOKEN"))
