import os
import discord
import re
from discord.ext import tasks
from datetime import datetime, timedelta, timezone
import psycopg2
import time

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
    "<:C001:873406247108476939>":"アメリカーナ帝国",
    "<:C002:873402760756879400>":"イギリス連合王国",
    "<:C003:872006469103542332>":"オクター連邦",
    "<:C004:873402986062295111>":"オーストリア帝国/神聖ローマ帝国",
    "<:C005:872008266115350568>":"カリフォーニエン大公国",
    "<:C006:873403184876503101>":"ガリア連邦共和国",
    "<:C007:872015668860583947>":"グアダラハラ連邦",
    "<:C008:872449071422537739>":"テソモニア旧共産圏地域",
    "<:C009:873403429559623720>":"テソモニア民主共和国",
    "<:C010:872011472002228254>":"デンマーク共和国",
    "<:C011:873403563366301807>":"ニッショニア連邦",
    "<:C012:873403690537607299>":"ネーデルランド連合王国",
    "<:C013:872014182961274911>":"ヒンドゥスターンベンガル武装帝国",
    "<:C014:873403824403017739>":"ビザンツ帝国",
    "<:C015:872013712679124992>":"モンゴル自由共和国",
    "<:C016:872424370230923315>":"ロヘニア",
    "<:C017:873405013525930034>":"地球連邦",
    "<:C018:873404987089256449>":"日本国",
    "<:C019:873405327104684062>":"自由カリブ海同盟",
    "<:C020:872010874376818708>":"高天原北域商会"
}

country_and_owner = {
    749896281618645036:"アメリカーナ帝国",
    858717333287338004:"イギリス連合王国",
    501014325138292737:"オクター連邦",
    651650016946946048:"オーストリア帝国/神聖ローマ帝国",
    822100206563754045:"カリフォーニエン大公国",
    "no_key_1":"ガリア連邦共和国",
    812992534597861397:"グアダラハラ連邦",
    820918441770745866:"テソモニア旧共産圏地域",
    736112703093080114:"テソモニア民主共和国",
    629189757758341122:"デンマーク共和国",
    "no_key_2":"ニッショニア連邦",
    533530662981074944:"ネーデルランド連合王国",
    243420382709809152:"ヒンドゥスターンベンガル武装帝国",
    707209061933776916:"ビザンツ帝国",
    735055190402531329:"モンゴル自由共和国",
    822098008094408724:"ロヘニア",
    772108293950406656:"地球連邦",
    647340197196857365:"日本国",
    491578038207774721:"自由カリブ海同盟",
    661481352931311636:"高天原北域商会"
}

client = discord.Client()
conn = psycopg2.connect(database_url)
cur = conn.cursor()

# 定期メッセージ
@tasks.loop(seconds=60)
async def loop():
    now = datetime.now(tz=JST).strftime('%Y年%m月%d日 %H:%M')
    pattern = re.compile(r' ')
    now = pattern.split(now)
    date = now[0]
    time = now[1]
    channel = client.get_channel(notice_channel)
    v_channel = client.get_channel(vote_channel)
    d_channel = client.get_channel(develop_channel)
    await d_channel.send('デバック')
    if time == '02:50':
        await channel.send('@everyone おやすみ、紳士諸君')
        vote_message = await v_channel.send(f"@everyone{date}の投票です。一人につき二国まで投票可能です。")
        for emoji in flag_emoji:
            await vote_message.add_reaction(emoji)
        cur.execute("INSERT INTO vote_message (vote_id,message_id,date) VALUES (1,%s,%s);", (vote_message.id, date))
        conn.commit()
    if time == '07:00':
        await channel.send('@everyone ごきげんよう、紳士諸君')
    if time == '15:00':
        await channel.send('@everyone お茶会の時間ですわ')
    if time == '18:00':
        await channel.send('@everyone おかえり、紳士諸君')
    if time == '07:00':
        cur.execute("SELECT * FROM vote_message WHERE vote_id = 1;")
        data = cur.fetchall()
        message = await v_channel.fetch_message(str(data[0][0]))
        reactions = message.reactions
        for reaction in reactions:
            tp_point = (reaction.count - 1) * 5
            cur.execute("UPDATE country_user SET transport_point=transport_point+%s WHERE country_name=%s;",
                        (tp_point, flag_emoji[str(reaction.emoji)]))
        cur.execute("TRUNCATE TABLE vote_message;")
        cur.execute("SELECT * FROM country_user;")
        data = cur.fetchall()
        country = ""
        for i in range(20):
            country += f"{data[i]}\n"
        await channel.send(country)
        conn.commit()

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

    # クエリ実行機能
    if message.content.startswith("/sql "):
        result = message.content.replace("/sql ", "")
        pattern = re.compile(r'/sql+?')
        sql_query = pattern.split(result)
        cur.execute(sql_query[0])
        conn.commit()
        try:
            data = cur.fetchall()
            await message.channel.send(data)
        except:
            await message.channel.send("OK")

    # 輸送力加算(ニュース)
    if message.channel.id == news_channel:
        result = message.content
        tp_point = len(result) / 50
        cur.execute("UPDATE country_user SET transport_point=transport_point+%s WHERE country_name=%s;",
                    (tp_point, country_and_owner[message.author.id]))
        conn.commit()

client.run(token)
cur.close()
conn.close()