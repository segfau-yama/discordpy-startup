from discord.ext import commands
from os import getenv
import discord
import traceback
import fictional_nation
import asyncpg
import asyncio

# ローカル用
try:
    from set import set_token
    set_token()
except:
    print("error")

bot = commands.Bot(command_prefix="#")
token = getenv('DISCORD_BOT_TOKEN')
dsn = getenv('DATABASE_URL')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('引数が足りません。正しい例:#add_meigen @やまもと#1569 "ごはんおいしい"')
    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("このコマンドは存在しません")
    else:
        ch = 871948382116134922
        embed = discord.Embed(title="エラー情報", description="", color=0xf00)
        embed.add_field(name="エラー発生サーバー名", value=ctx.guild.name, inline=False)
        embed.add_field(name="エラー発生サーバーID", value=ctx.guild.id, inline=False)
        embed.add_field(name="エラー発生ユーザー名", value=ctx.author.name, inline=False)
        embed.add_field(name="エラー発生ユーザーID", value=ctx.author.id, inline=False)
        embed.add_field(name="エラー発生コマンド", value=ctx.message.content, inline=False)
        embed.add_field(name="発生エラー", value=error, inline=False)
        m = await bot.get_channel(ch).send(embed=embed)
        await ctx.send(f"何らかのエラーが発生しました。ごめんなさい。\nこのエラーについて問い合わせるときはこのコードも一緒にお知らせください：{m.id}")


@bot.event
async def on_ready():
    print("on_ready")

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
fictional_nation.setup(bot, dsn)
bot.run(token)
