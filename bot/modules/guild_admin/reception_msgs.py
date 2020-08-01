import logging
import discord
from cmdClient import cmdClient

from logger import log
from settings import ColumnData, String, Channel, GuildSetting
from registry import tableInterface, Column, ColumnType, schema_generator

from .module import guild_admin_module as module


# Define guild settings
@module.guild_setting
class greeting_channel(ColumnData, Channel, GuildSetting):
    attr_name = "greeting_channel"
    category = "Greeting message"

    name = "greeting_ch"
    desc = "Channel in which to greet new members."

    long_desc = "Channel in which to send the greeting message when a new member joins."

    _table_interface_name = "guild_greetings"
    _data_column = "channelid"
    _delete_on_none = False


@module.guild_setting
class greeting_message(ColumnData, String, GuildSetting):
    attr_name = "greeting_message"
    category = "Greeting message"

    name = "greeting"
    desc = "Greeting message for new members."

    long_desc = ("Message to send to the greeting channel when new members join. "
                 "The following keys will be substituted for their values: "
                 "`{name}`, `{mention}`, `{guildname}`.")

    _default = "Hi {mention}, welcome to {guildname}! We hope you have a pleasant stay."

    _maxlen = 2000

    _table_interface_name = "guild_greetings"
    _data_column = "message"
    _delete_on_none = False

    def format_greeting_for(self, member):
        if self.data is None:
            return None
        else:
            resp = self.data
            resp = resp.replace("{name}", discord.utils.escape_mentions(member.name))
            resp = resp.replace("{guildname}", member.guild.name)
            resp = resp.replace("{mention}", member.mention)
            return resp


@module.guild_setting
class farewell_channel(ColumnData, Channel, GuildSetting):
    attr_name = "farewell_channel"
    category = "Farewell message"

    name = "farewell_ch"
    desc = "Channel in which to to say farewell to leaving members."

    long_desc = "Channel in which to send the farewell message after a member leaves."

    _table_interface_name = "guild_farewells"
    _data_column = "channelid"
    _delete_on_none = False


@module.guild_setting
class farewell_message(ColumnData, String, GuildSetting):
    attr_name = "farewell_message"
    category = "Farewell message"

    name = "farewell"
    desc = "Farewell message for members who have left."

    long_desc = ("Message to send to the farewell channel after members leave. "
                 "The following keys will be substituted for their values: "
                 "`{name}`, `{nickname}`, `{guildname}`.")

    _default = "Farewell {nickname}! Take care."

    _maxlen = 2000

    _table_interface_name = "guild_farewells"
    _data_column = "message"
    _delete_on_none = False

    def format_farewell_for(self, member):
        if self.data is None:
            return None
        else:
            resp = self.data
            resp = resp.replace("{name}", discord.utils.escape_mentions(member.name))
            resp = resp.replace("{guildname}", member.guild.name)
            resp = resp.replace("{nickname}", member.display_name)
            return resp


# Define event handlers
async def send_greeting(client, member):
    if member.bot:
        return

    greeting_ch = client.guild_config.greeting_channel.get(client, member.guild.id).value
    if not greeting_ch:
        return

    greeting_msg = client.guild_config.greeting_message.get(client, member.guild.id).format_greeting_for(member)
    if not greeting_msg:
        return

    try:
        await greeting_ch.send(greeting_msg)
    except discord.Forbidden:
        pass
    except Exception as e:
        log("Failed to greet member '{}' (uid:{}) in guild '{} (gid:{})."
            " Exception: {}".format(member,
                                    member.id,
                                    member.guild.name,
                                    member.guild.id,
                                    e.__repr__()),
            context="SEND_GREETING",
            level=logging.WARNING)


async def send_farewell(client, member):
    if member.bot:
        return

    farewell_ch = client.guild_config.farewell_channel.get(client, member.guild.id).value
    if not farewell_ch:
        return

    farewell_msg = client.guild_config.farewell_message.get(client, member.guild.id).format_farewell_for(member)
    if not farewell_msg:
        return

    try:
        await farewell_ch.send(farewell_msg)
    except discord.Forbidden:
        pass
    except Exception as e:
        log("Failed to farewell member '{}' (uid:{}) in guild '{} (gid:{})."
            " Exception: {}".format(member,
                                    member.id,
                                    member.guild.name,
                                    member.guild.id,
                                    e.__repr__()),
            context="SEND_FAREWELL",
            level=logging.WARNING)


@module.init_task
def attach_reception_handlers(client: cmdClient):
    client.add_after_event("member_join", send_greeting)
    client.add_after_event("member_leave", send_farewell)


# Define data schemas
greeting_mysql_schema, greeting_sqlite_schema, greeting_columns = schema_generator(
    "guild_greetings",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('channelid', ColumnType.SNOWFLAKE),
    Column('message', ColumnType.TEXT)
)

farewell_mysql_schema, farewell_sqlite_schema, farewell_columns = schema_generator(
    "guild_farewells",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('channelid', ColumnType.SNOWFLAKE),
    Column('message', ColumnType.TEXT)
)


# Attach data interfaces
@module.data_init_task
def attach_reception_data(client):
    greeting_interface = tableInterface(
        client.data,
        "guild_greetings",
        app=client.app,
        column_data=greeting_columns,
        shared=False,
        sqlite_schema=greeting_sqlite_schema,
        mysql_schema=greeting_mysql_schema
    )
    client.data.attach_interface(greeting_interface, "guild_greetings")

    farewell_interface = tableInterface(
        client.data,
        "guild_farewells",
        app=client.app,
        column_data=farewell_columns,
        shared=False,
        sqlite_schema=farewell_sqlite_schema,
        mysql_schema=farewell_mysql_schema
    )
    client.data.attach_interface(farewell_interface, "guild_farewells")
