# Desc: Tick file for jukebox
#
# Called By: record:main_tick

# Break block
execute unless block ~ ~ ~ jukebox run function record:jukebox/stop
execute unless block ~ ~ ~ jukebox run kill @s

# Detect custom record
execute if block ~ ~ ~ jukebox[has_record=true] unless data block ~ ~ ~ RecordItem.tag.running if data block ~ ~ ~ RecordItem.tag.record run function record:jukebox/play