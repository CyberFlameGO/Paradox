import discord
import shutil
import os
from datetime import datetime

from botdata import BotData
from botconf import Conf

from contextBot.Context import Context
from contextBot.Bot import Bot

# Global constants/ environment variables

CONF_FILE = "paradox.conf"
BOT_DATA_FILE = "botdata.db"


# Initialise

conf = Conf(CONF_FILE)
botdata = BotData(BOT_DATA_FILE)

PREFIX = conf.get("PREFIX")

LOG_CHANNEL = "428159039831146506"

LOGFILE = "logs/paralog.log"
LOGFILE_LAST = "logs/paralog.last.log"


## Log file

if os.path.isfile(LOGFILE):
    if os.path.isfile(LOGFILE_LAST):
        shutil.move(LOGFILE_LAST, "logs/{}paralog.log".format(datetime.utcnow().strftime("%s")))
    shutil.move(LOGFILE, LOGFILE_LAST)


async def get_prefixes(ctx):
        """
        Returns a list of valid prefixes in this context.
        Currently just bot and server prefixes
        """
        prefix = 0
        prefix_conf = ctx.server_conf.guild_prefix
        if ctx.server:
            prefix = await prefix_conf.get(ctx)
        prefix = prefix if prefix else ctx.bot.prefix
        return [prefix]

bot = Bot(data=botdata,
          bot_conf=conf,
          prefix=PREFIX,
          prefix_func=get_prefixes,
          log_file="logs/paralog.log")

bot.DEBUG = 1


async def log(bot, logMessage):
    print(logMessage)
    with open(bot.LOGFILE, 'a+') as logfile:
        logfile.write(logMessage + "\n")
    ctx = Context(bot=bot)
    log_splits = await ctx.msg_split(logMessage, True)
    for log in log_splits:
        await bot.send_message(discord.utils.get(bot.get_all_channels(), id=LOG_CHANNEL), log)
Bot.log = log

## Loading and initial objects

bot.load("commands", "config", "events", "utils", ignore=["RCS", "__pycache__"])

bot.objects["invite_link"] = "https://discordapp.com/api/oauth2/authorize?bot_id=401613224694251538&permissions=8&scope=bot"
bot.objects["support guild"] = "https://discord.gg/ECbUu8u"
bot.objects["sorted cats"] = ["General",
                              "Fun Stuff",
                              "Social",
                              "Utility",
                              "User info",
                              "Moderation",
                              "Server setup",
                              "Bot admin",
                              "Tex",
                              "Misc"]
bot.objects["sorted_conf_cats"] = ["Guild settings",
                                   "Join message",
                                   "Leave message",
                                   "Moderation"]

# ----Discord event handling----


@bot.event
async def on_ready():
    GAME = conf.getStr("GAME")
    if GAME == "":
        GAME = "in $servers$ servers!"
    GAME = await Context(bot=bot).ctx_format(GAME)
    await bot.change_presence(status=discord.Status.online, game=discord.Game(name=GAME))
    bot.sync_log("Logged in as")
    bot.sync_log(bot.user.name)
    bot.sync_log(bot.user.id)
    bot.sync_log("Logged into {} servers".format(len(bot.servers)))

    ctx = Context(bot=bot)
    with open(LOGFILE, "r") as f:
        log_splits = await ctx.msg_split(f.read(), True)
        for log in log_splits:
            await bot.send_message(discord.utils.get(bot.get_all_channels(), id=LOG_CHANNEL), log)


    bot.objects["emoji_tex_del"] = discord.utils.get(bot.get_all_emojis(), name='delete')
    bot.objects["emoji_tex_show"] = discord.utils.get(bot.get_all_emojis(), name='showtex')
    bot.objects["emoji_bot"] = discord.utils.get(bot.get_all_emojis(), name='parabot')
    bot.objects["emoji_botowner"] = discord.utils.get(bot.get_all_emojis(), name='botowner')
    bot.objects["emoji_botmanager"] = discord.utils.get(bot.get_all_emojis(), name='botmanager')
    bot.objects["emoji_online"] = discord.utils.get(bot.get_all_emojis(), name='ParaOn')
    bot.objects["emoji_idle"] = discord.utils.get(bot.get_all_emojis(), name='ParaIdle')
    bot.objects["emoji_dnd"] = discord.utils.get(bot.get_all_emojis(), name='ParaDND')
    bot.objects["emoji_offline"] = discord.utils.get(bot.get_all_emojis(), name='ParaInvis')



# ----Event loops----
# ----End event loops----


# ----Everything is defined, start the bot!----
bot.run(conf.get("TOKEN"))
