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
    # TODO:flagの読み込みを関数で行う
    # TODO:データベースの接続を簡略化する
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

    # 時間処理
    @tasks.loop(seconds=60)
    async def loop(self):
        now = datetime.now().strftime('%H:%M')
        notice_channel = await self.bot.fetch_channel(853919175406649364)
        vote_channel = await self.bot.fetch_channel(852882836189085697)
        dev_channel = await self.bot.fetch_channel(871948382116134922)

        # 投票開始
        # TODO:投票開始をサブコマンドにする
        if now == "00:00":
            vote = await vote_channel.send('@everyone 人気投票を開始します。投票は2国まで可能です。自国への投票は-10となります。')
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
        # TODO:投票集計をサブコマンドにする
        # TODO:デバッグ
        # TODO:Embed化
        if now == "23:59":
            # noinspection PyBroadException
            try:
                vote_id = None
                txt = "@everyone 投票結果:\n"
                rows = await self.conn.fetch("SELECT vote_id FROM bot_data")
                users = set()

                # 投票メッセージを取得
                for row in rows:
                    vote_id = row['vote_id']
                vote = await vote_channel.fetch_message(int(vote_id))

                # 投票集計処理
                if vote is not None:
                    for reaction in vote.reactions:
                        async for user in reaction.users():
                            if not user.bot:
                                users.add(user.id)

                        emoji = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
                        count = reaction.count * 10 - 10
                        txt += f"{emoji}:{count}\n"
                        await self.conn.execute(
                            "UPDATE country SET country_power=country_power+($1) WHERE flag=($2)"
                            , count, emoji)
                    for user in users:
                        await self.conn.execute(
                            "UPDATE country SET country_power=country_power+5 WHERE user_id=($1)"
                            , user)
                        pass
                    await vote_channel.send(txt)
            except Exception:
                print("error")

    @commands.command()
    async def country_rank(self, ctx):
        """国力ランキングを表示をする"""
        power = "国力ランキング:"
        rows = await self.conn.fetch(
            "SELECT flag, country_name, user_id, country_power FROM country ORDER BY country_power DESC"
        )
        for i, row in enumerate(rows):
            user = await self.bot.fetch_user(row['user_id'])
            power += f"\n{i + 1}位|{row['flag']} | {row['country_name']} | {user} | {row['country_power']}pt\n"
        await ctx.send(power)

    @commands.command()
    async def time(self, ctx):
        """時間を表示をする"""
        now = datetime.now().strftime('%H:%M')
        await ctx.send(f"ただいまの時刻:{now}")

    @commands.command()
    async def add_meigen(self, ctx, user: discord.Member, meigen: str):
        """紳士の会メンバーの迷言を追加する"""
        await ctx.send(f"迷言を追加しました。\nメンバー:{user}\n名言:{meigen}")
        print(user.id, meigen)
        await self.conn.execute("INSERT INTO meigen (user_id,text) VALUES (($1),($2))", str(user.id), meigen)

    # TODO:迷言の追加の例外処理を明確にする
    @commands.command()
    async def look_meigen(self, ctx, *args):
        """紳士の会メンバーの迷言を見る"""
        if len(args) == 1:
            if '<@' in args[0]:
                user_id = re.findall('[0-9]+', args[0])
                rows = await self.conn.fetch("SELECT text FROM meigen WHERE user_id=($1)", user_id[0])
                user = await self.bot.fetch_user(user_id[0])
                txt = f"{user}の名言:"
                for row in rows:
                    txt += f"\n{row['text']}\n"
                await ctx.send(txt)
            elif not args[0]:
                await ctx.send("こいつの迷言は無いよ")
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

    @commands.group()
    async def db(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('このコマンドにはサブコマンドが必要です。')

    @db.command()
    async def conn(self, ctx):
        """データベースに再接続する"""
        self.conn = await asyncpg.connect(self.dsn)
        await ctx.send("データベースに接続します")

    @db.command()
    async def close(self, ctx):
        """データベースから切断する"""
        await ctx.send("データベースから切断します")
        await self.conn.close()

    @db.command()
    async def query1(self, ctx, *, query):
        """クエリを実行する"""
        await ctx.send(query)
        await self.conn.execute(query)

    @db.command()
    async def query2(self, ctx, *, query):
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
        await self.conn.execute("UPDATE country SET country_power = 0")

    @commands.command()
    async def add_country(self, ctx, country, flag, player):
        """国家を追加する"""
        await ctx.send(f"国家を追加しました。\n国名:{country}\n国旗:{flag}\nプレイヤーid:{player}")
        await self.conn.execute(
            "INSERT INTO country (country_name, flag, user_id) VALUES (($1), ($2), ($3))", country, flag, player
        )


# Test用クラス(アップデートで追加予定のメソッドも含める)
class Test(commands.Cog):
    def __init__(self, bot, conn):
        self.bot = bot
        self.conn = conn

    # メインとなるroleコマンド
    @commands.group()
    async def role(self, ctx):
        # サブコマンドが指定されていない場合、メッセージを送信する。
        if ctx.invoked_subcommand is None:
            await ctx.send('このコマンドにはサブコマンドが必要です。')

    # roleコマンドのサブコマンド
    # 指定したユーザーに指定した役職を付与する。
    @role.command()
    async def add(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)

    # roleコマンドのサブコマンド
    # 指定したユーザーから指定した役職を剥奪する。
    @role.command()
    async def remove(self, ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)


def setup(bot, dsn):
    bot.add_cog(Bot(bot, dsn))
    bot.add_cog(Administrator(bot, dsn))
    # bot.add_cog(Test(bot, dsn))
