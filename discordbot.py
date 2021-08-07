import os
import discord
import re
from discord.ext import tasks
from datetime import datetime

token = os.environ['DISCORD_BOT_TOKEN']

notice_channel = 853919175406649364

link_regex = re.compile(
    r'https://discord\.com/channels/'
    r'(?:([0-9]{15,21})|(@me))/'
    r'(?P<channel_id>[0-9]{15,21})/'
    r'(?P<message_id>[0-9]{15,21})/?$'
)
flag_emoji = {
    "<:C001:873406247108476939>":"C001",
    "<:C002:873402760756879400>":"C002",
    "<:C003:872006469103542332>":"C003",
    "<:C004:873402986062295111>":"C004",
    "<:C005:872008266115350568>":"C005",
    "<:C006:873403184876503101>":"C006",
    "<:C007:872015668860583947>":"C007",
    "<:C008:872449071422537739>":"C008",
    "<:C009:873403429559623720>":"C009",
    "<:C010:872011472002228254>":"C010",
    "<:C011:873403563366301807>":"C011",
    "<:C012:873403690537607299>":"C012",
    "<:C013:872014182961274911>":"C013",
    "<:C014:873403824403017739>":"C014",
    "<:C015:872013712679124992>":"C015",
    "<:C016:872424370230923315>":"C016",
    "<:C017:873405013525930034>":"C017",
    "<:C018:873404987089256449>":"C018",
    "<:C019:873405327104684062>":"C019",
    "<:C020:872010874376818708>":"C020"
}

client = discord.Client()
@tasks.loop(seconds=60)
async def loop():
    # 現在の時刻
    now = datetime.now().strftime('%H:%M')
    if now == '07:00':
        channel = client.get_channel(notice_channel)
        await channel.send('@everyone ごきげんよう、紳士諸君')
    elif now == '15:00':
        channel = client.get_channel(notice_channel)
        await channel.send('@everyone お茶会の時間ですわ')
    elif now == '18:00':
        channel = client.get_channel(notice_channel)
        await channel.send('@everyone おかえり、紳士諸君')
    elif now == '23:59':
        channel = client.get_channel(notice_channel)
        await channel.send('@everyone おやすみ、紳士諸君')
@client.event
async def on_ready():
    loop.start()
async def on_message(message):
    # 送信者がbotである場合は弾く
    if message.author.bot:
        return
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

    if message.content.startswith("/vote "):
        result = message.content.replace("/vote ", "")
        pattern = re.compile(r'　| ')
        result = pattern.split(result)
        vote_message = await message.channel.send(result[1])

        if result[0] == "yn":
            await vote_message.add_reaction("👍")
            await vote_message.add_reaction("👎")
        if result[0] == "cou":
            for mykey in flag_emoji.keys():
                await vote_message.add_reaction(mykey)

client.run(token)
