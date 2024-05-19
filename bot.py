"""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import asyncio
import logging
import os
import platform
import random
import psycopg2
import time
import discord
import requests
from bs4 import BeautifulSoup

from discord.ext import tasks
from discord.ext.commands import AutoShardedBot
from discord import Webhook
import aiohttp

import embeds
from helpers import WordFinder, db_manager, ArtBuilder
import exceptions

from datetime import datetime, timedelta

from cogs.general import DynamicVotesButton

intents = discord.Intents.all()

bot = AutoShardedBot(
    command_prefix='',
    intents=intents,
    help_command=None,
)


bot.loaded = set()
bot.unloaded = set()


def save_ids_func(cmds):
    """Saves the ids of commands

    Args:
        cmds (Command)
    """
    for cmd in cmds:
        try:
            if cmd.guild_id is None:  # it's a global slash command
                bot.tree._global_commands[cmd.name].id = cmd.id
            else:  # it's a guild specific command
                bot.tree._guild_commands[cmd.guild_id][cmd.name].id = cmd.id
        except:
            pass

bot.save_ids = save_ids_func

# Setup both of the loggers


class LoggingFormatter(logging.Formatter):
    # Colors
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        format = format.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
# File handler
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

# Add the handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)
bot.logger = logger


def init_db():
    time.sleep(30)
    with psycopg2.connect(
        host='192.168.86.200', dbname='pg_wcb3', user=os.environ.get('POSTGRES_USER'), password=os.environ.get('POSTGRES_PASSWORD')
    ) as con:
        
        with con.cursor() as cursor:

            with open(
                f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql"
            ) as file:
                cursor.execute(file.read())

    bot.logger.info(f"initializing db")


@bot.event
async def on_ready() -> None:
    """
    The code in this event is executed when the bot is ready.
    """
    bot.logger.info(f"Logged in as {bot.user.name}")
    bot.logger.info(f"discord.py API version: {discord.__version__}")
    bot.logger.info(f"Python version: {platform.python_version()}")
    bot.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    bot.logger.info("-------------------")


    cmds = await bot.tree.sync()
    bot.save_ids(cmds)


@tasks.loop(minutes=1.0)
async def status_task() -> None:
    """
    Setup the game status task of the bot.
    """

    # check if someone used the status command
    if bot.status_manual is not None:
        # longer than 1 hour ago
        time_diff = datetime.now() - bot.status_manual 
        if time_diff.total_seconds() > 3600:
            bot.status_manual = None

    if bot.status_manual is None:
        statuses = [
            f"📈 detecting PRs!",
            f"🦾 Lifting weights",
        ]

        picked_status = random.choice(statuses)
        await bot.change_presence(activity=discord.CustomActivity(name=picked_status))

@bot.event
async def on_app_command_completion(interaction, command) -> None:
    """
    The code in this event is executed every time a normal command has been *successfully* executed.

    :param context: The context of the command that has been executed.
    """
    full_command_name = command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    if interaction.guild is not None:
        bot.logger.info(
            f"Executed {executed_command} command in {interaction.guild.name} (ID: {interaction.guild_id}) by {interaction.user} (ID: {interaction.user.id})"
        )
    else:
        bot.logger.info(
            f"Executed {executed_command} command by {interaction.user} (ID: {interaction.user.id}) in DMs"
        )

    # add stats to db
    await db_manager.increment_or_add_command_count(interaction.user.id, executed_command, 1)


async def on_tree_error(interaction, error):
    """
    The code in this event is executed every time a command catches an error.

    :param context: The context of the normal command that failed executing.
    :param error: The error that has been faced.
    """
    
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = embeds.OperationFailedEmbed(
            f"**Please slow down** - You can use this command again in {f'{round(hours)} hours ' if round(hours) > 0 else ''}{f'{round(minutes)} minutes ' if round(minutes) > 0 else ''}{f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            emoji="⏲️"
        )

        # send out response
        if interaction.response.is_done():
            return await interaction.followup.send(embed=embed, ephemeral=True)
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    elif isinstance(error, exceptions.UserBlacklisted):
        """
        The code here will only execute if the error is an instance of 'UserBlacklisted', which can occur when using
        the @checks.not_blacklisted() check in your command, or you can raise the error by yourself.
        """
        embed = embeds.OperationFailedEmbed(
            "You are blacklisted from using the bot!",
        )

        if interaction.guild:
            bot.logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) tried to execute a command in the guild {interaction.guild.name} (ID: {interaction.guild_id}), but the user is blacklisted from using the bot."
            )
        else:
            bot.logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) tried to execute a command in the bot's DMs, but the user is blacklisted from using the bot."
            )

    elif isinstance(error, exceptions.UserNotOwner):
        """
        Same as above, just for the @checks.is_owner() check.
        """
        embed = embeds.OperationFailedEmbed(
            "You are not the owner of the bot!",
            emoji="🛑"
        )
        if interaction.guild:
            bot.logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) tried to execute an owner only command in the guild {interaction.guild.name} (ID: {interaction.guild_id}), but the user is not an owner of the bot."
            )
        else:
            bot.logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
            )

    elif isinstance(error, discord.app_commands.MissingPermissions):
        embed = embeds.OperationFailedEmbed(
            "You are missing the permission(s) `"
            + ", ".join(error.missing_permissions)
            + "` to execute this command!",
        )

    elif isinstance(error, discord.app_commands.BotMissingPermissions):
        embed = embeds.OperationFailedEmbed(
            "I am missing the permission(s) `"
            + ", ".join(error.missing_permissions)
            + "` to fully perform this command!",
        )

    elif isinstance(error, exceptions.WrongChannel):
        embed = embeds.OperationFailedEmbed(
            "Wrong channel!",
            # We need to capitalize because the command arguments have no capital letter in the code.
            str(error).capitalize(),
        )

    elif isinstance(error, exceptions.UserNotInVC):
        embed = embeds.OperationFailedEmbed(
            f"You are not in a voice channel",
            emoji="🔇"
        ) 

    elif isinstance(error, exceptions.BotNotInVC):
        embed = embeds.OperationFailedEmbed(
            f" Bot is not in vc",
            "use /join to add bot to vc",
            emoji="🔇"
        ) 

    elif isinstance(error, exceptions.BotNotPlaying):
        embed = embeds.OperationFailedEmbed(
            f"The bot is not playing anything at the moment.",
            "Use /play to play a song or playlist",
            emoji="🔇"
        )
    
    elif isinstance(error, exceptions.TimeoutCommand):
        embed = embeds.OperationFailedEmbed(
            "You took too long!",
            emoji="⏲️"
        )
    
    elif isinstance(error, exceptions.CogLoadError):
        embed = embeds.OperationFailedEmbed(
            title="Cog error!",
        )
    
    elif isinstance(error, discord.HTTPException):
        embed = embeds.OperationFailedEmbed(
            title="Something went wrong!",
            description="most likely daily application command limits.",
        )

    else:
        embed = embeds.OperationFailedEmbed(
            title="Error!",
            # We need to capitalize because the command arguments have no capital letter in the code.
            description=str(error).capitalize(),
        )

    bot.logger.info(error) 
    
    # send out response
    if interaction.response.is_done():
        return await interaction.followup.send(embed=embed)
    await interaction.response.send_message(embed=embed)


bot.tree.on_error = on_tree_error


async def setup_hook() -> None:

    # For dynamic items, we must register the classes instead of the views.
    bot.add_dynamic_items(DynamicVotesButton)

bot.setup_hook = setup_hook


async def load_cogs() -> None:
    """
    The code in this function is executed whenever the bot will start.
    """
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                bot.logger.info(f"Loaded extension '{extension}'")
                bot.loaded.add(extension)

            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                bot.logger.error(f"Failed to load extension {extension}\n{exception}")
                bot.unloaded.add(extension)


init_db()
asyncio.run(load_cogs())
bot.run(os.environ.get("TOKEN"))
