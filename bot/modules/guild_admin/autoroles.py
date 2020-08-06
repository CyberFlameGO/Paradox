import logging
import discord
from cmdClient import cmdClient

from logger import log
from settings import ListData, RoleList, GuildSetting
from registry import tableInterface, Column, ColumnType, schema_generator

from .module import guild_admin_module as module


# Define guild settings
@module.guild_setting
class autoroles(ListData, RoleList, GuildSetting):
    attr_name = "autoroles"
    category = "Guild admin"

    name = "autoroles"
    desc = "Roles automatically given to new members."

    long_desc = "Roles automatically given to new members when they join the guild."

    _table_interface_name = "guild_autoroles"
    _data_column = "roleid"


@module.guild_setting
class bot_autoroles(ListData, RoleList, GuildSetting):
    attr_name = "bot_autoroles"
    category = "Guild admin"

    name = "bot_autoroles"
    desc = "Roles automatically given to new bots."

    long_desc = "Roles automatically given to new bots when they join the guild."

    _table_interface_name = "guild_bot_autoroles"
    _data_column = "roleid"


# Define event handler
async def give_autoroles(client: cmdClient, member: discord.Member):
    # Get the autoroles from storage
    if member.bot:
        autoroles = client.guild_config.bot_autoroles(client, member.guild.id).value
    else:
        autoroles = client.guild_config.autoroles(client, member.guild.id).value

    # Add the autoroles, if we can
    if autoroles and member.guild.me.guild_permissions.manage_roles:
        # Retrieve my top role with manage role permissions
        my_mr_roles = [role for role in member.guild.me.roles
                       if role.permissions.manage_roles or role.permissions.administrator]

        # Filter autoroles based on what I have permission to add
        if my_mr_roles:
            max_mr_role = max(my_mr_roles)
            autoroles = [role for role in autoroles if role < max_mr_role]
        else:
            autoroles = None

        # Add the roles if there are any left
        if autoroles:
            try:
                await member.add_roles(*autoroles, reason="Adding autoroles")
            except Exception as e:
                log("Failed to add autoroles to new member '{}' (uid:{}) in guild '{} (gid:{})."
                    " Exception: {}".format(member,
                                            member.id,
                                            member.guild.name,
                                            member.guild.id,
                                            e.__repr__()),
                    context="GIVE_AUTOROLE",
                    level=logging.WARNING)


# Register event handler
@module.init_task
def attach_autorole_handler(client: cmdClient):
    client.add_after_event("member_join", give_autoroles)


# Define data schemas
ar_mysql_schema, ar_sqlite_schema, ar_columns = schema_generator(
    "guild_autoroles",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('roleid', ColumnType.SNOWFLAKE, primary=True, required=True)
)

bar_mysql_schema, bar_sqlite_schema, bar_columns = schema_generator(
    "guild_bot_autoroles",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('roleid', ColumnType.SNOWFLAKE, primary=True, required=True)
)


# Attach data interfaces
@module.data_init_task
def attach_autorole_data(client):
    autorole_interface = tableInterface(
        client.data,
        "guild_autoroles",
        app=client.app,
        column_data=ar_columns,
        shared=False,
        sqlite_schema=ar_sqlite_schema,
        mysql_schema=ar_mysql_schema,
    )
    client.data.attach_interface(autorole_interface, "guild_autoroles")

    bot_autorole_interface = tableInterface(
        client.data,
        "guild_bot_autoroles",
        app=client.app,
        column_data=bar_columns,
        shared=False,
        sqlite_schema=bar_sqlite_schema,
        mysql_schema=bar_mysql_schema
    )
    client.data.attach_interface(bot_autorole_interface, "guild_bot_autoroles")