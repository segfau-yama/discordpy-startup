import asyncpg
import discord
from discord.ext import tasks, commands
from datetime import datetime
from os import getenv
import asyncio

# 架空国家用class
class Everyone:
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
        print("on_ready")


class Bot(commands.Cog, Everyone):
    def __init__(self, bot, dsn):
        super().__init__(bot, dsn)
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    # 投票時処理
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
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

        # 投票開始
        if now == "00:00":
            vote = await vote_channel.send('人気投票を開始します。投票は2国まで可能です。自国への投票は-10となります。')
            for emoji in self.flag:
                await vote.add_reaction(emoji)
            await self.conn.execute("UPDATE bot_data SET vote_id=($1) WHERE id=1", vote.id)

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
                        await self.conn.execute("UPDATE country SET country_power=country_power+($1) WHERE flag=($2)",
                                                count, emoji)
                    await vote_channel.send(txt)
            except:
                print("error")


class User(commands.Cog, Everyone):
    # 国力表示
    @commands.command()
    async def all_country(self, ctx):
        power = ""
        rows = await self.conn.fetch("SELECT flag, country_name, user_id, country_power FROM country")
        await ctx.send("国力一覧")
        for row in rows:
            user = await self.bot.fetch_user(row['user_id'])
            power += f"{row['flag']} | {row['country_name']} | {user} | {row['country_power']}pt\n"
        await ctx.send(power)

    # 時間表示
    @commands.command()
    async def time(self, ctx):
        now = datetime.now().strftime('%H:%M')
        await ctx.send(f"ただいまの時刻:{now}")


class SuperUser(commands.Cog, Everyone):
    @commands.check
    async def is_owner(self, ctx):
        return ctx.author.id == "オーナーのid"

    # 再接続
    @commands.command()
    @commands.is_owner()
    async def db_conn(self, ctx):
        self.conn = await asyncpg.connect(self.dsn)
        await ctx.send("データベースに接続します")

    # 入力クエリ実行
    @commands.command()
    @commands.is_owner()
    async def db_query1(self, ctx, *, query):
        await ctx.send(query)
        await self.conn.execute(query)

    # 出力クエリ実行
    @commands.command()
    @commands.is_owner()
    async def db_query2(self, ctx, *, query):
        txt = ""
        rows = await self.conn.fetch(query)
        for row in rows:
            txt += f"{row}\n"
        await ctx.send(txt)

    # 国力リセット
    @commands.command()
    @commands.is_owner()
    async def reset(self, ctx):
        await ctx.send("国力を初期化します")
        await self.conn.execute("UPDATE country SET (country_power, today_vote) = (0, FALSE)")

    # 国家追加
    @commands.command()
    @commands.is_owner()
    async def add_country(self, ctx, country, flag, player):
        await ctx.send(f"国力を追加しました。\n国名:{country}\n国旗:{flag}\nプレイヤーid:{player}")
        await self.conn.execute("INSERT INTO country (country_name, flag, user_id) VALUES (($1), ($2), ($3))", country, flag, player)


def setup(bot, dsn):
    bot.add_cog(Bot(bot, dsn))
    bot.add_cog(User(bot, dsn))
    bot.add_cog(SuperUser(bot, dsn))
