""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import asyncio
import os
import dateparser
import re
import random
from openai import OpenAI
import io

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

import embeds

from reactionmenu import ViewMenu, ViewSelect, ViewButton

from helpers import checks, db_manager, ArtBuilder



class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot


    # schrijf hierin je commands
    @app_commands.command(name="Grafiek", description="toon een PR grafiek van een bepaalde oefening.", extras={'cog': 'general'})
    @checks.not_blacklisted()
    @checks.not_in_dm()
    @app_commands.describe(user="Persoon")
    async def grafiek(self, interaction, user: discord.Member) -> None:
        pass
   


async def setup(bot):
    await bot.add_cog(General(bot))
