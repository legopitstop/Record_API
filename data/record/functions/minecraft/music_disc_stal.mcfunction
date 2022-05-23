# Desc: Summons the custom item
#
# Called by: Player

scoreboard players add #total creeper_drop_music_disc 1
summon item ~ ~ ~ {Item:{id:"minecraft:music_disc_stal",Count:1b,tag:{record:{}}}}