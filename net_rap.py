import discord
import re
from queue import Queue
import asyncio
from discord.ext import tasks, commands
import os
import psycopg2

queue = Queue()
link_regex = re.compile(
    r'https://discord\.com/channels/'
    r'(?:([0-9]{15,21})|(@me))/'
    r'(?P<channel_id>[0-9]{15,21})/'
    r'(?P<message_id>[0-9]{15,21})/?$'
)
link = ""
match = link_regex.match(link)

# ネットライム用class
class rhyme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.verse = -1
        self.count = 0
        self.v_count = 0
        self.time = 0
        self.red_corner = ""
        self.blue_corner = ""
        self.vote_id = 0
    def stop_w(self):
        while not queue.empty():
            queue.get()
        self.verse = 0
        self.count = 0
        self.v_count = 0
        self.red_corner = ""
        self.blue_corner = ""
    @commands.command()
    async def rhyme_battle(self, ctx, *mc):
        if len(mc) == 4 and any(chr.isdigit() for chr in mc[2]) and any(chr.isdigit() for chr in mc[3]):
            self.stop_w()
            mc_id = []
            verse = re.sub(r"\D", "", mc[2])
            time = re.sub(r"\D", "", mc[3])
            self.time = time
            self.verse = int(verse)
            mc_id.append(re.sub(r"\D", "", mc[0]))
            mc_id.append(re.sub(r"\D", "", mc[1]))
            a = await self.bot.fetch_user(mc_id[0])
            b = await self.bot.fetch_user(mc_id[1])
            self.red_corner = a.display_name
            self.blue_corner = b.display_name
            mes = f'赤コーナー:{a.display_name}\nvs\n青コーナー:{b.display_name}\n{verse}verse, 猶予{time}分で行います\n中止は「#stop」、バースは「#verse リリック」で投下してね\nレディー、、、ファイッ!!!'
            await ctx.send(mes)
        else:
            await ctx.send("値が違うようです、、、、構文例:#rhyme_battle A B 3verse 60分")
    @commands.command()
    async def verse(self, ctx, *, verse):
        if self.verse <= 0:
            await ctx.send("ないよぉ！バトルないよぉ！！")
        elif ctx.author.name == self.blue_corner or ctx.author.name == self.red_corner:
            self.v_count += 1
            if ctx.author.name == self.red_corner:
                self.count += 1
                if self.v_count % 2 == 0:
                    self.stop_w()
                    await ctx.send("強制終了")
                    return 0
            elif ctx.author.name == self.blue_corner:
                pass
                if self.v_count % 2 == 1 or self.count == 0:
                    self.stop_w()
                    await ctx.send("強制終了")
                    return 0
            queue.put(verse)
            v = f"{ctx.author.name}:{self.count}verse目"
            await ctx.send(v)
            if self.verse == self.count and ctx.author.name == self.blue_corner:
                text = f"@everyone\n試合終了です！\n{self.red_corner}と{self.blue_corner}、どちらが良かったか投票してください！！"
                message = await ctx.send(text)
                for reaction in ["🔴", "🔵"]:
                    await message.add_reaction(reaction)
                self.vote_id = message.id
                i = 1
                j = 0
                v = "コピー用\n"
                while not queue.empty():
                    if i % 2 == 1:
                        j += 1
                        v += f"{self.red_corner} {j}verse目:\n{queue.get()}\n"
                    else:
                        v += f"{self.blue_corner} {j}verse目:\n{queue.get()}\n"
                    i += 1
                await ctx.send(v)
                self.verse = 0
                self.count = 0
                self.v_count = 0
                await asyncio.sleep(10)
                vote = await ctx.channel.fetch_message(self.vote_id)
                print(vote.reactions)
                vote_result = ""
                for reaction in vote.reactions:
                    vote_result += f"{reaction.emoji} : {reaction.count}\n"
                await message.channel.send(vote_result)
                print(vote.reactions[0].count)
                winner = "@everyone\n"
                if vote.reactions[0].count >= vote.reactions[1].count:
                    winner += f"{self.red_corner}の勝ち"
                else:
                    winner += f"{self.blue_corner}の勝ち"
                await message.channel.send(winner)
                self.red_corner = ""
                self.blue_corner = ""
    """@commands.command()
    async def look_verse(self, ctx):
        self.verse = 0

        if queue.empty():
            await ctx.send("ないよぉ！バースないよぉ！！")
        while not queue.empty():
            v = f"{i}つ目:{queue.get()}"
            await ctx.send(v)
            i += 1"""

    @commands.command()
    async def stop(self, ctx):
        await ctx.send("中止します")
        self.verse = 0
        self.count = 0
        while not queue.empty():
            queue.get()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, ctx):
        if ctx.message_id == self.vote_id:
            print(ctx.channel_id)
            channel = self.bot.get_channel(ctx.channel_id)
            await asyncio.sleep(3600*5)
            a = await channel.fetch_message(self.vote_id)
            print(a)

# sql用class
class sql_com(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    def get_connection(self):
        dsn = os.environ.get('DATABASE_URL')
        return psycopg2.connect(dsn)
    @commands.command()
    async def query(self, ctx, text):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(text)
        rows = cur.fetchall()
        await ctx.send(rows)
        conn.commit()
def setup(bot):
    return bot.add_cog(rhyme(bot))