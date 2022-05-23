# Desc: Places the jukeboxs
#
# Called By: record:main_tick

summon marker ~ ~ ~ {Tags:[Jukebox]}
setblock ~ ~ ~ jukebox
kill @s