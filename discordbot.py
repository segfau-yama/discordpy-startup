from discord.ext import commands
from os import getenv
import traceback
import fictional_nation
import asyncpg

# ローカル用
try:
    from set import set_token
    set_token()
except:
    print("error")

bot = commands.Bot(command_prefix="#")
dsn = getenv('DATABASE_URL')
token = getenv('DISCORD_BOT_TOKEN')


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.event
async def on_ready():
    print("on_ready")

fictional_nation.setup(bot, dsn)
bot.run(token)
