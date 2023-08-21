# Made by: @Legopitstop
# Desc: Uninstalls this datapack
#
# Called By: Player

# Disable the datapack from the world
datapack disable "file/Record API [datapack] v1.2.0"
datapack disable "file/Record API [datapack] v1.2.0.zip"

# Scoreboard(s)
scoreboard objectives remove record.jukebox
scoreboard objectives remove record.util
scoreboard objectives remove record.creeper
scoreboard objectives remove record.stopsound

# Storage(s)
data remove storage record:loot_tables creeper
data remove storage record:loot_tables total_creeper

# Tag(s)
tag @a remove recordLoad
tag @a remove recordTick

