# Made by: @Legopitstop
# Desc: Run the loot table
#
# Called By: record:creeper/drop

$loot spawn ~ ~ ~ loot $(this)
tellraw @a [{"text": "record.util: "},{"storage": "record:loot_tables", "nbt": "this"}]