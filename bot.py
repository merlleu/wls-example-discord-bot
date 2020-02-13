import discord, time, psutil,json

from config import config
import discord
import emotes
from discord.ext import commands
from wlsAPI import wlsAPI, YuniteAPI
# bot = discord.Client()



bot = commands.Bot(command_prefix=config["prefix"], description='wlsbot')
bot_config_version="v0.0.1"

wls=wlsAPI(config['wlsToken'])
yunite=YuniteAPI(config['yunite_token'])
bot.loop.create_task(wls.start())

adminRole=config['adminRole']
verification_channel=config['verification_channel']

def load_config():
    with open(config['eventsFile']) as f:
        return {int(k):v for k,v in json.loads(f.read()).items()}

def save_config():
    with open(config['eventsFile'], 'w') as f:
        return f.write(json.dumps(events))

events = load_config()

@bot.event
async def on_ready():
    # print(dir(bot))
    print(f"Discord Bot online: {bot.user.name}")
    global bot_starttime
    bot_starttime=time.time()


@bot.command()
async def init(ctx, *args):
    if adminRole in [_.id for _ in ctx.message.author.roles]:
        try:
            assert args[0].startswith("<#")
            chan=int(args[0][2:-1])
            if events.get(chan):
                await ctx.send(f"{emotes.nope} **{events.get(chan)['tname']}** is already linked with <#{chan}> .")
                return
            c=await ctx.send(f"{emotes.wlsloading} *Fetching Tournament...*")
            tid=sui(args[1])
            trn=await wls.get_tournament(tid)
            if trn.get("error"):
                await c.edit(content=f"{emotes.nope} Tournament not found.")
                return
            if not await wls.is_organizer(tid):
                await c.edit(content=f"{emotes.nope} You must add `wlsystem` to tournament organizers for tournament **{trn['tournamentName']}**.")
                return
            events[chan]={
            "tid": tid,
            "tname": trn['tournamentName']
            }
            save_config()
            await c.edit(content=f"{emotes.yes} *Success!*\nDashboard URL: https://wls.re/t/#/standings/{tid}/ \nChannel: <#{chan}>")
        except Exception as e:
            await ctx.send(f"{emotes.nope} **[ERROR] > `{e}`**\n`t!init #channel eXXXXXXXXXXXX`\n*(registration chan, tournament id)*")
    return

@bot.command()
async def tournaments(ctx, *args):
    if adminRole in [_.id for _ in ctx.message.author.roles]:
        if events:
            await ctx.send("\n".join(
            [
            f"**{conf['tname']}** <#{chan}> https://wls.re/t/#/standings/{conf['tid']}/"
            for chan, conf in events.items()
            ]
            ))
        else:
            await ctx.send("*0 tournaments.*")

@bot.command()
async def unlink(ctx, *args):
    if adminRole in [_.id for _ in ctx.message.author.roles]:
        try:
            assert args[0].startswith("<#")
            chan=int(args[0][2:-1])
            e=events.get(chan)
            if not e:
                await ctx.send(f"{emotes.warning} There are no tournaments linked with <#{chan}>\n")
                return
            events.pop(chan)
            save_config()
            await ctx.send(f"{emotes.yes} *Success!*\n")
        except Exception as e:
            await ctx.send(f"{emotes.nope} **[ERROR] > `{e}`**\n`t!unlink #channel`\n*(registration chan)*")
    return

@bot.command()
async def join(ctx):
    if events.get(ctx.channel.id):
        await ctx.message.delete()

        e=events[ctx.channel.id]
        yun=await yunite.get_player(ctx.guild.id, ctx.author.id)
        if not yun.get("isLinked"):
            await ctx.send(f"{emotes.nope} <@{ctx.author.id}> You must link your epic account with yunite in <#{verification_channel}>", delete_after=60)
            return
        wusr=await wls.get_player(yun['epicID'])
        if not wusr['found']:
            await ctx.send(f"{emotes.nope} <@{ctx.author.id}> You must link your epic account on WLS: https://wls.re/app/", delete_after=60)
            return

        r=await wls.invite_player(e['tid'], wusr['id'])
        if r.get('error'):
            if r['errorName']=="wls.api.tournament.players.invite.alreadyinvited":
                await ctx.send(f"{emotes.warning} <@{ctx.author.id}> You are already invited in **{e['tname']}**", delete_after=60)
                return
        else:
            await ctx.send(f"{emotes.yes} <@{ctx.author.id}> Welcome !\nYou've been invited, go check-in your team here: https://wls.re/app/play/mytournaments/{e['tid']}/myteam/", delete_after=60)
            return

@bot.command()
async def leave(ctx):
    if events.get(ctx.channel.id):
        await ctx.message.delete()

        e=events[ctx.channel.id]
        yun=await yunite.get_player(ctx.guild.id, ctx.author.id)
        if not yun.get("isLinked"):
            await ctx.send(f"{emotes.nope} <@{ctx.author.id}> You must link your epic account with yunite in <#{verification_channel}>", delete_after=60)
            return
        wusr=await wls.get_player(yun['epicID'])
        if not wusr['found']:
            await ctx.send(f"{emotes.nope} <@{ctx.author.id}> You must link your epic account on WLS: https://wls.re/app/", delete_after=60)
            return

        r=await wls.kick_player(e['tid'], wusr['id'])
        if r.get('error'):
            if r['status']=="notfound":
                await ctx.send(f"{emotes.warning} <@{ctx.author.id}> You aren't invited in  **{e['tname']}**", delete_after=60)
                return
        else:
            if r.get("teamDeleted", False):
                await ctx.send(f"{emotes.yes} <@{ctx.author.id}> See you soon ! Your team has been kicked from **{e['tname']}**", delete_after=60)
            else:
                await ctx.send(f"{emotes.yes} <@{ctx.author.id}> See you soon ! You've been kicked from **{e['tname']}**", delete_after=60)

@bot.command(pass_context=True)
async def botstatus(ctx):
    if adminRole not in [_.id for _ in ctx.message.author.roles]:
        return
    start = time.perf_counter()
    message = await ctx.send('{} PING TEST ...'.format("<a:load:481845463059005441>"))
    end = time.perf_counter()
    await message.delete()
    duration = (end - start) * 100
    second = time.time() - bot_starttime
    minute, second = divmod(second, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)
    week, day = divmod(day, 7)
    await ctx.message.delete()
    embed=discord.Embed(title="{} Bot stats ".format(bot.user.name), color=0xdb4c3c, url="http://warlegend.net")
    embed.set_thumbnail(url="https://i.imgur.com/sUwldjl.png")
    embed.add_field(name="<:server:488095131770028062> Guilds : {} ".format(len(bot.guilds)), value="`{}b s`".format(bot.command_prefix), inline=True)
    embed.add_field(name="<:ping:488095098442350593> Bot latency :", value=("{} ms (ws: {} ms)".format(round(duration), round(bot.latency))), inline=True)
    embed.add_field(name="<:version:488095087470051358> Bot version :", value=bot_config_version, inline=True)
    embed.add_field(name="<:uptime:488095143908343818> Uptime :", value=("%d weeks %d days - %d:%d:%d" % (week, day, hour, minute, second)), inline=True)
    embed.add_field(name="<:cpu:488095070260822044> CPU usage :", value="{} %".format(round(psutil.cpu_percent())), inline=True)
    embed.add_field(name="<:ram:488095117169786895> RAM usage :", value="{} % | {} / {} Mo".format(round(psutil.virtual_memory().percent), round(psutil.virtual_memory().used/1048576), round(psutil.virtual_memory().total/1048576)), inline=True)
    embed.add_field(name="<:cr:488329905126375424> 2020 :", value="<:mrerl:482247934247960587> [@merlleu](https://twitter.com/merlleu)", inline=True)
    embed.set_footer(text="{} Powered by @merlleu ".format(bot.user.name), icon_url="https://cdn.discordapp.com/emojis/483430094673674241.png?v=1")
    await ctx.send(embed=embed)




sui_fbd=["<", ">", "'", '"', "`", "\\", "/"]
def sui(input):
    return ''.join(filter(lambda x: (x not in sui_fbd), input))

bot.run(config['token'])
