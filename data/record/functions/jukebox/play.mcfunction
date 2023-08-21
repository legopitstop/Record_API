# Desc: Play record
#
# Called By: record:jukebox/tick

# actionbar
title @a[distance=..64] actionbar {"translate":"record.nowPlaying","with":[{"block": "~ ~ ~", "nbt":"RecordItem.tag.display.Lore[0]","color": "white","interpret": true}]}

# Play sound
function record:jukebox/callback with block ~ ~ ~ RecordItem.tag.record

scoreboard players set @s record.stopsound 1

# Prevent ticking
data modify block ~ ~ ~ RecordItem.tag.running set value true
