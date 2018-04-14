from paraCH import paraCH
import discord
from datetime import datetime
import asyncio

cmds = paraCH()


class ModEvent:
    """
    TODO: Ticket numbers and stuff.
    """
    actions = {"ban": "User Banned",
               "multi-ban": "Multiple-User Ban",
               "hackban": "User Hackbanned",
               "multi-hackban": "Multiple-User Hackban",
               "kick": "User Kicked",
               "multi-kick": "Users Kicked",
               "unban": "User Unbanned",
               "multi-unban": "Users Unbanned",
               "mute": "User Muted",
               "multi-mute": "Users Muted",
               "unmute": "User Unmuted",
               "multi-unmute": "Users Unmuted",
               "softban": "User Softbanned",
               "multi-softban": "Users Softbanned"}

    def __init__(self, ctx, action, mod, users, reason="None", timeout=0):
        self.ctx = ctx
        self.action = action
        self.mod = mod
        self.users = users
        self.user_strs = ["`{0.name}` (ID: `{0.id}`)".format(user) for user in users]
        self.timeout = timeout
        self.reason = reason
        self.init_time = datetime.utcnow()
        self.embed = None

    async def embedify(self):
        """
        TODO: timeout in sensible form
        """
        embed = discord.Embed(title=self.actions[self.action], color=discord.Colour.red())
        embed.add_field(name="User{}:".format("s" if len(self.users) > 1 else ""), value="\n".join(self.user_strs), inline=False)
        if self.timeout:
            embed.add_field(name="Expires:", value="{} hour{}".format(self.timeout, "s" if self.timeout > 1 else ""), inline=False)
        embed.add_field(name="Reason", value=self.reason, inline=False)
        embed.set_footer(icon_url=self.mod.avatar_url, text=self.init_time.strftime("Acting Moderator: {} at %-I:%M %p, %d/%m/%Y".format(self.mod)))
        self.embed = embed
        return embed

    async def modlog_post(self):
        """
        TODO: When channel is retrieved as a channel, some bits won't be required.
        """
        modlog = await self.ctx.server_conf.modlog_ch.get(self.ctx)
        if not modlog:
            return -1
        modlog = self.ctx.server.get_channel(modlog)
        if not modlog:
            return 2
        if not self.embed:
            await self.embedify()
        try:
            self.modlog_msg = await self.ctx.bot.send_message(modlog,  embed=self.embed)
        except discord.Forbidden:
            return 1
        except Exception:
            return 3
        return 0


async def ban(ctx, user, **kwargs):
    """
    Todo: on rewrite, make this post reason
    """
    ban_reason = kwargs["ban_reason"]
    days = kwargs["days"]
    try:
        await ctx.bot.ban(user, int(days))
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0

async def softban(ctx, user, **kwargs):
    """
    Todo: on rewrite, make this post reason
    """
    ban_reason = kwargs["ban_reason"]
    days = kwargs["days"]
    try:
        await ctx.bot.ban(user, int(days))
        await ctx.bot.unban(ctx.server, user)
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0


async def kick(ctx, user, **kwargs):
    try:
        await ctx.bot.kick(user)
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0

async def unban(ctx, user, **kwargs):
    try:
        await ctx.bot.unban(ctx.server, user)
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0

async def test_action(ctx, user, **kwargs):
    return 0


async def giverole(ctx, role, **kwargs):
    user = kwargs["user"]
    try:
        await ctx.bot.add_roles(user, role)
    except discord.Forbidden:
        return 1
    except Exception:
        return 2
    return 0


async def purge(ctx, user, hours):
    pass

async def role_finder(ctx, user_str, msg):
    role = await ctx.find_role(user_str, interactive=False if hack else True, create=True)
    if role is None:
        if ctx.cmd_err[0] != -1:
            msg = msg + "\t⚠ Couldn't find role `{}`, skipping\n".format(user_str)
        else:
            msg = msg + "\t🗑 Role selection aborted for `{}`, skipping\n".format(user_str)
            ctx.cmd_err = (0, "")
    return (role, msg)

async def member_finder(ctx, user_str, msg, hack=False, collection=None, is_member=True):
    if hack:
        if user_str.isdigit():
            try:
                print(user_str)
                member_info = await ctx.bot.get_user_info(user_str.strip())
            except discord.NotFound:
                msg += "\t⚠ User with id `{}` does not exist, skipping\n".format(user_str)
                return (None, msg)
            member = discord.Object(id=user_str)
            member.server = ctx.server
            member.name = member_info.name
            return (member, msg)
    user = await ctx.find_user(user_str, in_server=True, interactive=True, collection=collection, is_member=is_member)
    if user is None:
        if ctx.cmd_err[0] != -1:
            msg = msg + "\t⚠ Couldn't find user `{}`, skipping\n".format(user_str)
        else:
            msg = msg + "\t🗑 User selection aborted for `{}`, skipping\n".format(user_str)
            ctx.cmd_err = (0, "")
    return (user, msg)

async def user_finder(ctx, user_str, msg):
    user, msg = await member_finder(ctx, user_str, msg, hack=True)
    return (user, msg)

async def ban_finder(ctx, user_str, msg):
    user, msg = await member_finder(ctx, user_str, msg, collection=await ctx.bot.get_bans(ctx.server), is_member=False)
    return (user, msg)

async def role_result(ctx, result, msg, role, **kwargs):
    if result == 0:
        msg += "\tAdded role `{}`".format(role)
    elif result == 1:
        msg += "\tInsufficient permissions to add role `{}`".format(role)
    else:
        msg += "\tUnknown error while adding role `{}`, aborting sequence.".format(role)
        return (1, msg)
    return (0, msg)

async def mod_result(ctx, result, msg, user, **kwargs):
    strings = kwargs["strings"]
    if result in strings["results"]:
        msg += "\t{}".format(strings["results"][result].format(user=user))
        return (0, msg)
    else:
        msg += "\t{}".format(strings["fail_unknown"].format(user=user))
        return (1, msg)



async def multi_action(ctx, user_strs, action, finder, result_func, start_str, **kwargs):
    founds = []
    msg = start_str
    out_msg = await ctx.reply(msg)

    for user_str in user_strs:
        if user_str == "":
            continue
        old_msg = msg
        msg += "\t{}".format(user_str)
        await ctx.bot.edit_message(out_msg, msg)
        found, msg = await finder(ctx, user_str, old_msg)
        if found is None:
            continue
        result = await action(ctx, found, **kwargs)
        code, msg = await result_func(ctx, result, old_msg, found, **kwargs)
        if code:
            break
        if result == 0:
            founds.append(found)
        msg += "\n"
    await ctx.bot.edit_message(out_msg, msg)
    return founds


async def multi_mod_action(ctx, user_strs, action, strings, reason, finder=member_finder, **kwargs):
    users = await multi_action(ctx, user_strs, action, finder, mod_result, strings["start"], strings=strings, reason=reason, **kwargs)
    if len(users) == 0:
        return
    action = strings["action_name"] if len(users) == 1 else strings["action_multi_name"]
    mod_event = ModEvent(ctx, action, ctx.author, users, reason)
    result = await mod_event.modlog_post()
    if result == 1:
        await ctx.reply("I tried to post to the modlog, but lack the permissions!")  # TODO: Offer to repost after modlog works.
    elif result == 2:
        await ctx.reply("I can't see the set modlog channel!")
    elif result == 3:
        await ctx.reply("An unexpected error occurred while trying to post to the modlog.")


async def request_reason(ctx):
    reason = await ctx.input("📋 Please provide a reason! (`no` for no reason or `c` to abort ban)")
    if reason.lower() == "no":
        reason = "None"
    elif reason.lower() == "c":
        await ctx.reply("📋 Aborting!")
        return None
    elif reason is None:
        await ctx.reply("📋 Request timed out, aborting.")
        return None
    return reason


@cmds.cmd("hackban",
          category="Moderation",
          short_help="Hackbans users",
          aliases=["hb"])
@cmds.execute("flags", flags=["r==", "p=", "f"])
@cmds.require("in_server")
@cmds.require("in_server_can_hackban")
async def cmd_hackban(ctx):
    """
    Usage:
        {prefix}hackban <user1> [user2] [user3]... [-r <reason>] [-p <days>] [-f]
    Description:
        Hackbans the users listed with an optional reason.
        Hackbanning allows you to ban without the user being in the server.
        This is not an interactive command, you provide a userid for the users you wish to ban.
    Flags:
        -p:  (purge) Purge <days> days of message history for each user. (Default 1)
        -f:  (fake) Pretends to hackban.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to hackban!")
        return
    reason = ctx.flags["r"]
    purge_days = ctx.flags["p"]
    action_func = test_action if ctx.flags["f"] else ban
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    if not purge_days:
        purge_days = "1"
    if not purge_days.isdigit():
        await ctx.reply("⚠ Number of days to purge must be a number!")
        return
    if int(purge_days) > 7:
        await ctx.reply("⚠ Number of days to purge must be less than 7")
        return
    strings = {"action_name": "hackban",
               "action_multi_name": "multi-hackban",
               "start": "Hackbanning... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error hackbanning `{user.name}` (id: `{user.id}`)! Aborting hackban sequence..."}
    strings["results"] = {0: "🔨 Successfully hackbanned `{user.name}` (id: `{user.id}`)" + (" and purged `{}` days of messages".format(purge_days) if int(purge_days) > 0 else "!"),
                          1: "🚨 Failed to hackban `{user.name}` (id: `{user.id}`)! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason, finder=user_finder, days=int(purge_days), ban_reason="{}: {}".format(ctx.author, reason))

@cmds.cmd("unban",
          category="Moderation",
          short_help="Unbans users")
@cmds.execute("flags", flags=["r=="])
@cmds.require("in_server")
@cmds.require("in_server_can_unban")
async def cmd_unban(ctx):
    """
    Usage:
        {prefix}unban <user1> [user2] [user3]... [-r <reason>]
    Description:
        Unbans the users listed.
        Partial names are supported, and looked up from the ban list.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to hackban!")
        return
    reason = ctx.flags["r"]
    action_func = unban
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    strings = {"action_name": "unban",
               "action_multi_name": "multi-unban",
               "start": "Unbanning... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error unbanning `{user.name}` (id: `{user.id}`)! Aborting unban sequence..."}
    strings["results"] = {0: "🔨 Successfully unbanned `{user.name}` (id: `{user.id}`)!",
                          1: "🚨 Failed to unban `{user.name}` (id: `{user.id}`)! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason, finder=ban_finder, ban_reason="{}: {}".format(ctx.author, reason))

@cmds.cmd("ban",
          category="Moderation",
          short_help="Bans users",
          aliases=["b", "banne", "bean"])
@cmds.execute("flags", flags=["r==", "p=", "f"])
@cmds.require("in_server")
@cmds.require("in_server_can_ban")
async def cmd_ban(ctx):
    """
    Usage:
        {prefix}ban <user1> [user2] [user3]... [-r <reason>] [-p <days>] [-f]
    Description:
        Bans the users listed with an optional reason.
    Flags:
        -p:  (purge) Purge <days> days of message history for each user.
        -f:  (fake) Pretends to ban.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to ban!")
        return
    reason = ctx.flags["r"]
    purge_days = ctx.flags["p"]
    action_func = test_action if ctx.flags["f"] else ban
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    if not purge_days:
        purge_days = "0"
    if not purge_days.isdigit():
        await ctx.reply("⚠ Number of days to purge must be a number!")
        return
    if int(purge_days) > 7:
        await ctx.reply("⚠ Number of days to purge must be less than 7")
        return
    strings = {"action_name": "ban",
               "action_multi_name": "multi-ban",
               "start": "Banning... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error banning `{user.name}`! Aborting ban sequence..."}
    strings["results"] = {0: "🔨 Successfully banned `{user.name}`" + (" and purged `{}` days of messages".format(purge_days) if int(purge_days) > 0 else "!"),
                          1: "🚨 Failed to ban `{user.name}`! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason, days=int(purge_days), ban_reason="{}: {}".format(ctx.author, reason))


@cmds.cmd("softban",
          category="Moderation",
          short_help="Softbans users",
          aliases=["sb"])
@cmds.execute("flags", flags=["r==", "p=", "f"])
@cmds.require("in_server")
@cmds.require("in_server_can_softban")
async def cmd_softban(ctx):
    """
    Usage:
        {prefix}softban <user1> [user2] [user3]... [-r <reason>] [-p <days>] [-f]
    Description:
        Softbans (bans and unbans) the users listed with an optional reason.
    Flags:
        -p:  (purge) Purge <days> days of message history for each user. By default purges 1 day.
        -f:  (fake) Pretends to softban.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to softban!")
        return
    reason = ctx.flags["r"]
    purge_days = ctx.flags["p"]
    action_func = test_action if ctx.flags["f"] else softban
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    if not purge_days:
        purge_days = "1"
    if not purge_days.isdigit():
        await ctx.reply("⚠ Number of days to purge must be a number!")
        return
    if int(purge_days) > 7:
        await ctx.reply("⚠ Number of days to purge must be less than 7")
        return
    strings = {"action_name": "softban",
               "action_multi_name": "multi-softban",
               "start": "Softbanning... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error softbanning `{user.name}`!Aborting ban sequence..."}
    strings["results"] = {0: "🔨 Softbanned `{user.name}`" + " and purged `{}` days of messages!".format(purge_days),
                          1: "🚨 Failed to softban `{user.name}`! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason, days=int(purge_days), ban_reason="{}: {}".format(ctx.author, reason))


@cmds.cmd("kick",
          category="Moderation",
          short_help="Kicks users",
          aliases=["k"])
@cmds.execute("flags", flags=["r==", "f"])
@cmds.require("in_server")
@cmds.require("in_server_can_kick")
async def cmd_kick(ctx):
    """
    Usage:
        {prefix}kick <user1> [user2] [user3]... [-r <reason>] [-f]
    Description:
        Kicks the users listed with an optional reason.
    Flags:
        -f:  (fake) Pretends to kick.
    """
    if ctx.arg_str.strip() == "":
        await ctx.reply("You must give me a user to kick!")
        return
    reason = ctx.flags["r"]
    action_func = test_action if ctx.flags["f"] else kick
    reason = reason if reason else (await request_reason(ctx))
    if not reason:
        return
    strings = {"action_name": "kick",
               "action_multi_name": "multi-kick",
               "start": "Kicking... \n",
               "fail_unknown": "🚨 Encountered an unexpected fatal error kicking `{user.name}`! Aborting kick sequence..."}
    strings["results"] = {0: "🔨 Kicked `{user.name}`!",
                          1: "🚨 Failed to kick `{user.name}`! (Insufficient Permissions)"}
    await multi_mod_action(ctx, ctx.params, action_func, strings, reason)


@cmds.cmd("giverole",
          category="Moderation",
          short_help="Give role(s) to a member",
          aliases=["gr"])
@cmds.require("in_server")
@cmds.require("has_manage_server")
@cmds.execute("user_lookup", in_server=True)
async def cmd_giverole(ctx):
    """
    Usage:
        {prefix}giverole <user> <role1> [role2]...
    Description:
        Gives the specified roles to the provided user.
        Provides a friendlier alternative to {prefix}rolemod.
    Examples:
        {prefix}gr Para Bots root
    """
    if len(ctx.params) < 2:
        await ctx.reply("Please provide a user and at least one role to add!")
        return
    user = ctx.objs["found_user"]
    if not user:
        await ctx.reply("I couldn't find any matching users in this server sorry!")
        return
    await multi_action(ctx, ctx.params[1:], giverole, role_finder, role_result, "Adding Roles to `{}`...\n".format(user.name), user=user)



@cmds.cmd("rolemod",
          category="Moderation",
          short_help="Modify role(s) for member(s)!",
          aliases=["rmod"])
@cmds.require("in_server")
@cmds.require("has_manage_server")
async def cmd_rolemod(ctx):
    """
    Usage:
        {prefix}rolemod <user1> [user2] [user3]... <+|->role1 [<+|->role2]...
    Description:
        Modifies the specified user(s) roles.
        All listed roles must be prefixed with + or -, the roles with + will be added and the roles with - will be removed.
    Example:
        {prefix}rmod Para +Bots -Member
    """
    users = []
    roles = []
    n = len(ctx.params)
    i = 0
    while i < n:
        param = ctx.params[i]
        if param.strip() == "":
            i += 1
            continue
        if param.startswith("+") or param.startswith("-"):
            if len(param) == 1:
                if i < n - 1:
                    obj = ctx.params[i+1]
                    i += 1
                else:
                    break
            else:
                obj = param[1:]
            role = await ctx.find_role(obj, create=True, interactive=True)
            if role is None:
                return
            roles.append((1 if param.startswith("+") else -1, role))
        else:
            users.append(param)
        i += 1
    if len(users) == 0:
        await ctx.reply("No users were given, nothing to do!")
        return
    if len(roles) == 0:
        await ctx.reply("No valid roles were given, nothing to do!")
        return
    error_lines = ""
    intro = "Modifying roles...\n"
    real_users = []
    user_lines = []
    n = len(users)
    out_msg = await ctx.reply(intro)
    for role in roles:
        for i in range(n):
            started = False
            if i >= len(real_users):
                started = True
                user_lines.append("\tIdentifying `{}`".format(users[i]))
                await ctx.bot.edit_message(out_msg, "{}{}{}".format(intro, "\n".join(user_lines), error_lines))
                user = await ctx.find_user(users[i], in_server=True, interactive=True)
                real_users.append(user)
                if user is None:
                    if ctx.cmd_err[0] != -1:
                        user_lines[i] = "\t⚠ Couldn't find user `{}`, skipping".format(users[i])
                    else:
                        user_lines[i] = "\t🗑 User selection aborted for `{}`, skipping".format(users[i])
                        ctx.cmd_err = (0, "")
                    await ctx.bot.edit_message(out_msg, "{}{}{}".format(intro, "\n".join(user_lines), error_lines))
                    continue
            if real_users[i] is None:
                continue
            user = real_users[i]
            if started:
                user_lines[i] = "\tModified user `{}` with: ".format(user)
            try:
                if role[0] > 0:
                    await ctx.bot.add_roles(user, role[1])
                    user_lines[i] += "{}`+{}`".format("" if started else ", ", role[1].name)
                else:
                    await ctx.bot.remove_roles(user, role[1])
                    user_lines[i] += "{}`-{}`".format("" if started else ", ", role[1].name)
            except discord.Forbidden:
                if not error_lines:
                    error_lines = "\nErrors:\n"
                error_lines += ("\tI don't have permissions to {} `{}`!\n".format("add role `{}` to".format(role[1].name) if role[0] > 0 else "remove role `{}` from".format(role[1].name), user))
                await asyncio.sleep(1)
            await ctx.bot.edit_message(out_msg, "{}{}{}".format(intro, "\n".join(user_lines), error_lines))


'''
@cmds.cmd("hackban",
          category="Moderation",
          short_help="Pre-bans users by id")
@cmds.execute("flags", flags=["r=="])
async def cmd_hackban(ctx):
    """
    Usage: {prefix}hackban <userid1> [userid2] [userid3]... [-r <reason>]

    Bans the user ids listed with an optional reason.
    """
    pass
'''
