# Made by: @Legopitstop
# Desc: Get RNG index value for loot table
#
# Called By: record:main_tick & record:creeper/test

$execute store result storage record:loot_tables index int 1 run random value 0..$(total_creeper) minecraft:entities/creeper
function record:creeper/drop with storage record:loot_tables

# reset
kill @s[type=item]