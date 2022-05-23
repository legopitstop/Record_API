# Desc: Kills all disc items until one is left
#
# Called By: main:creeper/init

# remove random disc
kill @e[type=item,nbt={Item:{tag:{record:{}}}}, sort=random, limit=1]

# Subtract one item, then run again
scoreboard players remove #total creeper_drop_music_disc 1
execute unless score #total creeper_drop_music_disc matches ..0 run function record:creeper/loop