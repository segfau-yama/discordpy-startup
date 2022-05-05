from discord.ext import commands
from os import getenv
import traceback
import fictional_nation
import os

os.environ['DATABASE_URL'] = "postgres://qdrcocvpqfbbwg:5b360ed6bcd13526a6136961b1d0c3dd1264a529cb81aea1e949d16ff9662431@ec2-3-213-76-170.compute-1.amazonaws.com:5432/d61i6gvsbs1frk"
os.environ['DISCORD_BOT_TOKEN'] = "NzEyNjU5NDc1MTUyMTA5NTY4.GDmExB.ySQQej7wcWMOhwnD7xe8qF0cUrj_SyuxIUzHi4"

bot = commands.Bot(command_prefix="#")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

bot.add_cog(fictional_nation.world(bot))

token = getenv('DISCORD_BOT_TOKEN')

bot.run(token)