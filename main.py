import asyncio
import math
import os
import re
from typing import Optional, Literal
import logging

import pytz
from discord import app_commands, Embed
from discord.app_commands import Choice
from discord.ext import commands, tasks
import discord

from dotenv import load_dotenv

from localtime import midnight, days_in_the_past
import datetime
from octopus import OctopusSettings

load_dotenv()

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

logging.basicConfig(level=logging.DEBUG)

logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('octopus').setLevel(logging.DEBUG)


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object],
               spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


class MainCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = OctopusSettings()
        self.octopus = self.settings.get_octopus()

    @staticmethod
    # validate format
    async def validate_date(date: str, ctx: commands.Context) -> Optional[datetime.datetime]:
        if not re.match(r"\d{4}-\d{2}-\d{2}", date):
            await ctx.send("Invalid date format. Use `YYYY-MM-DD`.")
            return
        return datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.timezone("Asia/Tokyo"))

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send('Pong!')

    @commands.hybrid_command(
        name="info",
        description="Get Account Information.",
    )
    async def info(self, ctx: commands.Context) -> None:
        embed = Embed(
            title="Info",
        )
        status = await self.octopus.check_auth()
        if status:
            account_number = await self.octopus.get_account_number()
            embed.add_field(
                name="供給地点識別番号",
                value=account_number,
            )
        else:
            embed.add_field(
                name="認証に失敗しました",
                value="Failed to authenticate",
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="usage",
        description="指定した期間の電気使用量を取得します。期間を指定しない場合は過去7日間のデータを取得します。",
    )
    @app_commands.describe(
        start_at="取得する期間の開始日。ハイフン区切りで指定します。(例:2024-01-01)",
        end_at="取得する期間の終了日時。指定しない場合は開始日時から最新のデータまで取得します。",
    )
    async def usage(self, ctx: commands.Context, start_at: Optional[str] = None, end_at: Optional[str] = None) -> None:

        if start_at is None and end_at is None:
            start_at = midnight(days_in_the_past(7))
            end_at = midnight()
        elif end_at is None:
            start_at = await self.validate_date(start_at, ctx)
            end_at = midnight()
        else:
            start_at = await self.validate_date(start_at, ctx)
            end_at = await self.validate_date(end_at, ctx)

        readings = await self.octopus.get_hh_readings(start_at, end_at)
        embed = Embed(
            # title=":zap: 使用量",
            color=0xffff00,
        )
        total = math.fsum([reading.value for reading in readings])
        embed.add_field(
            name="合計",
            value=f"{total} kWh",
        )
        embed.set_footer(
            text="{} から {} までのデータ".format(
                readings[0].start_at.strftime("%Y-%m-%d %H:%M"),
                readings[-1].end_at.strftime("%Y-%m-%d %H:%M"),
            ),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="compare",
        description="指定した期間の電気使用量を比較して表示します。デフォルトでは過去7日間その前の7日間のデータを比較します。",
    )
    @app_commands.describe(
        start_at1="取得する期間の開始日。ハイフン区切りで指定します。(例:2024-01-01)",
        end_at1="取得する期間の終了日時。指定しない場合は開始日時から最新のデータまで取得します。",
        start_at2="取得する期間の開始日。ハイフン区切りで指定します。(例:2024-01-01)",
        end_at2="取得する期間の終了日時。指定しない場合は開始日時から最新のデータまで取得します。",
    )
    async def compare(self, ctx: commands.Context, start_at1: Optional[str] = None, end_at1: Optional[str] = None,
                      start_at2: Optional[str] = None, end_at2: Optional[str] = None) -> None:
        # validate format
        async def validate_date(date: str) -> Optional[datetime.datetime]:
            if not re.match(r"\d{4}-\d{2}-\d{2}", date):
                await ctx.send("Invalid date format. Use `YYYY-MM-DD`.")
                return
            return datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.timezone("Asia/Tokyo"))

        async def validate_order(start: datetime, end: datetime) -> Optional[
            tuple[datetime.datetime, datetime.datetime]]:
            if start > end:
                await ctx.send("Invalid date order.")
                return
            return start, end

        await ctx.interaction.response.defer()

        if all(d is None for d in [start_at1, end_at1, start_at2, end_at2]):
            start_at1 = midnight(days_in_the_past(14))
            end_at1 = midnight(days_in_the_past(7))
            start_at2 = midnight(days_in_the_past(7))
            end_at2 = midnight()
        else:
            start_at1, end_at1 = await validate_order(await validate_date(start_at1), await validate_date(end_at1))
            start_at2, end_at2 = await validate_order(await validate_date(start_at2), await validate_date(end_at2))

        readings1, readings2 = await asyncio.gather(
            self.octopus.get_hh_readings(start_at1, end_at1),
            self.octopus.get_hh_readings(start_at2, end_at2),
        )

        total1 = math.fsum([reading.value for reading in readings1])
        total2 = math.fsum([reading.value for reading in readings2])

        embed = Embed(
            # title=":zap: 使用量比較",
            color=0xffff00,
        )
        embed.add_field(
            name="使用量比較",
            value=f"期間1は期間2より**{round(total1 - total2, 1)} kWh**多いです。"
            if total1 > total2 else f"期間1は期間2より**{round(total2 - total1, 1)} kWh**少ないです。",
            inline=False,
        )
        embed.add_field(
            name="期間1",
            value=f"**{round(total1, 1)} kWh**",
        )
        embed.add_field(
            name="期間2",
            value=f"**{round(total2, 1)} kWh**",
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="day",
        description="指定した日の電気使用量を取得します。デフォルトでは昨日のデータを取得します。",
    )
    @app_commands.describe(
        date="取得する日。ハイフン区切りで指定します。(例:2024-01-01)",
    )
    async def day(self, ctx: commands.Context, date: Optional[str] = None) -> None:

        if date is None:
            date = midnight(days_in_the_past(1))
        else:
            date = await self.validate_date(date, ctx)

        readings = await self.octopus.get_hh_readings(date, midnight(date) + datetime.timedelta(days=1))
        embed = Embed(
            # title=":zap: 使用量",
            color=0xffff00,
        )
        total = math.fsum([reading.value for reading in readings])
        embed.add_field(
            name="合計",
            value=f"{total} kWh",
        )
        embed.set_footer(
            text="{} のデータ".format(
                readings[0].start_at.strftime("%Y-%m-%d %H:%M"),
            ),
        )
        await ctx.send(embed=embed)


async def main():
    await bot.add_cog(MainCog(bot))
    await bot.start(os.getenv('TOKEN'))


asyncio.run(main())
