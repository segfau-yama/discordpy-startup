import os
import discord
import re
from discord.ext import tasks
from datetime import datetime, timedelta, timezone
import psycopg2

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
flag_emoji = {
    "<:C001:873406247108476939>": "アメリカーナ帝国",
    "<:C002:873402760756879400>": "イギリス連合王国",
    "<:C003:872006469103542332>": "オクター連邦",
    "<:C004:873402986062295111>": "オーストリア帝国/神聖ローマ帝国",
    "<:C005:872008266115350568>": "カリフォーニエン大公国",
    "<:C006:873403184876503101>": "ガリア連邦共和国",
    "<:C007:872015668860583947>": "グアダラハラ連邦",
    "<:C008:872449071422537739>": "テソモニア旧共産圏地域",
    "<:C009:873403429559623720>": "テソモニア民主共和国",
    "<:C010:872011472002228254>": "デンマーク共和国",
    "<:C011:873403563366301807>": "ニッショニア連邦",
    "<:C012:873403690537607299>": "ネーデルランド連合王国",
    "<:C013:872014182961274911>": "ヒンドゥスターンベンガル武装帝国",
    "<:C014:873403824403017739>": "ビザンツ帝国",
    "<:C015:872013712679124992>": "モンゴル自由共和国",
    "<:C016:872424370230923315>": "ロヘニア",
    "<:C017:873405013525930034>": "地球連邦",
    "<:C018:873404987089256449>": "日本国",
    "<:C019:873405327104684062>": "自由カリブ海同盟",
    "<:C020:872010874376818708>": "高天原北域商会"
}

client = discord.Client()

@client.event
async def on_message(message):
    # 送信者がbotである場合は弾く
    if message.author.bot:
        return
    # 投票機能
    if message.content.startswith("/vote "):
        result = message.content.replace("/vote ", "")
        pattern = re.compile(r'　| ')
        result = pattern.split(result)
        vote_message = await message.channel.send(result[1])

        if result[0] == "yn":
            await vote_message.add_reaction("👍")
            await vote_message.add_reaction("👎")
        if result[0] == "cou":
            for emoji in flag_emoji:
                await vote_message.add_reaction(emoji)

client.run(token)