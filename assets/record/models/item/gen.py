"""This generates placeholder JSON models to prevent FileNotFoundError"""
import json, os

# List of all vanilla models
items = [
    'music_disc_11',
    'music_disc_13',
    'music_disc_blocks',
    'music_disc_cat',
    'music_disc_chirp',
    'music_disc_far',
    'music_disc_mall',
    'music_disc_mellohi',
    'music_disc_otherside',
    'music_disc_pigstep',
    'music_disc_stal',
    'music_disc_strad',
    'music_disc_wait',
    'music_disc_ward'
]

# get the base path
LOCAL = os.path.dirname(os.path.realpath(__file__))

# loop for all items
for item in items:

    # Loop 500 times
    for num in range(500):
        filename = item+'_'+str(num+1)+'.json'
        content = {"parent": "minecraft:item/generated","textures": {"layer0": "minecraft:item/"+item}}
        wrt = open(LOCAL+'/'+filename, 'w')
        wrt.write(json.dumps(content))
        wrt.close()
        print(filename)