# Migration from v1 to v2
Continuing the migration from the `key-value` property tables to individual data tables.

This version migrates the following features:
* starboard

# Migration operation
Apply the `mysql-schema.sql` or `sqlite-schema.sql` script to the database, as required.
The `sqlite` migration script does not migrate the old data, only updating the version and creating the new tables.


# Description of each of the properties in the v0 property tables, and subsequent action
Unless explicitly stated, value data is encoded by `json.dumps()` and may be reloaded into the actual values described below by `json.loads()`.

## `servers` table
* `starboard_emoji`
    * Property name: `starboard_emoji`
    * Application: `paradox`
    * Type: `str`
    * Description: The string form of the starboard emoji
    * Parse as: `string`
    * Action
        * Target table: `guild_starboard`
        * Insert type: `upsert`
        * Upsert constraint: `(app, guildid)`
        * Insert keymap: `{'guildid': 'row.serverid', 'emoji': 'row.value', 'app': 'paradox'}`

* `texit_starboard_emoji`
    * Property name: `starboard_emoji`
    * Application: `texit`
    * Type: `str`
    * Description: The string form of the starboard emoji
    * Parse as: `string`
    * Action
        * Target table: `guild_starboard`
        * Insert type: `upsert`
        * Upsert constraint: `(app, guildid)`
        * Insert keymap: `{'guildid': 'row.serverid', 'emoji': 'row.value', 'app': 'texit'}`

* `starboard_channel`
    * Property name: `starboard_channel`
    * Application: `paradox`
    * Type: `str` or literal `null`
    * Description: The channel to send starred messages.
    * Note: Only migrated if the corresponding `starboard_enabled` property is `True`.
    * Parse as: `id`
    * Action
        * Target table: `guild_starboard`
        * Insert type: `upsert`
        * Upsert constraint: `(app, guildid)`
        * Insert keymap: `{'guildid': 'row.serverid', 'channelid': 'row.value', 'app': 'paradox'}`

* `texit_starboard_channel`
    * Property name: `starboard_channel`
    * Application: `texit`
    * Type: `str` or literal `null`
    * Description: The channel to send starred messages.
    * Note: Only migrated if the corresponding `texit_starboard_enabled` property is `True`.
    * Parse as: `id`
    * Action
        * Target table: `guild_starboard`
        * Insert type: `upsert`
        * Upsert constraint: `(app, guildid)`
        * Insert keymap: `{'guildid': 'row.serverid', 'channelid': 'row.value', 'app': 'texit'}`

* `starboard_enabled`
    * Property name: `starboard_enabled`
    * Application: `paradox`
    * Type: `bool`
    * Description: Whether the starboard is enabled or not
    * Note: Taken into account as part of the `starboard_channel` migration.
    * Parse as: `boolean`
    * Action
        * Not to be migrated

* `texit_starboard_enabled`
    * Property name: `starboard_enabled`
    * Application: `texit`
    * Type: `bool`
    * Description: Whether the starboard is enabled or not
    * Note: Taken into account as part of the `texit_starboard_channel` migration.
    * Parse as: `boolean`
    * Action
        * Not to be migrated

* `starboard_threshold`
    * Property name: `starboard_threshold`
    * Application: `None`
    * Type: `int`
    * Description: The number of reactions to wait for before considering a message starred
    * Parse as: `integer`
    * Action
        * Target table: `guild_starboard`
        * Insert type: `upsert`
        * Upsert constraint: `(app, guildid)`
        * Insert keymap: `[{'guildid': 'row.serverid', 'threshold': 'row.value', 'app': 'paradox'}, {'guildid': 'row.serverid', 'threshold': 'row.value', 'app': 'texit'}]`
