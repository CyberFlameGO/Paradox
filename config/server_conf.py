from contextBot.Conf import Conf
from paraSetting import paraSetting
import settingTypes

server_conf = Conf("s_conf")

# TODO can do the write check with what's


class Server_Setting(paraSetting):
    long_setting = False  # Whether the setting is stored as a long string or not
    @classmethod
    async def read(cls, ctx):
        if cls.long_setting:
            value = await ctx.data.servers_long.get(ctx.server.id, cls.name)
        else:
            value = await ctx.data.servers.get(ctx.server.id, cls.name)
        return value

    @classmethod
    async def write(cls, ctx, value):
        (code, msg) = await ctx.CH.checks["in_server_has_mod"](ctx)
        if code != 0:
            ctx.cmd_err = (code, msg)
            return
        if cls.long_setting:
            return await ctx.data.servers_long.set(ctx.server.id, cls.name, value)
        else:
            return await ctx.data.servers.set(ctx.server.id, cls.name, value)


@server_conf.setting
class Server_Setting_Prefix(Server_Setting, settingTypes.STR):
    name = "guild_prefix"
    vis_name = "prefix"
    desc = "Custom server prefix"
    category = "Guild settings"

    @classmethod
    async def dyn_default(cls, ctx):
        return ctx.bot.prefix


@server_conf.setting
class Server_Setting_Starboard(Server_Setting, settingTypes.BOOL):
    name = "starboard_enabled"
    vis_name = "starboard"
    desc = "Enable/Disable Starboard"
    category = "Starboard"
    default = False

    outputs = {True: "Enabled",
               False: "Disabled"}

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        if ctx.cmd_err[0]:
            return result
        starboards = ctx.bot.objects["server_starboard_emojis"]
        if value:
            starboards[ctx.server.id] = await ctx.server_conf.starboard_emoji.get(ctx)
            ctx.bot.objects["server_starboards"][ctx.server.id] = {}
        else:
            starboards.pop(ctx.server.id, None)
        return result


@server_conf.setting
class Server_Setting_StarChan(Server_Setting, settingTypes.CHANNEL):
    name = "starboard_channel"
    vis_name = "star_channel"
    desc = "Starboard channel"
    category = "Starboard"
    default = None

@server_conf.setting
class Server_Setting_StarThresh(Server_Setting, settingTypes.INT):
    name = "starboard_threshold"
    vis_name = "star_threshold"
    desc = "Minimum stars a message must have to be posted in the starboard channel"
    category = "Starboard"
    default = 2

@server_conf.setting
class Server_Setting_StarEmoji(Server_Setting, settingTypes.EMOJI):
    name = "starboard_emoji"
    vis_name = "star_emoji"
    desc = "Starboard emoji"
    category = "Starboard"
    default = "⭐"

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        if ctx.cmd_err[0]:
            return result
        starboards = ctx.bot.objects["server_starboard_emojis"]
        if ctx.server.id in starboards:
            starboards[ctx.server.id] = value if value else cls.default
        return result


@server_conf.setting
class Server_Setting_Autorole(Server_Setting, settingTypes.ROLE):
    name = "guild_autorole"
    vis_name = "autorole"
    desc = "Role automatically given to new members"
    category = "Guild settings"
    default = "0"


@server_conf.setting
class Server_Setting_Autoroles(Server_Setting, settingTypes.ROLELIST):
    name = "guild_autoroles"
    vis_name = "autoroles"
    desc = "Roles automatically given to new members"
    category = "Hidden Guild settings"
    default = "0"


@server_conf.setting
class Server_Setting_Autorole_Bot(Server_Setting, settingTypes.ROLE):
    name = "guild_autorole_bot"
    vis_name = "autorole_bot"
    desc = "Role automatically given to new bots. By default same as autorole."
    category = "Guild settings"

    @classmethod
    async def dyn_default(cls, ctx):
        return await ctx.server_conf.guild_autorole.get(ctx)


@server_conf.setting
class Server_Setting_selfroles(Server_Setting, settingTypes.ROLELIST):
    name = "self_roles"
    vis_name = "selfroles"
    desc = "Roles which users can give themselves with giveme command"
    default = None
    category = "Guild settings"
    long_setting = True


@server_conf.setting
class Server_Setting_Clean_Channels(Server_Setting, settingTypes.CHANNELLIST):
    name = "clean_channels"
    vis_name = "clean_channels"
    desc = "Automatically delete new messages in these channels."
    category = "Guild settings"
    default = None

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        cleaned = ctx.bot.objects["cleaned_channels"]
        if (ctx.cmd_err and ctx.cmd_err[0] != 0):
            return
        cleaned[ctx.server.id] = value if value else []
        return result

# Moderation settings


@server_conf.setting
class Server_Setting_modrole(Server_Setting, settingTypes.ROLE):
    name = "mod_role"
    vis_name = "modrole"
    desc = "Role required to use moderation commands"
    default = None
    category = "Moderation"


@server_conf.setting
class Server_Setting_role_persistence(Server_Setting, settingTypes.BOOL):
    name = "role_persistence"
    vis_name = "roles_persist"
    desc = "Whether roles are re-added when a user leaves and rejoins."
    default = True
    category = "Moderation"

    outputs = {True: "Enabled",
               False: "Disabled"}


@server_conf.setting
class Server_Setting_mute_role(Server_Setting, settingTypes.ROLE):
    name = "mute_role"
    vis_name = "mute_role"
    desc = "Role given to mute users (automatically set, but can be overridden)"
    default = None
    category = "Moderation"


@server_conf.setting
class Server_Setting_Channel_Blacklist(Server_Setting, settingTypes.CHANNELLIST):
    name = "channel_blacklist"
    vis_name = "channel_blacklist"
    desc = "Disable non-moderator command responses in these channels."
    category = "Guild settings"
    default = None

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        blacklist = ctx.bot.objects["channel_blacklists"]
        if (ctx.cmd_err and ctx.cmd_err[0] != 0):
            return
        blacklist[ctx.server.id] = value if value else []
        return result

# Logging settings


@server_conf.setting
class Server_Setting_modlog_ch(Server_Setting, settingTypes.CHANNEL):
    name = "modlog_ch"
    vis_name = "modlog"
    desc = "Channel to report moderation events in"
    default = None
    category = "Logging"


@server_conf.setting
class Server_Setting_joinlog_ch(Server_Setting, settingTypes.CHANNEL):
    name = "joinlog_ch"
    vis_name = "joinlog"
    desc = "Channel to send information about users joining and leaving"
    default = None
    category = "Logging"


@server_conf.setting
class Server_Setting_userlog_ch(Server_Setting, settingTypes.CHANNEL):
    name = "userlog_ch"
    vis_name = "userlog"
    desc = "Channel to send information about user updates."
    default = None
    category = "Logging"


@server_conf.setting
class Server_Setting_userlog_events(Server_Setting, settingTypes.USEREVENTLIST):
    name = "userlog_events"
    vis_name = "userlog_events"
    desc = "Which events to log in the userlog"
    default = ["username", "nickname", "avatar", "roles"]
    category = "Logging"


@server_conf.setting
class Server_Setting_userlog_ignore(Server_Setting, settingTypes.MEMBERLIST):
    name = "userlog_ignore"
    vis_name = "userlog_ignore"
    desc = "List of users ignored by userlog."
    default = None
    category = "Logging"

# Join and leave message settings


@server_conf.setting
class Server_Setting_Join_Msg(Server_Setting, settingTypes.FMTSTR):
    name = "join_msgs_msg"
    vis_name = "join_msg"
    desc = "Join message"
    default = "Give a warm welcome to $mention$!"
    category = "Join message"
    long_setting = True


@server_conf.setting
class Server_Setting_Join_Ch(Server_Setting, settingTypes.CHANNEL):
    name = "join_ch"
    vis_name = "join_ch"
    desc = "Channel to post in when a user joins"
    default = None
    category = "Join message"


@server_conf.setting
class Server_Setting_Leave_Msg(Server_Setting, settingTypes.FMTSTR):
    name = "leave_msgs_msg"
    vis_name = "leave_msg"
    desc = "Leave message"
    default = "Goodbye $username$, we hope you had a nice stay!"
    category = "Leave message"
    long_setting = True


@server_conf.setting
class Server_Setting_Leave_Ch(Server_Setting, settingTypes.CHANNEL):
    name = "leave_ch"
    vis_name = "leave_ch"
    desc = "Channel to post in when a user leaves"
    default = None
    category = "Leave message"


# Maths related settings

@server_conf.setting
class Server_Setting_Latex_Listen(Server_Setting, settingTypes.BOOL):
    name = "latex_listen_enabled"
    vis_name = "latex"
    desc = "Enables/Disables listening for LaTeX messages"
    default = False
    category = "Mathematical settings"

    outputs = {True: "Enabled",
               False: "Disabled"}

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        listens = ctx.bot.objects["server_tex_listeners"]
        if not (ctx.cmd_err and ctx.cmd_err[0] != 0):
            if value:
                channels = await ctx.bot.data.servers.get(ctx.server.id, "maths_channels")
                listens[str(ctx.server.id)] = channels if channels else []
            else:
                listens.pop(ctx.server.id)
        return result


@server_conf.setting
class Server_Setting_Maths_Channels(Server_Setting, settingTypes.CHANNELLIST):
    name = "maths_channels"
    vis_name = "latex_channels"
    desc = "Only listen to LaTeX in these channels, if set"
    category = "Mathematical settings"
    default = None

    @classmethod
    async def humanise(cls, ctx, raw):
        if not raw:
            return "All channels"
        return await super().humanise(ctx, raw)

    @classmethod
    async def write(cls, ctx, value):
        result = await super().write(ctx, value)
        listens = ctx.bot.objects["server_tex_listeners"]
        if (ctx.cmd_err and ctx.cmd_err[0] != 0):
            return
        listens[ctx.server.id] = value if value else []
        return result


def load_into(bot):
    bot.add_to_ctx(server_conf, name="server_conf")
    bot.s_conf = server_conf
    bot.settingTypes = settingTypes
