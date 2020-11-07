from settings import GuildSetting, String, ColumnData
from registry import tableInterface, schema_generator, Column, ColumnType

from wards import guild_manager

from .module import guild_admin_module as module


# Define configuration setting
@module.guild_setting
class guild_prefix(ColumnData, String, GuildSetting):
    attr_name = "prefix"
    category = "Guild admin"
    read_check = None
    write_check = guild_manager

    name = "prefix"
    desc = "Custom guild prefix."

    long_desc = ("Command prefix to use instead of the default one. "
                 "Mentions and custom user prefixes will still apply.")

    _maxlen = 10

    _table_interface_name = "guild_prefixes"
    _data_column = "prefix"
    _delete_on_none = True

    @property
    def default(self):
        return self.client.prefix

    def write(self, **kwargs):
        """
        Update guild prefix cache and execute parent writer.
        """
        if self._data:
            self.client.objects["guild_prefix_cache"][self.guildid] = self._data
        else:
            self.client.objects["guild_prefix_cache"].pop(self.guildid, None)

        super().write(**kwargs)

    @classmethod
    def initialise(cls, client):
        """
        Load the custom guild prefixes into cache.
        """
        rows = client.data.guild_prefixes.select_where()
        client.objects["guild_prefix_cache"] = {row['guildid']: row['prefix'] for row in rows}

        client.log("Read {} guilds with custom prefixes.".format(len(rows)),
                   context="LOAD_GUILD_PREFIXES")


# Define data schema
prefix_mysql_schema, prefix_sqlite_schema, prefix_columns = schema_generator(
    "guild_prefixes",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('prefix', ColumnType.SHORTSTRING)
)


# Attach data interface
@module.data_init_task
def attach_prefix_data(client):
    prefix_interface = tableInterface(
        client.data,
        "guild_prefixes",
        app=client.app,
        column_data=prefix_columns,
        shared=False,
        sqlite_schema=prefix_sqlite_schema,
        mysql_schema=prefix_mysql_schema
    )
    client.data.attach_interface(prefix_interface, "guild_prefixes")
