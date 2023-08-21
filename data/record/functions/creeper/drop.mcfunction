# Made by: @Legopitstop
# Desc: text
#
# Called By: text

$data modify storage record:loot_tables this set from storage record:loot_tables creeper[$(index)]
function record:creeper/callback with storage record:loot_tables

# Clean up
data remove storage record:loot_tables this
data remove storage record:loot_tables index