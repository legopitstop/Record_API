# Desc: runs all files (looping)
#
# Called by: record:pre_tick

# Jukebox tick
execute as @e[type=marker,tag=Jukebox] at @s run function record:jukebox/tick

# Creeper Loot
execute as @e[type=item,nbt={Item:{id: "minecraft:paper", tag:{DropCreeperDisc:1b}}}] at @s run function record:creeper/init with storage record:loot_tables

# Place jukebox
execute as @e[type=marker,tag=SetJukebox] at @s if block ~ ~ ~ command_block run function record:jukebox/place

# Summon marker at jukebox
execute at @a[scores={record.jukebox=1..}] run fill ~-5 ~-5 ~-5 ~10 ~10 ~10 command_block{Command:'summon marker ~ ~ ~ {Tags:["SetJukebox"]}',auto:1b} replace minecraft:jukebox[has_record=false]

# Data fixer
execute as @e[type=item,nbt={Item:{tag:{running:true}}}] run function record:jukebox/stop
execute as @e[type=item,nbt={Item:{tag:{running:true}}}] run data remove entity @s Item.tag.running

# Reset
execute as @a[scores={record.jukebox=1..}] run scoreboard players reset @s record.jukebox
