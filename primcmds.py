'''
    Provides primitive commands.
    Effectively a way of adding functionality while building the full framework.
'''

import discord
import asyncio
import json
import os
import sys
import traceback
from io import StringIO

from parautils import *

#----Primitive Commands setup----
'''
This is for adding basic commands as a proof of concept.
Not intended to be used in production.
'''

#Define permission dictionary
permFuncs = {}

async def perm_default(message, args, client, conf, botdata):
    await reply(client, message, "Sorry, you don't have the required permission. In fact, the required permission isn't defined yet!")
    return 1

def require_perm(permName):
    permName = permName.lower()
    permFunc = permFuncs[permName][0] if permName in permFuncs else perm_default
    def perm_decorator(func):
        async def permed_func(message, cargs, client, conf, botdata, *args, **kwargs):
            error = await permFunc(message, cargs, client, conf, botdata)
            if error == 0:
                await func(message, cargs, client, conf, botdata)
            else:
                await log("Permission failure running command in message \n{}\nFrom user \n{}\nRequired permission \"{}\" which returned error code \"{}\"".format(message.content, message.author.id, permName, error))
            return
        return permed_func
    return perm_decorator

def perm_func(permName):
    def decorator(func):
        permFuncs[permName.lower()] = [func]
        return func
    return decorator

#Initialise command dict
##Entries are indexed by cmdName and contain data described in prim_cmd
primCmds = {}

#Command decorator
def prim_cmd(cmdName, category, desc = "No description", helpDesc = "No help has yet been written for this command."):
    '''
    Decorator wrapper which adds the command to the commands dict so it can be looked up and run.
        cmdName -- Name of the command
        category -- string representing the category, if categorised commands are created
            (e.g. for categorised help)
        desc -- user readable short description for the command
        helpDesc -- user readable help string for the command
    Returns the actual decorator below
    '''
    def decorator(func):
        '''
        Takes in the function, adds it to the cmd dictionary, spits it out again.
        '''
        primCmds[cmdName] = [func, category, desc, helpDesc]
        return func
    return decorator



#----End primitive commands setup---
#------PERMISSION FUNCTIONS------

@perm_func("Master")
async def perm_master(message, cargs, client, conf, botdata):
    if int(message.author.id) not in conf.getintlist("masters"):
        await reply(client, message, "This command requires you to be one of my masters.")
        return 1
    return 0

@perm_func("Exec")
async def perm_exec(message, cargs, client, conf, botdata):
    if (int(message.author.id) not in conf.getintlist("execWhiteList")) and (int(message.author.id) not in conf.getintlist("masters")):
        await reply(client, message, "You don't have the required Exec perms to use this command.")
        return 1
    return 0

#----End permission functions----

#---Helper functions---


#---End helper functions---


#------COMMANDS------

#Primitive Commands

#Bot admin commands
@prim_cmd("restart", "admin")
@require_perm("Master")
async def prim_cmd_restart(message, cargs, client, conf, botdata):
    await reply(client, message, os.system('./Nanny/scripts/redeploy.sh'))

@prim_cmd("setgame", "admin", "Sets my playing status!", "Usage: setgame <status>\n\nSets my playing status to <status>. The following keys may be used:\n\t$users: Number of users I can see.\n\t$servers: Number of servers I am in.\n\t$channels: Number of channels I am in.")
@require_perm("Master")
async def prim_cmd_setgame(message, cargs, client, conf, botdata):
#    current_status = client.servers[0].get_member(client.user.id)
#    await client.change_presence(status=current_status, game = discord.Game(name=cargs))
    status = await para_format(client, cargs, message)
    await client.change_presence(game = discord.Game(name = status))
    await reply(client, message, "Game changed to: \'{}\'".format(status))


@prim_cmd("masters", "admin", "Modify or check the bot masters", "Usage: masters [list] | [+/add | -/remove] <userid/mention>\n\nAdds or removes a bot master by id or mention, or lists all current masters.")
@require_perm("Master")
async def prim_cmd_masters(message, cargs, client, conf, botdata):
    masters = conf.getintlist("masters")
    #TODO: Make this a human readable list of names
    masterNames = ', '.join([str(master) for master in masters])
    params = cargs.split(' ')
    action = params[0]
    if action in ['', 'list']:
        await reply(client, message, "My masters are:\n{}".format(masterNames))
    elif (action in ['+', 'add']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
        userid = int(params[1].strip('<!@>'))
        if userid in masters:
            await reply(client, message, "This user is already one of my masters!")
        else:
            masters.append(userid)
            conf.set("masters", masters)
            await reply(client, message, "I accept this user as a new master.")
    elif (action in ['-', 'remove']) and (len(params) == 2) and params[1].strip('<!@>').isdigit():
        userid = int(params[1].strip('<!@>'))
        if userid not in masters:
            await reply(client, message, "This user is not one of my masters!")
        else:
            masters.remove(userid)
            conf.set("masters", masters)
            await reply(client, message, "I have rejected this master.")
    else:
        await reply(client, message, primCmds["masters"][3])


#TODO: refactor masters to a general list add/check/remove function, add exec config or join commands


@prim_cmd("logs", "admin", "Reads and returns the logs", "Usage: logs [number]\n\nSends the logfile or the last <number> lines of the log.")
@require_perm("Master")
async def prim_cmd_logs(message, cargs, client, conf, botdata):
    logfile = LOGFILE #Getting this from utils at the moment
    params = cargs.split(' ')
    if cargs == '':
        await client.send_file(message.channel, logfile)
    elif params[0].isdigit():
        logs = await tail(logfile, params[0])
        await reply(client, message, "Here are your logs:\n```{}```".format(logs))


#Bot exec commands

async def _async(message, cargs, client, conf, botdata):
    if cargs == '':
        return (primCmds['async'][3], 1)
    env = {'message' : message,
           'args' : cargs,
           'client' : client,
           'conf' : conf,
           'botdata' : botdata,
           'channel' : message.channel,
           'author' : message.author,
           'server' : message.server}
    env.update(globals())
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    exec_string = "async def _temp_exec():\n"
    exec_string += '\n'.join(' ' * 4 + line for line in cargs.split('\n'))
    try:
        exec(exec_string, env)
        result = (redirected_output.getvalue(), 0)
    except Exception:
        traceback.print_exc()
        result = (str(traceback.format_exc()), 2)
    _temp_exec = env['_temp_exec']
    try:
        returnval = await _temp_exec()
        value = redirected_output.getvalue()
        if returnval == None:
            result = (value, 0)
        else:
            result = (value + '\n' + str(returnval), 0)
    except Exception:
        traceback.print_exc()
        result = (str(traceback.format_exc()), 2)
    finally:
        sys.stdout = old_stdout
    return result

@prim_cmd("async", "exec", "Executes async code and shows the output", "Usage: async <code>\n\nRuns <code> as an asyncronous coroutine and prints the output or error.") 
@require_perm("Exec")
async def cmd_async(message, cargs, client, conf, botdata):
    output, error = await _async(message, cargs, client, conf, botdata)
    if error == 1:
        await reply(client, message, output)
    elif error == 2:
        await reply(client, message, "**Async input:**```py\n{}\n```\n**Output (error):**```py\n{}\n```".format(cargs, output))
    else:
        await reply(client, message, "**Async input:**```py\n{}\n```\n**Output:**```py\n{}\n```".format(cargs, output))


async def _exec(message, cargs, client, conf, botdata):
    if cargs == '':
        return (primCmds['exec'][3],1)
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    result = None
    try:
        exec(cargs)
        result = (redirected_output.getvalue(), 0)
    except Exception:
        traceback.print_exc()
        result = (str(traceback.format_exc()), 2)
    finally:
        sys.stdout = old_stdout
    return result

@prim_cmd("exec", "exec", "Executes code and shows the output", "Usage: exec <code>\n\nRuns <code> in current environment using exec() and prints the output or error.") 
@require_perm("Exec")
async def cmd_exec(message, cargs, client, conf, botdata):
    output, error = await _exec(message, cargs, client, conf, botdata)
    if error == 1:
        await reply(client, message, output)
    elif error == 2:
        await reply(client, message, "**Exec input:**```py\n{}\n```\n**Output (error):**```py\n{}\n```".format(cargs, output))
    else:
        await reply(client, message, "**Exec input:**```py\n{}\n```\n**Output:**```py\n{}\n```".format(cargs, output))




#General utility commands


@prim_cmd("about", "general", "Provides information about the bot", "Usage: about\n\nSends a message containing information about the bot.")
async def prim_cmd_about(message, cargs, client, conf, botdata):
    await reply(client, message, 'This is a bot created via the collaborative efforts of Retro, Pue, and Loomy.')
    
@prim_cmd("invite", "general", "Sends the bot's invite link", "Usage: invite\n\nSends the link to invite the bot to your server.")
async def prim_cmd_about(message, cargs, client, conf, userdata):
    await reply(client, message, 'Here\'s my invite link! \n <https://discordapp.com/api/oauth2/authorize?client_id=401613224694251538&permissions=8&scope=bot>')

@prim_cmd("ping", "general", "Checks the bot's latency", "Usage: ping\n\nChecks the response delay of the bot. Usually used to test whether the bot is responsive or not.")
async def prim_cmd_ping(message, cargs, client, conf, botdata):
    sentMessage = await client.send_message(message.channel, 'Beep')
    mainMsg = sentMessage.timestamp
    editedMessage = await client.edit_message(sentMessage,'Boop')
    editMsg = editedMessage.edited_timestamp
    latency = editMsg - mainMsg
    latency = latency.microseconds // 1000
    latency = str(latency)
    await client.edit_message(sentMessage, 'Ping: '+latency+'ms')
    
@prim_cmd("support", "general", "Sends the link to the bot guild", "Usage: support\n\nSends the invite link to the Paradøx support guild.")
async def prim_cmd_about(message, cargs, client, conf, botdata):
    await reply(client, message, 'Join my server here!\n\n<https://discord.gg/ECbUu8u>')

@prim_cmd("help", "general", "Provides some detailed help on a command", "Usage: help [command name]\n\nShows detailed help on the requested command, or lists all the commands.")
async def prim_cmd_help(message, cargs, client, conf, botdata):
    msg = ""
    if cargs == "":
        msg = "```ini\n [ Available Commands: ]\n"
        for cmd in sorted(primCmds):
            msg += "; {}{}:\t{}\n".format(" "*(12-len(cmd)), cmd, primCmds[cmd][2])
        msg += "; This bot is a work in progress. If you have any questions, please ask a developer.\n"
        msg += "```"
    else:
        params = cargs.split(' ')
        for cmd in params:
            if cmd in primCmds:
                msg += "```{}```\n".format(primCmds[cmd][3])
            else:
                msg += "I couldn't find a command named `{}`. Please make sure you have spelled the command correctly. \n".format(cmd)
    await reply(client, message, msg)

@prim_cmd("testembed", "testing", "Sends a test embed.", "Usage: testembed\n\nSends a test embed, what more do you want?")
@require_perm("Exec")
async def prim_cmd_testembed(message, cargs, client, conf, botdata):
    embed = discord.Embed(title = "This is a title", color = discord.Colour.teal()) \
        .set_author(name = "I am an Author") \
        .add_field(name = "This is a field1 title", value = "This is field1 content", inline = True) \
        .add_field(name = "This is a field2 title", value = "This is field2 content", inline = True) \
        .add_field(name = "This is a field3 title", value = "This is field3 content", inline = False) \
        .set_footer(text = "This is a footer")
    await client.send_message(message.channel, embed=embed)


#------END COMMANDS------

