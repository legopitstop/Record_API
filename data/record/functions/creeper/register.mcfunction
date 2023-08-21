# Made by: @Legopitstop
# Desc: Register all creeper drops
#
# Called By: record:main_tick & record:reload

# Clear
data modify storage record:loot_tables creeper set value []
function #record:register_creeper_drops

# Get total index
execute store result score #temp record.util run data get storage record:loot_tables creeper
execute store result storage record:loot_tables total_creeper int 1 run scoreboard players remove #temp record.util 1