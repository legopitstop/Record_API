# Desc: Setup for the datapack
#
# Called by: #minecraft:load
# tells tick that load file has ran.
tag @a add recordLoad
tag @a add recordTick

# Create scoreboard(s)
scoreboard objectives add record.jukebox minecraft.used:jukebox
scoreboard objectives add record.util dummy
scoreboard objectives add record.creeper dummy
scoreboard objectives add record.stopsound dummy

# Create storage(s)
execute unless data storage record:loot_tables creeper run function record:creeper/register