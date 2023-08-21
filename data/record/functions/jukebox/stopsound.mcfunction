# Made by: @Legopitstop
# Desc: Stops the vanilla disc from playing
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
stopsound @a[distance=..128] record minecraft:music_disc.relic

# reset
scoreboard players reset @s record.stopsound