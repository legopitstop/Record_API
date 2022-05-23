# Desc: Setup for the datapack
#
# Called by: #minecraft:load
# tells tick that load file has ran.
tag @a add recordLoad
tag @a add recordTick

# Create scoreboard(s)
scoreboard objectives add used.jukebox minecraft.used:jukebox
scoreboard objectives add __util__ dummy
scoreboard objectives add creeper_drop_music_disc dummy