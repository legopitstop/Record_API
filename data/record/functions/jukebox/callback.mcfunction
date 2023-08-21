# Made by: @Legopitstop
# Desc: Plays this sound
#
# Called By: record:jukebox/play

$execute as @e[tag=Jukebox,limit=1,sort=nearest] at @s run playsound $(sound) record @a ~ ~ ~ 4 1 0