"""Add item predicates for all vanilla discs"""
import json, os

# base path
LOCAL = os.path.dirname(os.path.realpath(__file__))

# loop through all files that end in .json
for file in os.listdir(LOCAL):
    if file.endswith('.json'):

        # Read
        opn = open(LOCAL+'/'+file, 'r')
        obj = json.load(opn)
        opn.close()
        obj['overrides'] = []

        # Add 1-500 CustomModelData predicates
        for num in range(500):
            filename = file.replace('.json','') + '_' + str(num+1)
            print(filename)
            obj['overrides'].append({"predicate": {"custom_model_data": num+1},"model": "record:item/"+filename})
            
        # Write
        wrt = open(LOCAL+'/'+file, 'w')
        wrt.write(json.dumps(obj))
        wrt.close()
