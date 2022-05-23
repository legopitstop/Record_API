# Desc: runs all files (looping)
#
# Called by: #minecraft:tick

# tells load to run, then tick can run
execute if entity @a[tag=!recordLoad] run function record:main_load
execute if entity @r[tag=recordTick] run function record:main_tick