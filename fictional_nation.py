import asyncpg
import asyncio
from discord.ext import tasks, commands
from datetime import datetime
from os import getenv

# 架空国家用class
class world(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dsn = getenv('DATABASE_URL')
        self.conn = None
        self.loop.start()
        self.flag = []
        self.vote = None

    def cog_unload(self):
        self.loop.cancel()

    # 起動時処理
    @commands.Cog.listener()
    async def on_ready(self):
        print("on_ready")
        self.conn = await asyncpg.connect(self.dsn)
        rows = await self.conn.fetch("SELECT flag FROM country")
        for row in rows:
            self.flag.append(row["flag"])

    # 時間処理
    @tasks.loop(seconds=10)
    async def loop(self):
        now = datetime.now().strftime('%H:%M')
        notice_channel = await self.bot.fetch_channel(853919175406649364)
        vote_channel = await self.bot.fetch_channel(852882836189085697)

        """self.vote = await vote_channel.send('投票を開始します。投票は2国まで可能です。')
        for emoji in self.flag:
            await self.vote.add_reaction(emoji)
        await asyncio.sleep(10)

        vote = await vote_channel.fetch_message(self.vote.id)
        # vote = await vote_channel.fetch_message(971087716878012456)
        print(vote.reactions)
        await vote_channel.send("投票結果:")
        for reaction in vote.reactions:
            emoji = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
            count = reaction.count * 10 - 10
            await self.conn.execute("UPDATE country SET country_power=country_power+($1) WHERE flag=($2)", count,
                                    emoji)
            await vote_channel.send(f"{emoji}:{count}")"""

        # 投票開始
        if now == "00:00":
            self.vote = await vote_channel.send('投票を開始します。投票は2国まで可能です。')
            for emoji in self.flag:
                await self.vote.add_reaction(emoji)

        if now == "07:00":
            await notice_channel.send('おはよう、紳士諸君')
        if now == "12:00":
            await notice_channel.send('紅茶はいかがかね？')
        if now == "23:00":
            await notice_channel.send('おやすみ、紳士諸君')

        # 投票集計
        if now == "23:59":
            vote = await vote_channel.fetch_message(self.vote.id)
            # vote = await vote_channel.fetch_message(971087716878012456)
            print(vote.reactions)
            await vote_channel.send("投票結果:")
            for reaction in vote.reactions:
                emoji = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
                count = reaction.count * 10 - 10
                await self.conn.execute("UPDATE country SET country_power=country_power+($1) WHERE flag=($2)", count,
                                        emoji)
                await vote_channel.send(f"{emoji}:{count}")

    # 国力表示
    @commands.command()
    async def power(self, ctx):
        power = ""
        rows = await self.conn.fetch("SELECT flag, country_name, country_power FROM country")
        await ctx.send("国力一覧")
        for row in rows:
            power += f"{row['flag']}{row['country_name']}:{row['country_power']}\n"
        await ctx.send(power)

    # 再接続
    @commands.command()
    async def db_conn(self, ctx):
        self.conn = await asyncpg.connect(self.dsn)
        await ctx.send("データベースに接続します")

    # 入力クエリ実行
    @commands.command()
    async def db_query1(self, ctx, *, query):
        await ctx.send(query)
        await self.conn.execute(query)

    # 出力クエリ実行
    @commands.command()
    async def db_query2(self, ctx, *, query):
        rows = await self.conn.fetch(query)
        for row in rows:
            await ctx.send(row)

    # 国力リセット
    @commands.command()
    async def reset(self, ctx):
        await ctx.send("国力を初期化します")
        await self.conn.execute("UPDATE country SET country_power = 0")


def setup(bot):
    return bot.add_cog(world(bot))
