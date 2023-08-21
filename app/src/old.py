"""(DEPRECATED) This is used for upgrading to a new format and should not be used."""
from PIL import Image
import UserFolder
import os
import json
import uuid

class Cache():
    def __init__(self, user:UserFolder.User):
        self.user = user

        self.objects = user.join('objects')
        os.makedirs(self.objects, exist_ok=True)
        if user.exists('index.json')==False:
            with user.open('index.json', 'w') as f:
                f.write(json.dumps({'objects': {}}))
        self.index = self.open()

    def size(self):
        """Returns the total size of the cache"""
        size = 0
        for ele in os.scandir(self.user.join('objects')):
            size += os.path.getsize(ele)
        return size
    
    def exists(self, fp:str=None, hash:str=None):
        """Checks if the file is in the cache"""
        fp = self.get(fp=fp, hash=hash)
        if fp!=None: return True
        else: return False

    def open(self):
        """Read the index"""
        with self.user.open('index.json', 'r') as f:
            return json.load(f)

    def save(self):
        """Write the index"""
        with self.user.open('index.json', 'w') as f:
            return f.write(json.dumps(self.index))

    def add_image(self, fp, size):
        """Add an image to the cache"""
        img = Image.open(fp).resize(size, Image.NEAREST)
        hash = uuid.uuid4().hex
        img.save(self.user.join('objects', hash), format='png')
        return self.add_index(fp, hash)

    def add_sound(self, fp):
        """Add a sound to cache"""
        return self.add(fp)

    def add_index(self, fp:str, hash:str):
        """Adds the fp and hash to the index.json"""
        self.index['objects'][fp] = {'hash': hash}
        self.save()
        return hash

    def add(self, fp):
        """Add the raw file to the cache"""
        with open(fp, 'rb') as r:
            hash = uuid.uuid4().hex
            with open(os.path.join(self.objects, hash), 'wb') as w:
                w.write(r.read())
                return self.add_index(fp, hash)

    def get(self, fp:str=None, hash:str=None):
        """Get the hash fp from the fp"""
        if fp!=None:
            try:
                hash = self.index['objects'][fp]['hash']
                return self.get(hash=hash)
            except KeyError:
                return None
        
        elif hash!=None:
            fp = self.user.join('objects',hash)
            if os.path.exists(fp) and os.path.isfile(fp): return fp
            else: return None
    
    def delete(self):
        """Clear all cached files"""
        for file in os.listdir(self.user.join('objects')):
            os.remove(self.user.join('objects', file))
        self.index = {'objects': {}}
        self.save()
        return True
