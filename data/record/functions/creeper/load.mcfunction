# Desc: Run the function once
#
# Called By: main:main_tick

# reset
scoreboard players set #total creeper_drop_music_disc 0

# Spawn all discs
function #record:creeper

# Subtract one item (bc we only want to get one item)
scoreboard players remove #total creeper_drop_music_disc 1

# Kill a random disc until one is left
function record:creeper/loop