from discord.ext import commands
from os import getenv
import traceback
import fictional_nation


bot = commands.Bot(command_prefix="#")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

bot.add_cog(fictional_nation.world(bot))

token = getenv('DISCORD_BOT_TOKEN')

bot.run(token)