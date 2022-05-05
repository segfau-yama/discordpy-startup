from discord.ext import commands
from os import getenv
import traceback
import discord
import random
import fictional_nation
import psycopg2

bot = commands.Bot(command_prefix="#")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

bot.add_cog(fictional_nation.world(bot))

# token = getenv('DISCORD_BOT_TOKEN')
token = "NzEyNjU5NDc1MTUyMTA5NTY4.Gw2KmQ.rmy5Bxqwln13T5wfrPMRMCWAJbR5vOrtt_LnCo"
bot.run(token)