# Desc: Stop the record from playing
#
# Called By: record:main_tick

execute at @e[tag=Jukebox] if block ~ 319 ~ command_block run setblock ~ 319 ~ air
execute at @e[tag=Jukebox] run stopsound @a[distance=..64] record