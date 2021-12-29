import os
import discord
import re
from discord.ext import tasks
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
token = os.environ['DISCORD_BOT_TOKEN']
database_url = os.environ['DATABASE_URL']

notice_channel = 853919175406649364
vote_channel = 852882836189085697
news_channel = 853593633051246593
develop_channel = 871948382116134922

link_regex = re.compile(
    r'https://discord\.com/channels/'
    r'(?:([0-9]{15,21})|(@me))/'
    r'(?P<channel_id>[0-9]{15,21})/'
    r'(?P<message_id>[0-9]{15,21})/?$'
)

client = discord.Client()

# 定期メッセージ
@tasks.loop(seconds=60)
async def loop():
    now = datetime.now(tz=JST).strftime('%Y年%m月%d日 %H:%M')
    pattern = re.compile(r' ')
    now = pattern.split(now)
    time = now[1]
    channel = client.get_channel(notice_channel)
    if time == '07:00':
        await channel.send('@everyone ごきげんよう、紳士諸君')

@client.event
async def on_ready():
    loop.start()

@client.event
async def on_message(message):
    # 送信者がbotである場合は弾く
    if message.author.bot:
        return

    # メッセージについたリアクションの個数を送信
    if message.content.startswith("/get_reactions "):
        link = message.content.replace("/get_reactions", "")
        match = link_regex.match(link)
        channel = client.get_channel(int(match.group("channel_id")))
        target_message = await channel.fetch_message(int(match.group("message_id")))
        reactions = target_message.reactions
        text = "絵文字 : 個数\n"
        for reaction in reactions:
            text += f"{reaction.emoji} : {reaction.count}\n"
        await message.channel.send(text)