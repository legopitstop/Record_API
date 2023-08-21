from pygame import mixer
import os
import json
import logging
import random
import shutil
import base64
import io
import enum
import nbtlib

from util import convert_image_to_base64, convert_file_to_base64, save_base64, convert_base64_to_image, fetch_config
from client import ClientItem, ClientProject, ClientAsset

# **For Annotations Only**
from tkinter import StringVar, IntVar, messagebox, filedialog
from PIL import Image, ImageFile

logger = logging.getLogger('Server')

LOCAL = os.path.dirname(os.path.realpath(__file__))

class AssetType(enum.Enum):
    TEXTURE = 'texture'
    SOUND = 'sound'

class Asset(ClientAsset):
    def __init__(self, project, type:AssetType, path:str=None, source:str=None, size:tuple=None):
        self.project = project
        self.type = type
        self.source = source
        self.size = size
        self.path = path

        # Variables
        # self.sound_state = 'STOPPED'

    # Variables
    @property
    def PATH(self) -> StringVar:
        var = getattr(self, '_PATH', None)
        if var is None:
            var = StringVar()
            setattr(self, '_PATH', var)
        return var

    # Properties
    @property
    def size(self) -> tuple[int, int]:
        return getattr(self, '_size', None)
    
    @size.setter
    def size(self, value:tuple[int]):
        if value is None: return
        elif isinstance(value, tuple):
            setattr(self, '_size', value)
        else:
            raise TypeError(f"Expected tuple but got '{self.__class__.__name__}' instead")

    @property
    def source(self) -> str:
        return getattr(self, '_source', None)
    
    @source.setter
    def source(self, value:str):
        if value is None: return
        setattr(self, '_source', str(value))

    @property
    def type(self) -> AssetType|None:
        return getattr(self, '_type', None)
    
    @type.setter
    def type(self, value:AssetType):
        if isinstance(value, AssetType):
            setattr(self, '_type', value)
        elif isinstance(value, str):
            setattr(self, '_type', AssetType[str(value)])
        else:
            raise TypeError(f"Expected AssetType but got '{value.__class__.__name__}' instead")

    @property
    def path(self) -> str:
        res = self.PATH.get()
        if res =='':
            if self.type == AssetType.TEXTURE: return os.path.join(LOCAL, 'resources', 'pack.png')
            elif self.type == AssetType.SOUND: return os.path.join(LOCAL, 'resources', 'default.ogg')
        return res
    
    @path.setter
    def path(self, value:str):
        if value is None:
            raise TypeError(f"Expected str but got 'None' instead")
        if not os.path.isfile(value):
            raise FileNotFoundError(f"No such file or directory: '{value}'")
        self.PATH.set(str(value))

        if self.type == AssetType.TEXTURE:
            img = Image.open(self.path).resize(self.size, Image.NEAREST).convert('RGBA')
            self.source = convert_image_to_base64(img)

        elif self.type == AssetType.SOUND:
            self.source = convert_file_to_base64(self.path) # update source
            
            self.stop()
            self.load()
        
        else:
            raise TypeError(f"Unknown AssetType '{self.type}'")

    @classmethod
    def from_json(cls, parent, type:AssetType, size, data:dict):
        self = cls.__new__(cls)
        self.project = parent
        self.type = type
        self.size = size
        if 'source' in data: self.source = data.get('source')
        if 'path' in data:
            try:
                self.path = data.get('path')
            except FileNotFoundError as err:
                logger.warning(f"Failed to load asset: {err}")
        return self
    
    def json(self):
        data = {
            'path': self.path,
            'source': str(self.source)
        }
        return data

    # DEPRIVED - remove
    def configureOLD(self, **kw):
        applied_source = False
        if 'source' in kw:
            self.source = kw['source']
            applied_source = True

        if 'path' in kw:
            self.path = kw['path']
            self.textvariable.set(kw['path'])

            if applied_source is False:
                self.source = convert_file_to_base64(self.path)

            if self.type == AssetType.TEXTURE:
                if 'widget' in kw and kw['widget']!=None:
                    img = self.get_image()
                    kw['widget'].configure(image=img)

            elif self.type==AssetType.SOUND:
                self.stop()
                self.load()

            else: logging.error('Unknown AssetType "%s"', self.type)

    def export(self, fp:str):
        """Export asset as a file"""
        save_base64(fp, self.source)

    # Sound only
    def load(self):
        """Load the sound"""
        if self.type == AssetType.SOUND:
            if self.source is not None:
                mixer.music.unload()
                path = io.BytesIO(base64.decodebytes(bytes(self.source, 'utf-8')))
                mixer.music.load(path)
            else:
                raise TypeError(f"Expected Asset.source to be str but got None instead")

    def play(self):
        """Play the sound"""
        if self.type ==AssetType.SOUND:
            mixer.music.play()
            self.sound_state = 'PLAYING'

    def stop(self):
        """Stop the sound"""
        if self.type ==AssetType.SOUND:
            mixer.music.stop()
            self.sound_state = 'STOPPED'
            
    def pause(self):
        """Stop the sound"""
        if self.type ==AssetType.SOUND:
            mixer.music.pause()
            self.sound_state = 'PAUSED'

    def unpause(self):
        """Stop the sound"""
        if self.type ==AssetType.SOUND:
            mixer.music.unpause()
            self.sound_state = 'PLAYING'

    def toggle(self):
        """Toggle play/stop"""
        if self.sound_state=='PLAYING': self.stop()
        elif self.sound_state=='STOPPED': self.play()
        elif self.sound_state=='PAUSED': self.unpause()

    # Image only
    def get_image(self) -> ImageFile.ImageFile:
        if self.source is not None and self.source != 'None':
            return convert_base64_to_image(self.source)
        else:
            raise AttributeError('Asset.source does not exist or is invalid!')

class PartialItem:
    def __init__(self, id:str=None, name:str=None, artest:str=None, power_level:int=None, nbt:str=None, custom_model_data:int=None, obtain:str=None, texture:Asset=None, sound:Asset=None):
        self.id = id
        self.name = name
        self.artest = artest
        self.power_level = power_level
        self.nbt = nbt
        self.obtain = obtain
        self.custom_model_data = custom_model_data
        self.texture = texture
        self.sound = sound

    # Variables
    @property
    def NBT_ERROR(self) -> StringVar:
        var = getattr(self, '_NBT_ERROR', None)
        if var is None:
            var = StringVar(value='')
            setattr(self, '_NBT_ERROR', var)
        return var

    @property
    def ID(self) -> StringVar:
        var = getattr(self, '_ID', None)
        if var is None:
            var = StringVar(value='music_disc_new')
            setattr(self, '_ID', var)
        return var

    @property
    def NAME(self) -> StringVar:
        var = getattr(self, '_NAME', None)
        if var is None:
            var = StringVar(value='New Disc')
            setattr(self, '_NAME', var)
        return var

    @property
    def ARTEST(self) -> StringVar:
        var = getattr(self, '_ARTEST', None)
        if var is None:
            var = StringVar(value='None')
            setattr(self, '_ARTEST', var)
        return var

    @property
    def NBT(self) -> StringVar: 
        var = getattr(self, '_NBT', None)
        if var is None:
            var = StringVar(value='{}')
            setattr(self, '_NBT', var)
        return var

    @property
    def OBTAIN(self) -> StringVar:
        var = getattr(self, '_OBTAIN', None)
        if var is None:
            var = StringVar(value='none')
            setattr(self, '_OBTAIN', var)
        return var

    @property
    def POWER_LEVEL(self) -> IntVar:
        var = getattr(self, '_POWER_LEVEL', None)
        if var is None:
            var = IntVar(value=1)
            setattr(self, '_POWER_LEVEL', var)
        return var

    @property
    def CUSTOM_MODEL_DATA(self) -> IntVar:
        var = getattr(self, '_CUSTOM_MODEL_DATA', None)
        if var is None:
            var = IntVar(value=0)
            setattr(self, '_CUSTOM_MODEL_DATA', var)
        return var

    # Properties
    @property
    def custom_model_data(self) -> int:
        return self.CUSTOM_MODEL_DATA.get()

    @custom_model_data.setter
    def custom_model_data(self, value:int|str|None):
        if value is None:
            self.CUSTOM_MODEL_DATA.set(random.randint(1, 500))
        elif isinstance(value, int):
            self.CUSTOM_MODEL_DATA.set(value)
        elif isinstance(value, str):
            self.CUSTOM_MODEL_DATA.set(int(value)) # Convert str to int
        else:
            raise TypeError(f"Expected int or None but got '{value.__class__.__name__}' instead")

    @property
    def id(self) -> str:
        return self.ID.get()
    
    @id.setter
    def id(self, value:str|None):
        if value is None: self.ID.set('music_disc_new')
        else: self.ID.set(str(value))

    @property
    def name(self) -> str:
        return self.NAME.get()
    
    @name.setter
    def name(self, value:str|None):
        if value is None: self.NAME.set('New Disc')
        else: self.NAME.set(str(value))

    @property
    def artest(self) -> str:
        return self.ARTEST.get()
    
    @artest.setter
    def artest(self, value:str|None):
        if value is None: self.ARTEST.set('None')
        else: self.ARTEST.set(str(value))

    @property
    def power_level(self) -> str:
        return self.POWER_LEVEL.get()

    @power_level.setter
    def power_level(self, value:int|str|None):
        if value is None:
            self.POWER_LEVEL.set(1)
        elif isinstance(value, int):
            self.POWER_LEVEL.set(value)
        elif isinstance(value, str):
            self.POWER_LEVEL.set(int(value)) # Convert str to int
        else:
            raise TypeError(f"Expected int or None but got '{value.__class__.__name__}' instead")

    @property
    def nbt(self) -> str:
        return self.NBT.get()
    
    @nbt.setter
    def nbt(self, value:str|None):
        if value is None: self.NBT.set('{}')
        else: self.NBT.set(str(value))

    @property
    def obtain(self) -> str:
        return self.OBTAIN.get()
    
    @obtain.setter
    def obtain(self, value:str|int|None):
        if value is None: self.obtain = 'none'
        elif isinstance(value, int):
            match value:
                case 0: self.obtain = 'none'
                case 1: self.obtain = 'creeper'
                case _:
                    ValueError(f"Expected integer between 0 and 1 but got {value} instead")
        else:
            if str(value).lower() in ['none', 'creeper']:
                self.OBTAIN.set(str(value).lower())
            else:
                raise ValueError(f"Expected 'nokne' or 'creeper' but got '{value}' instead")

    @property
    def texture(self) -> Asset:
        res = getattr(self, '_texture', None)
        if res is None:
            self.texture = Asset(self.project, AssetType.TEXTURE, path=os.path.join(LOCAL, 'resources', 'missing.png'), size=(16, 16))
            return self.texture
        return res

    @texture.setter
    def texture(self, value:Asset|None):
        if value is None:
            setattr(self, '_texture', Asset(self.project, AssetType.TEXTURE, path=os.path.join(LOCAL, 'resources', 'missing.png'), size=(16, 16)))
        elif isinstance(value, Asset):
            setattr(self, '_texture', value)
        else:
            raise TypeError(f"Expected Asset or None but got '{value.__class__.__name__}' instead")

    @property
    def sound(self) -> Asset:
        res = getattr(self, '_sound', None)
        if res is None:
            self.sound = Asset(self.project, AssetType.SOUND, path=os.path.join(LOCAL, 'resources', 'default.ogg'))
            return self.sound
        return res

    @sound.setter
    def sound(self, value:Asset|None):
        if value is None:
            setattr(self, '_sound', Asset(self.project, AssetType.SOUND, path=os.path.join(LOCAL, 'resources', 'default.ogg')))
        elif isinstance(value, Asset):
            setattr(self, '_sound', value)
        else:
            raise TypeError(f"Expected Asset or None but got '{value.__class__.__name__}' instead")
    
    @classmethod
    def from_json(cls, parent, index:int, data:dict):
        self = cls.__new__(cls)
        self.project = parent
        self.index = index
        if 'id' in data: self.id = data.get('id')
        if 'name' in data: self.name = data.get('name')
        if 'artest' in data: self.artest = data.get('artest')
        if 'power_level' in data: self.power_level = data.get('power_level')
        if 'nbt' in data: self.nbt = data.get('nbt')
        if 'custom_model_data' in data: self.custom_model_data = data.get('custom_model_data')
        if 'obtain' in data: self.obtain = data.get('obtain')
        if 'texture' in data: self.texture = Asset.from_json(parent, AssetType.TEXTURE, (16,16), data.get('texture'))
        if 'sound' in data: self.sound = Asset.from_json(parent, AssetType.SOUND, None, data.get('sound'))
        return self

    def json(self):
        data = {
            'id': self.id,
            'name': self.name,
            'artest': self.artest,
            'power_level': self.power_level,
            'custom_model_data': self.custom_model_data,
            'nbt': self.nbt,
            'obtain': self.obtain,
            'texture': self.texture.json(),
            'sound': self.sound.json()
        }
        return data

class Item(PartialItem, ClientItem):
    def __init__(self, project, index:int, **kw):
        PartialItem.__init__(self, **kw)
        self.project = project
        self.index = index

    def roll_model_data(self):
        self.custom_model_data = None

    def save(self):
        """Save the item to the project"""
        self.project.render_outline() # update the outline

    def copy(self):
        """
        Returns a copy of this item
        """
        return Item.from_json(self.project, self.index, self.json())

    def rename(self, name:str=None):
        if name is None:
            if getattr(self, 'name_entry', None) is not None:
                self.name_entry.focus()
                self.name_entry.select_range(0, 'end')
        else:
            self.name = name

        return self

class PartialProject:
    def __init__(self, format:int=None, index:int=None, name:str=None, version:str=None, namespace:str=None, icon:Asset=None, description:str=None, descType:str=None, items:list[Item]=None):
        # self.last_descType = descType
        # self.selectedItem:Item = None
        # self.items = []
        # self.is_playing = False
        # self.format = format
        
        # Variables
        self.index = index
        self.format = format
        self.name = name
        self.version = version
        self.namespace = namespace
        self.descType = descType
        self.description = description
        self.icon = icon
        self.items = items

    # Variables
    @property
    def DESC_ERROR(self) -> StringVar:
        var = getattr(self, '_DESC_ERROR', None)
        if var is None:
            var = StringVar()
            setattr(self, '_DESC_ERROR', var)
        return var

    @property
    def NAME(self) -> StringVar:
        var = getattr(self, '_NAME', None)
        if var is None:
            var = StringVar(value='New Project')
            setattr(self, '_NAME', var)
        return var
    
    @property
    def VERSION(self) -> StringVar:
        var = getattr(self, '_VERSION', None)
        if var is None:
            var = StringVar(value='1.0.0')
            setattr(self, '_VERSION', var)
        return var

    @property
    def NAMESPACE(self) -> StringVar:
        var = getattr(self, '_NAMESPACE', None)
        if var is None:
            var = StringVar(value='minecraft')
            setattr(self, '_NAMESPACE', var)
        return var
    
    @property
    def DESC_TYPE(self) -> StringVar:
        var = getattr(self, '_DESC_TYPE', None)
        if var is None:
            var = StringVar(value='String')
            setattr(self, '_DESC_TYPE', var)
        return var

    @property
    def DESCRIPTION(self) -> StringVar:
        var = getattr(self, '_DESCRIPTION', None)
        if var is None:
            var = StringVar(value='My custom music discs pack!')
            setattr(self, '_DESCRIPTION', var)
        return var

    # Properties
    @property
    def index(self) -> int:
        return getattr(self, '_index', 0)
    
    @index.setter
    def index(self, value:int|None):
        if value is None: setattr(self, '_index', 0)
        elif isinstance(value, int): setattr(self, '_index', value)
        else:
            raise TypeError(f"Expected int or None but got '{value.__class__.__name__}' instead")

    @property
    def items(self) -> list[Item]:
        return getattr(self, '_items', [])
    
    @items.setter
    def items(self, value:list[Item]|None):
        if value is None: setattr(self, '_items', [])
        elif isinstance(value, list):
            setattr(self, '_items', [])
            for i in value:
                if isinstance(i, Item):
                    self.items.append(i)
                else:
                    raise TypeError(f"Expected Item but got '{i.__class__.__name__}' instead")
        else:
            raise TypeError(f"Expected list or None but got '{value.__class__.__name__}' instead")

    @property
    def name(self) -> str:
        return self.NAME.get()
    
    @name.setter
    def name(self, value:str|None):
        if value is None: self.NAME.set('New Project')
        else: self.NAME.set(str(value))

    @property
    def version(self) -> str:
        return self.VERSION.get()
    
    @version.setter
    def version(self, value:str|None):
        if value is None: self.VERSION.set('1.0.0')
        else: self.VERSION.set(str(value))

    @property
    def namespace(self) -> str:
        return self.NAMESPACE.get()
    
    @namespace.setter
    def namespace(self, value:str):
        if value is None: self.NAMESPACE.set('minecraft')
        else: self.NAMESPACE.set(str(value))

    @property
    def descType(self) -> str:
        return self.DESC_TYPE.get()
    
    @descType.setter
    def descType(self, value:str|int|None):
        if value is None: self.DESC_TYPE.set('String')
        elif isinstance(value, int):
            match value:
                case 0: self.descType = 'String'
                case 1: self.descType = 'TextComponent'
                case _:
                    ValueError(f"Expected integer between 0 and 1 but got {value} instead")
        else:
            if str(value) in ['String', 'TextComponent']:
                self.DESC_TYPE.set(str(value))
            else:
                raise ValueError(f"Expected 'String' or 'TextComponent' but got '{value}' instead")

    @property
    def description(self) -> str:
        return self.DESCRIPTION.get()
    
    @description.setter
    def description(self, value:str|None):
        if value is None: self.DESCRIPTION.set('My custom music discs pack!')
        else: self.DESCRIPTION.set(str(value))

    @property
    def icon(self) -> Asset:
        res = getattr(self, '_icon', None)
        if res is None:
            self.icon = Asset(self, AssetType.TEXTURE, path=os.path.join(LOCAL, 'resources', 'pack.png'), size=(128, 128))
            return self.icon
        return res
    
    @icon.setter
    def icon(self, value:Asset|None):
        if value is None:
            setattr(self, '_icon', Asset(self, AssetType.TEXTURE, path=os.path.join(LOCAL,  'resources', 'pack.png'), size=(128, 128)))
        elif isinstance(value, Asset):
            setattr(self, '_icon', value)
        else:
            raise TypeError(f"Expected Asset or None but got '{value.__class__.__name__}' instead")

    # Util Properties
    @property
    def lastDescType(self) -> str|None:
        return getattr(self, '_lastDescType', None)
    
    @lastDescType.setter
    def lastDescType(self, value:str|None):
        if value is None: setattr(self, '_lastDescType', None)
        else: setattr(self, '_lastDescType', value)

    @property
    def selectedItem(self) -> Item|None:
        return getattr(self, '_selected_item', None)
    
    @selectedItem.setter
    def selectedItem(self, value:Item|None):
        if value is None: setattr(self, '_selected_item', None)
        elif isinstance(value, Item): setattr(self, '_selected_item', value)
        else:
            raise TypeError(f"Expected Item or None but got '{value.__class__.__name__}' instead")

    @classmethod
    def from_json(cls, parent, data:dict):
        self = cls.__new__(cls)
        self.client = parent
        if 'format' in data: self.format = data.get('format')
        if 'name' in data:
            self.name = data.get('name')

        if 'version' in data: self.version = data.get('version')
        if 'namespace' in data: self.namespace = data.get('namespace')
        if 'description' in data: self.description = data.get('description')
        if 'descType' in data: self.descType = data.get('descType')

        if 'icon' in data:
            self.icon = Asset.from_json(self, AssetType.TEXTURE, (128, 128), data.get('icon'))

        if 'items' in data:
            i = 0
            items = []
            for item in data.get('items'):
                obj = Item.from_json(self, i, item)
                items.append(obj)
                i += 1
            self.items = items
        
        return self
    
    def json(self):
        data = {
            'format': self.format,
            'name': self.name,
            'version': self.version,
            'namespace': self.namespace,
            'icon': self.icon.json(),
            'descType': self.descType,
            'description': self.description,
            'items': []
        }
        for item in self.items: data['items'].append(item.json())
        return data

class Project(PartialProject, ClientProject):
    def __init__(self, client, format:int=None, **kw):
        PartialProject.__init__(self, **kw)
        self.client = client
        
        self.format = self.client._format
        if format is not None: self.format = format
    
    def add_item(self, item:Item):
        """Adds a new item to the project"""
        self.items.insert(0, item)
        self.update()
        self.set_item(0)

    def remove_item(self, index:int=None):
        """Remove the item with the index or the current selected item"""
        if index==None and self.selectedItem!=None: index = self.selectedItem.index
        if index!=None:
            confirm = messagebox.askyesno('Delete Item', 'Are you sure that you want to delete this item?', parent=self.client)
            if confirm:
                try:
                    del self.items[index]
                    self.adjust_index()
                    self.render_outline()
                    self.render()
                except IndexError:
                    logger.warning('Failed to delete the item as it was not found!')
                    messagebox.showwarning('Item not found', 'Failed to delete the item as it was not found!', parent=self.client)

    def adjust_index(self):
        """Updates all items with their new index values"""
        index = 0
        for item in self.items:
            item.index = index
            index+=1

    def save(self):
        """Save variables (SCREEN) to class"""
        # Save item
        if self.selectedItem!=None:
            self.selectedItem.save()

        # Save project
        self.name = self.NAME.get()
        self.version = self.VERSION.get()
        self.namespace = self.NAMESPACE.get()
        self.description = self.DESCRIPTION.get()
        self.descType = self.DESC_TYPE.get()

    def get_item(self, index:int):
        """Get the item from index"""
        for item in self.items:
            if item.index == index: return item
        return None

    def set_item(self, index:int):
        """Set the item"""
        self.save()
        self.selectedItem = self.get_item(index)
        if self.selectedItem!=None:
            self.client.rpc_state('item')
            self.selectedItem.render()

    def _import(self):
        filetypes = [('Project', '*.mcdisc')]
        fp = filedialog.askopenfilename(defaultextension='.mcdisc', parent=self.client, filetypes=filetypes, title='Import')
        if fp!='':
            if fp.endswith('.mcdisc'):
                project:Project = self.client.open(fp, False)
                if project!=None:
                    for item in project.items: self.items.append(item)
                    self.adjust_index()
                    self.render_outline()
                    logger.info(f'IMPORT "{fp}"')
                    return True
                
            else:
                messagebox.showwarning('Import Error', f"'{os.path.basename(fp)}' is not a supported filetype.")

        return False

    def render_description(self):
        """Render the description as a STRING or JSON"""
        if self.descType == 'rawjson':
            try: return json.loads(self.description)
            except json.decoder.JSONDecodeError: return self.description
        else: return self.description

    def export_v1(self, path:str):
        """
        API VERSION: 1
        """
        
        def remove_dir(path:str):
            if os.path.exists(path) and os.path.isdir(path):
                for name in os.listdir(path):
                    file = os.path.join(path, name)
                    if os.path.isfile(file): os.remove(file)
                    elif os.path.isdir(file): remove_dir(file)
                try: os.removedirs(path)
                except FileNotFoundError: pass

        # Datapack
        dp_name = self.client.format('dp', name=self.name, version=self.version)
        dp_path = os.path.join(path, dp_name)
        os.makedirs(os.path.join(dp_path, 'data', 'record', 'tags', 'functions'), exist_ok=True)
        os.makedirs(os.path.join(dp_path, 'data', self.namespace, 'functions'), exist_ok=True)
        os.makedirs(os.path.join(dp_path, 'data', self.namespace, 'loot_tables', 'item'), exist_ok=True)
        os.makedirs(os.path.join(dp_path, 'data', self.namespace, 'tags', 'functions'), exist_ok=True)
        
        with open(os.path.join(dp_path, 'pack.mcmeta'), 'w') as manifest:
            data = {
                'pack': {
                    'pack_format': int(self.client.c.getItem('dp_version')),
                    'version': self.version,
                    'description': self.render_description() # Should get converted to JSON if type is set to TextComponent
                }
            }
            manifest.write(json.dumps(data))
        if self.icon!=None: self.icon.export(os.path.join(dp_path, 'pack.png'))
        # Resourcepack
        rp_name = self.client.format('rp', name=self.name, version=self.version)
        rp_path = os.path.join(path, rp_name)
        os.makedirs(os.path.join(rp_path, 'resources', 'record', 'models', 'item'), exist_ok=True)
        os.makedirs(os.path.join(rp_path, 'resources', self.namespace, 'lang'), exist_ok=True)
        os.makedirs(os.path.join(rp_path, 'resources', self.namespace, 'sounds', 'records'), exist_ok=True)
        os.makedirs(os.path.join(rp_path, 'resources', self.namespace, 'textures', 'item'), exist_ok=True)
        with open(os.path.join(rp_path, 'pack.mcmeta'), 'w') as manifest:
            data = {
                'pack': {
                    'pack_format': int(self.client.c.getItem('rp_version')),
                    'version': self.version,
                    'description': self.render_description() # Should get converted to JSON if type is set to rawjson
                }
            }
            manifest.write(json.dumps(data))
        if self.icon!=None: self.icon.export(os.path.join(rp_path, 'pack.png'))
        # Both for items
        LANG = {"___comment": "Generated using Music Disc Studio"}
        SOUNDS = {}
        CREEPER_TAG = {'values': []}
        ALL_TAG = {'values': []}
        for item in self.items:
            item:Item = item # TEMP
            mc_item = self.client.mc_disc_power(item.power_level)
            # Datapack
            with open(os.path.join(dp_path, 'data', self.namespace, 'functions', '%s.mcfunction'%(item.id)), 'w') as func:
                if item.obtain=='creeper':
                    obtain = 'scoreboard players add #total creeper_drop_music_disc 1\n'
                    CREEPER_TAG['values'].append('%s:%s'%(self.namespace, item.id))
                else: obtain = ''
                FUNCTION = '# Desc: Summons the custom item\n#\n# Called by: Player\n'+obtain+'loot spawn ~ ~ ~ loot %s:item/%s'%(self.namespace, item.id)
                func.write(FUNCTION)
                ALL_TAG['values'].append('%s:%s'%(self.namespace, item.id))
            # Loot table
            item_nbt = nbtlib.Compound(
                id = nbtlib.String(self.namespace),
                record = nbtlib.Compound(
                    power_level = nbtlib.Int(item.power_level),
                    command=nbtlib.String(f"execute as @e[tag=Jukebox,limit=1,sort=nearest] at @s run playsound {self.namespace}:music_disc.{item.id.replace('music_disc_', '')}' record @a ~ ~ ~ 4 1 0")
                ),
                HideFlags = nbtlib.Int(32),
                CustomModelData= nbtlib.Int(item.custom_model_data),
                display = nbtlib.Compound(
                    Name = nbtlib.String('{"translate":"item.'+self.namespace+'.'+item.id+'","italic": false}'),
                    Lore = nbtlib.List([
                        nbtlib.String('{"translate":"item.'+self.namespace+'.'+item.id+'.desc","color":"gray","italic": false}')
                    ])
                )
            )
            try:
                additional_nbt:nbtlib.Compound = nbtlib.parse_nbt(item.nbt)
            except nbtlib.InvalidLiteral as err:
                logger.warning(f'Failed to parse NBT for item {item.name}')
                continue
            # Merge with item_nbt
            if isinstance(additional_nbt, nbtlib.Compound):
                for k, tag in additional_nbt.items():
                    item_nbt[k] = tag
            with open(os.path.join(dp_path, 'data', self.namespace, 'loot_tables', 'item', '%s.json'%(item.id)), 'w') as file:
                table = {
                    'pools': [
                        {
                            'rolls': 1,
                            'entries': [
                                {
                                    'type': 'minecraft:item',
                                    'name': 'minecraft:%s'%(mc_item),
                                    'functions': [
                                        {
                                            'function': 'minecraft:set_nbt', # Should be split to use 'set_name' and 'set_lore'
                                            'tag': str(item_nbt.snbt())
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
                file.write(json.dumps(table))                    
            # Resroucepack
            item.sound.export(os.path.join(rp_path, 'resources', self.namespace, 'sounds', 'records', '%s.ogg'%(item.id.replace('music_disc_',''))))
            item.texture.export(os.path.join(rp_path, 'resources', self.namespace, 'textures', 'item', '%s.png'%(item.id)))
            with open(os.path.join(rp_path, 'resources', 'record', 'models', 'item', '%s_%s.json'%(mc_item, item.custom_model_data)), 'w') as model:
                data = {'parent': 'minecraft:item/generated','textures': {'layer0': '%s:item/%s'%(self.namespace, item.id)}}
                model.write(json.dumps(data))
            LANG['item.%s.%s'%(self.namespace, item.id)] = 'Music Disc'
            LANG['item.%s.%s.desc'%(self.namespace, item.id)] = self.client.format('lore', name=item.name, artest=item.artest)
            SOUNDS['music_disc.%s'%(item.id.replace('music_disc_',''))] = {
                'sounds': [
                    {
                        'name': '%s:records/%s'%(self.namespace, item.id.replace('music_disc_','')),
                        'stream': True
                    }
                ]
            }
        with open(os.path.join(dp_path, 'data', 'record', 'tags', 'functions', 'creeper.json'), 'w') as tag: tag.write(json.dumps(CREEPER_TAG))
        with open(os.path.join(dp_path, 'data', self.namespace, 'tags', 'functions', 'all.json'), 'w') as tag: tag.write(json.dumps(ALL_TAG))
        with open(os.path.join(rp_path, 'resources', self.namespace, 'lang', '%s.json'%(self.client.c.getItem('locale'))), 'w') as file: file.write(json.dumps(LANG))
        with open(os.path.join(rp_path, 'resources', self.namespace, 'sounds.json'), 'w') as file: file.write(json.dumps(SOUNDS))
        # ZIP packs
        if self.client.c.getItem('archiveOutput')=='True':
            shutil.make_archive(dp_path, 'zip', dp_path)
            shutil.make_archive(rp_path, 'zip', rp_path)
            remove_dir(dp_path)
            remove_dir(rp_path)
        confirm = messagebox.askyesno('Export', 'Successfully exported "%s". Do you want to open the output folder?'%(self.name))
        if confirm: os.startfile(path)
        return True

    def export(self, type:str=None):
        path = filedialog.askdirectory(mustexist=False, parent=self.client, title='Export')
        if path!='':
            if int(self.client.c.getItem('api_version')) == 1:
                return self.export_v1(path)
        return False

    def update(self):
        self.render_outline()
        self.adjust_index()

class WebConfig:
    """
    Config from the Github repo for up-to-date info.
    """
    settings = {
        'resources_format': 15,
        'data_format': 15
    }
    items = []
    def __init__(self, settings:dict, items:list=[]):
        self.settings = settings
        self.items = items

    @classmethod
    def fetch(cls):
        self = cls.__new__(cls)
        res, data = fetch_config()
        if res:
            self.settings = data['settings']
            self.items = data['items']
        return self
    