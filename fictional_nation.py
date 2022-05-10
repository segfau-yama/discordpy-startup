import asyncpg
import discord
from discord.ext import tasks, commands
from datetime import datetime
from os import getenv
import asyncio
import re

class Every:
    def __init__(self, bot, dsn):
        self.bot = bot
        self.dsn = dsn
        self.conn = None
        self.flag = []

    # 起動時処理
    @commands.Cog.listener()
    async def on_ready(self):
        self.conn = await asyncpg.connect(self.dsn)
        rows = await self.conn.fetch("SELECT flag FROM country")
        for row in rows:
            self.flag.append(row["flag"])


# 架空国家用class
class Bot(commands.Cog, Every):
    def __init__(self, bot, dsn):
        super().__init__(bot, dsn)
        self.loop.add_exception_type(asyncpg.PostgresConnectionError)
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    # 投票時処理
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        vote_id = None
        vote_jg = None
        rows1 = await self.conn.fetch("SELECT vote_id FROM bot_data")
        rows2 = await self.conn.fetch("SELECT today_vote FROM country WHERE user_id = ($1)", str(payload.user_id))
        for row in rows1:
            vote_id = int(row['vote_id'])
        for row in rows2:
            vote_jg = bool(row['today_vote'])
        vote_jg = not vote_jg
        if payload.message_id == vote_id and vote_jg:
            await self.conn.execute(
                "UPDATE country SET (country_power, today_vote)=(country_power+5, ($1)) WHERE user_id=($2)", vote_jg,
                str(payload.user_id))

    # 時間処理
    @tasks.loop(seconds=60)
    async def loop(self):
        now = datetime.now().strftime('%H:%M')
        notice_channel = await self.bot.fetch_channel(853919175406649364)
        vote_channel = await self.bot.fetch_channel(852882836189085697)
        dev_channel = await self.bot.fetch_channel(871948382116134922)

        # 投票開始
        if now == "00:00":
            vote = await vote_channel.send('人気投票を開始します。投票は2国まで可能です。自国への投票は-10となります。')
            print(vote.id)
            for emoji in self.flag:
                await vote.add_reaction(emoji)
            await self.conn.execute("UPDATE bot_data SET vote_id=($1) WHERE id=1", str(vote.id))

        if now == "07:00":
            await notice_channel.send('おはよう、紳士諸君')
        if now == "12:00":
            await notice_channel.send('紅茶はいかがかね？')
        if now == "23:00":
            await notice_channel.send('おやすみ、紳士諸君')

        # 投票集計
        if now == "23:59":
            try:
                vote_id = None
                txt = ""
                rows = await self.conn.fetch("SELECT vote_id FROM bot_data")
                for row in rows:
                    vote_id = row['vote_id']
                vote = await vote_channel.fetch_message(int(vote_id))
                if vote is not None:
                    print(vote.reactions)
                    await vote_channel.send("投票結果:")
                    for reaction in vote.reactions:
                        emoji = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
                        count = reaction.count * 10 - 10
                        txt += f"{emoji}:{count}"
                        await self.conn.execute("UPDATE country SET (country_power,today_vote)=(country_power+($1),FALSE) WHERE flag=($2)", count, emoji)
                    await vote_channel.send(txt)
            except:
                print("error")

    @commands.command()
    async def all_country(self, ctx):
        """全ての国家を表示をする"""
        power = ""
        rows = await self.conn.fetch("SELECT flag, country_name, user_id, country_power FROM country ORDER BY country_power DESC")
        await ctx.send("国力一覧")
        for row in rows:
            user = await self.bot.fetch_user(row['user_id'])
            power += f"{row}位|{row['flag']} | {row['country_name']} | {user} | {row['country_power']}pt\n"
        await ctx.send(power)

    @commands.command()
    async def time(self, ctx):
        """時間を表示をする"""
        now = datetime.now().strftime('%H:%M')
        await ctx.send(f"ただいまの時刻:{now}")

    @commands.command()
    async def vote_result(self, ctx):
        """現在の投票結果を確認する"""
        vote_channel = await self.bot.fetch_channel(852882836189085697)
        try:
            vote_id = None
            txt = ""
            rows = await self.conn.fetch("SELECT vote_id FROM bot_data")
            for row in rows:
                vote_id = row['vote_id']
            vote = await vote_channel.fetch_message(int(vote_id))
            if vote is not None:
                await ctx.send("現在の投票結果:")
                for reaction in vote.reactions:
                    emoji = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
                    count = reaction.count * 10 - 10
                    txt += f"{emoji}:{count}pt\n"
                await ctx.send(txt)
        except:
            print("error")

    @commands.command()
    async def add_meigen(self, ctx, user: discord.Member, meigen: str):
        """紳士の会メンバーの名言を追加する"""
        print(user.id, meigen)
        await self.conn.execute("INSERT INTO meigen (user_id,text) VALUES (($1),($2))", str(user.id), meigen)

    @commands.command()
    async def look_meigen(self, ctx, *args):
        """紳士の会メンバーの名言を見る"""
        if len(args) == 1:
            txt = ""
            if '<@' in args[0]:
                user_id = re.findall('[0-9]+', args[0])
                rows = await self.conn.fetch("SELECT text FROM meigen WHERE user_id=($1)", user_id[0])
                user = await self.bot.fetch_user(user_id[0])
                for row in rows:
                    txt += f"{user}の名言:\n{row['text']}\n"
                await ctx.send(txt)
            elif not args[0]:
                await ctx.send("こいつの名言は無いよ")
        elif len(args) == 0:
            txt = ""
            rows = await self.conn.fetch("SELECT text FROM meigen")
            for row in rows:
                txt += f"{row['text']}\n"
            await ctx.send(txt)

class Administrator(commands.Cog, Every):
    def __init__(self, bot, dsn):
        super().__init__(bot, dsn)

    def cog_check(self, ctx):
        return ctx.author.id == 501014325138292737

    @commands.command()
    async def db_conn(self, ctx):
        """データベースに再接続する"""
        self.conn = await asyncpg.connect(self.dsn)
        await ctx.send("データベースに接続します")

    @commands.command()
    async def db_close(self, ctx):
        """データベースから切断する"""
        await ctx.send("データベースから切断します")
        await self.conn.close()

    @commands.command()
    async def db_query1(self, ctx, *, query):
        """クエリを実行する"""
        await ctx.send(query)
        await self.conn.execute(query)

    @commands.command()
    async def db_query2(self, ctx, *, query):
        """クエリを実行し結果を出力する"""
        txt = ""
        rows = await self.conn.fetch(query)
        for row in rows:
            txt += f"{row}\n"
        await ctx.send(txt)

    @commands.command()
    async def reset(self, ctx):
        """国力をリセットする"""
        await ctx.send("国力を初期化します")
        await self.conn.execute("UPDATE country SET (country_power, today_vote) = (0, FALSE)")

    @commands.command()
    async def add_country(self, ctx, country, flag, player):
        """国家を追加する"""
        await ctx.send(f"国家を追加しました。\n国名:{country}\n国旗:{flag}\nプレイヤーid:{player}")
        await self.conn.execute("INSERT INTO country (country_name, flag, user_id) VALUES (($1), ($2), ($3))", country,
                                flag, player)


class Test(commands.Cog):
    def __init__(self, bot, conn):
        self.bot = bot
        self.conn = conn

    @commands.command()
    async def db_query2(self, ctx, *, query):
        print(self.conn)
        txt = ""
        rows = await self.conn.fetch(query)
        for row in rows:
            txt += f"{row}\n"
        await ctx.send(txt)

    @commands.Cog.listener()
    async def on_ready(self):
        print(self.conn)


def setup(bot, dsn):
    bot.add_cog(Bot(bot, dsn))
    bot.add_cog(Administrator(bot, dsn))
