import os
import discord

token = os.environ['DISCORD_BOT_TOKEN']
database_url = os.environ['DATABASE_URL']

client = discord.Client()

@client.event
async def on_message(message):
    # 送信者がbotである場合は弾く
    if message.author.bot:
        return

    # メッセージについたリアクションの個数を送信
    if message.content.startswith("/ping"):
        text = "pong"
        await message.channel.send(text)