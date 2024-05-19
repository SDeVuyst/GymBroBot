import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot


    # schrijf hierin je commands
    @app_commands.command(
            name="grafiek", 
            description="toon een PR grafiek van een bepaalde oefening."
    )
    @app_commands.describe(user="Persoon waarvan je de grafiek wilt zien")
    async def grafiek(self, interaction, user: discord.Member) -> None:
        pass
   


async def setup(bot):
    await bot.add_cog(General(bot))
