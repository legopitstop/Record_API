# Desc: Play record
#
# Called By: record:jukebox/tick

# Stop vanilla sounds
stopsound @a[distance=..128] record minecraft:music_disc.11
stopsound @a[distance=..128] record minecraft:music_disc.13
stopsound @a[distance=..128] record minecraft:music_disc.blocks
stopsound @a[distance=..128] record minecraft:music_disc.cat
stopsound @a[distance=..128] record minecraft:music_disc.chirp
stopsound @a[distance=..128] record minecraft:music_disc.far
stopsound @a[distance=..128] record minecraft:music_disc.mall
stopsound @a[distance=..128] record minecraft:music_disc.mellohi
stopsound @a[distance=..128] record minecraft:music_disc.otherside
stopsound @a[distance=..128] record minecraft:music_disc.pigstep
stopsound @a[distance=..128] record minecraft:music_disc.stal
stopsound @a[distance=..128] record minecraft:music_disc.strad
stopsound @a[distance=..128] record minecraft:music_disc.wait
stopsound @a[distance=..128] record minecraft:music_disc.ward

# actionbar
title @a[distance=..64] actionbar {"translate":"record.nowPlaying","with":[{"block": "~ ~ ~", "nbt":"RecordItem.tag.display.Lore[0]","color": "white","interpret": true}]}

# Run command
execute if block ~ 319 ~ command_block run setblock ~ 319 ~ air
execute if block ~ 319 ~ air run setblock ~ 319 ~ command_block{}
execute if block ~ 319 ~ command_block run data modify block ~ 319 ~ Command set from block ~ ~ ~ RecordItem.tag.record.command
execute if block ~ 319 ~ command_block run data modify block ~ 319 ~ auto set value 1b

# Prevent ticking
data modify block ~ ~ ~ RecordItem.tag.running set value true