from customtkinter import CTkLabel, CTkEntry, CTkOptionMenu, CTkTextbox, CTkFrame
from tkinter import CENTER, DISABLED, E, END, EW, LEFT, NW, S, W, Canvas, StringVar, Tk, filedialog, PhotoImage, messagebox
from UserFolder import User
from PIL import Image, ImageTk
from pygame import mixer
from tktooltip import ToolTip
import os
import json
import uuid
import logging
import random
import shutil
import _tkinter

LOCAL = os.path.dirname(os.path.realpath(__file__))

class Picture(Canvas):
    def __init__(self, master:Tk, image:Image=None, width:int=None, height:int=None, text:str=None, fg:str='black', bg:str='white',**kw):
        """Display an image on the window"""
        super().__init__(master, borderwidth=0, highlightthickness=0)
        self.image = Image.open(os.path.join(LOCAL, 'assets', 'missing.png'))
        self.width = None
        self.height = None
        self.text = None
        self.fg = None
        self.configure(image=image,width=width,height=height,text=text, fg=fg, bg=bg,**kw)

    def update(self):
        # Clear canvas to redraw
        self.delete('all')

        # Resize image
        if self.width == None: self.width = 1
        if self.height == None: self.height = 1
        self.imagetk = ImageTk.PhotoImage(self.image.resize((self.width, self.height), Image.NEAREST))
        self.create_image(2,2,image=self.imagetk,anchor=NW,tags=['IMAGE'])


        if self.text!=None:
            self.create_text(self.width/2, self.height+20, text=self.text, fill=self.fg, justify=CENTER, anchor=S, tag='TEXT')

        else: text_height = 0

        # Update canvas dimentions
        super().configure(width=self.width, height=self.height + text_height)

    def configure(self,**kw):
        """Modify the widget"""
        if 'image' in kw and kw['image'] is not None:
            self.image:Image = kw['image']
            if self.width==None:self.width = self.image.width
            if self.height==None:self.height = self.image.height

        if 'text' in kw and kw['text'] is not None: self.text = kw['text']
        if 'width' in kw and kw['width'] is not None:self.width = kw['width']
        if 'height' in kw and kw['height'] is not None:self.height = kw['height']
        if 'fg' in kw and kw['fg'] is not None: self.fg = kw['fg']
        if 'bg' in kw and kw['bg'] is not None: super().configure(bg=kw['bg'])

        self.update()

    config = configure

class Cache():
    def __init__(self, user: User):
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
        #TODO This should convert the sound to OGG and Channel 1
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

class AssetType():
    TEXTURE = 'texture'
    SOUND = 'sound'

class Asset():
    def __init__(self, project, type:AssetType, textvariable:StringVar, size:tuple=None, hash:str=None, path:str=None):
        self.cache:Cache = project.client.cache
        self.project = project
        self.logger = logging.getLogger('Asset')
        self.type = type
        self.hash = hash
        self.path = path
        self.textvariable = textvariable
        self.sound_state = 'STOPPED'
        self.size = size

        if self.hash!=None and self.path!=None:
            if self.cache.exists(hash=self.hash)==False:
                self.logger.info('MISSING "%s"', self.path)
                self.configure(path=self.path)

        # Default
        if self.hash==None and self.path==None:
            if type==AssetType.TEXTURE:
                self.configure(path=os.path.join(LOCAL, 'assets', 'missing.png'), size=size)
                logging.info('texture %s %s', self.hash, self.path)
            elif type==AssetType.SOUND: 
                self.configure(path=os.path.join(LOCAL, 'assets', 'default.ogg'))
                logging.info('sound %s %s', self.hash, self.path)
    
    def json(self):
        data = {
            'hash': self.hash,
            'path': self.path
        }
        return data

    def configure(self, **kw):
        if 'path' in kw:
            self.path = kw['path']
            self.textvariable.set(kw['path'])
            if self.type == AssetType.TEXTURE:
                self.hash = self.cache.add_image(self.path, self.size)
                if 'widget' in kw and kw['widget']!=None:
                    img = self.get_image()
                    kw['widget'].configure(image=img)

            elif self.type==AssetType.SOUND:
                self.hash = self.cache.add_sound(self.path)
                self.stop()
                self.load()

            else: logging.error('Unknown AssetType "%s"', self.type)
        
        if 'hash' in kw: self.hash = kw['hash']

    config = configure

    def choose(self, widget=None, callback=None):
        """Choose a file"""
        if self.type==AssetType.TEXTURE:
            defaultextension = '.png'
            filetypes = [('Images', '.png .tif .tiff .bmp .jpg .jpeg .gif .eps .raw')]
        
        elif self.type==AssetType.SOUND:
            defaultextension = '.ogg'
            # filetypes = [('Sounds', '.ogg .mp3 .aac .flac .alac .wav .aiff .dsd .pcm')]
            filetypes = [('Sounds', '.ogg')]
        
        else:
            defaultextension = None
            filetypes = [('Any', '*.*')]

        fp = filedialog.askopenfilename(defaultextension=defaultextension, filetypes=filetypes, initialdir=self.textvariable.get(), parent=self.project.client)
        if os.path.exists(fp) and os.path.isfile(fp):
            self.configure(path=fp, widget=widget)
            self.textvariable.set(fp)
            if callback!=None: callback(fp)

    def export(self, fp:str):
        """Export the cached version of the asset"""
        cache_path = self.cache.get(hash=self.hash)
        if cache_path!=None:
            with open(cache_path, 'rb') as src:
                with open(fp, 'wb') as dst:
                    dst.write(src.read())
                    return True
        return False

    # Sound only
    def load(self):
        """Load the sound"""
        if self.type == AssetType.SOUND:
            mixer.music.unload()
            mixer.music.load(self.path) #TODO Shoud use the cached file

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
    def get_image(self):
        if self.hash!=None:
            fp = self.cache.get(hash=self.hash)
            return Image.open(fp=fp)

class Item():
    def __init__(self, project, index:int=0, id:str='music_disc_new', name:str='New Disc', artest:str='None', power_level:int=1, nbt:str="{}", custom_model_data:int=None, obtain:str='none', texture:dict={}, sound:dict={}):
        self.project = project
        self.logger = logging.getLogger('Item')
        self.index = index

        # Variables
        self.ID = StringVar()
        self.NAME = StringVar()
        self.ARTEST = StringVar()
        self.POWER_LEVEL = StringVar()
        self.NBT = StringVar()
        self.OBTAIN = StringVar()
        self.TEXTURE = StringVar()
        self.SOUND = StringVar()

        self.id = id
        self.name = name
        self.artest = artest
        self.power_level = power_level
        self.nbt = nbt
        self.obtain = obtain
        self.custom_model_data = custom_model_data
        self.texture = texture
        self.sound = sound

        # Assets
        # if texture!=None:self.texture = Asset(self.project, AssetType.TEXTURE, self.TEXTURE, (16,16), **texture)
        # else: self.texture = Asset(self.project, AssetType.TEXTURE, self.TEXTURE, (16,16))
        # if sound!=None: self.sound = Asset(self.project, AssetType.SOUND, self.SOUND, **sound)
        # else: self.sound = Asset(self.project, AssetType.SOUND, self.SOUND)

        # if custom_model_data==None: self.custom_model_data = random.randint(1, 500)

    # Properties
    @property
    def custom_model_data(self): return self._custom_model_data

    @custom_model_data.setter
    def custom_model_data(self, value:int|None):
        if value == None: self._custom_model_data = random.randint(1, 500)
        else: self._custom_model_data = value

    @property
    def id(self): return self.ID.get()
    @id.setter
    def id(self, value:str): self.ID.set(value)

    @property
    def name(self): return self.NAME.get()
    @name.setter
    def name(self, value:str): self.NAME.set(value)

    @property
    def artest(self): return self.ARTEST.get()
    @artest.setter
    def artest(self, value:str): self.ARTEST.set(value)

    @property
    def power_level(self): return self.POWER_LEVEL.get()
    @power_level.setter
    def power_level(self, value:int): self.POWER_LEVEL.set(str(value))

    @property
    def nbt(self): return self.NBT.get()
    @nbt.setter
    def nbt(self, value:str):
        if value==None: self.NBT.set('{}')
        else: self.NBT.set(value)

    @property
    def obtain(self): return self.OBTAIN.get()
    @obtain.setter
    def obtain(self, value:str):
        if value==None: self.OBTAIN.set('none')
        else: self.OBTAIN.set(value)

    @property
    def texture(self): return self._texture
    @texture.setter
    def texture(self, value:dict):
        self._texture = Asset(self.project, AssetType.TEXTURE, self.TEXTURE, (16,16), hash=value.get('hash'), path=value.get('path'))
        self.TEXTURE.set(self._texture.path)

    @property
    def sound(self): return self._sound
    @sound.setter
    def sound(self, value:dict):
        self._sound = Asset(self.project, AssetType.SOUND, self.SOUND, hash=value.get('hash'), path=value.get('path'))
        self.SOUND.set(self._sound.path)
    
    # Methods

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

    def render(self):
        """Render the item screen"""
        self.project.client.clear_screen()
        client:Tk = self.project.client.screen
        power_level_values = [
            "1", # 13
            "2", # cat
            "3", # blocks
            "4", # chirp
            "5", # far
            "6", # mall
            "7", # mellohi
            "8", # stal
            "9", # strad
            "10", # ward
            "11", # 11
            "12", # wait
            "13", # pigstep
            "14", # otherside
            "15" # 5
        ]
        obtain_values = ['none', 'creeper']

        options = CTkFrame(client)

        CTkLabel(options, text='Name', anchor=E).grid(row=0,column=0, padx=10, sticky=W)
        CTkEntry(options, textvariable=self.NAME).grid(row=1, column=0, pady=5, padx=10, sticky=EW)
        
        CTkLabel(options, text='Artest', anchor=E).grid(row=2,column=0, padx=10, sticky=W)
        CTkEntry(options, textvariable=self.ARTEST).grid(row=3, column=0, pady=5, padx=10, sticky=EW)
        
        CTkLabel(options, text='ID', anchor=E).grid(row=4,column=0, padx=10, sticky=W)
        id = CTkEntry(options, textvariable=self.ID)
        self.project.client.validate(id, 'id')
        id.grid(row=5, column=0, pady=5, padx=10, sticky=EW)
        
        CTkLabel(options, text='Power Level', anchor=E).grid(row=6,column=0, padx=10, sticky=W)
        CTkOptionMenu(options, values=power_level_values, variable=self.POWER_LEVEL).grid(row=7,column=0, pady=5, padx=10, sticky=EW)
        
        CTkLabel(options, text='NBT', anchor=E).grid(row=8,column=0, padx=10, sticky=W)
        CTkEntry(options, textvariable=self.NBT).grid(row=9, column=0, pady=5, padx=10, sticky=EW)
        
        CTkLabel(options, text='Obtain', anchor=E).grid(row=10,column=0, padx=10, sticky=W)
        CTkOptionMenu(options, values=obtain_values, variable=self.OBTAIN).grid(row=11, column=0, pady=5, padx=10, sticky=EW)
        
        pic = Picture(options, image=Image.open(self.project.client.cache.get(hash=self.texture.hash)), width=100, height=100, bg=options['bg'])
        pic.bind('<Button-1>', lambda e: self.texture.choose(pic))
        pic.grid(row=12, column=0, padx=10,pady=5,sticky=W)
        ToolTip(pic, msg='Left Click to choose file')
        CTkLabel(options, text='Texture', anchor=E).grid(row=13,column=0, padx=10, sticky=W)
        CTkEntry(options, textvariable=self.TEXTURE, state=DISABLED).grid(row=14,column=0, pady=5, padx=10, sticky=EW)
        
        snd = Picture(options, image=Image.open(os.path.join(LOCAL, 'assets', 'jukebox.png')).convert('RGBA'), width=100, height=100, bg=options['bg'])
        snd.bind('<Button-3>', lambda e: self.sound.toggle())
        snd.bind('<Button-1>', lambda e: self.sound.choose(snd))
        snd.grid(row=15,column=0, padx=10,pady=5,sticky=W)
        ToolTip(snd, msg='Left Click to choose file\nRight Click to play/stop sound')

        CTkLabel(options, text='Sound', anchor=E).grid(row=16,column=0, padx=10, sticky=W)
        CTkEntry(options, textvariable=self.SOUND, state=DISABLED).grid(row=17,column=0, pady=5, padx=10, sticky=EW)
        options.grid_columnconfigure(0, weight=1)
        
        # Load the sound
        self.sound.load()
        options.grid(row=0,column=0, padx=20, pady=20, sticky='nesw')
        client.grid_columnconfigure(0, weight=1)
        client.grid_rowconfigure(0, weight=1)

        return self

    def save(self):
        """Save the item to the project"""
        self.project.render_outline() # update the outline

class Project():
    def __init__(self, client, name:str='New Project', version:str='1.0.0', namespace:str='minecraft', icon:dict={}, description:str='My custom music discs pack!', descType:str='String', items:list=[]):
        self.client = client
        self.logger = logging.getLogger('Project')

        self.last_descType = descType
        self.selectedItem:Item = None
        self.items = []
        self.is_playing = False
        
        # Variables
        self.desc = None
        self.DESC_ERROR = StringVar()
        self.NAME = StringVar()
        self.VERSION = StringVar()
        self.NAMESPACE = StringVar()
        self.ICON = StringVar()
        self.DESC_TYPE = StringVar()
        self.DESCRIPTION = StringVar()

        self.name = name
        self.version = version
        self.namespace = namespace
        self.descType = descType
        self.description = description
        self.icon = icon

        # Assets
        # if icon!=None:self.icon = Asset(self, AssetType.TEXTURE, self.ICON, (128,128), **icon)
        # else: self.icon = Asset(self, AssetType.TEXTURE, self.ICON, (128,128))

        self.index = 0
        for item in items:
            self.items.append(Item(self, self.index, **item))
            self.index+=1

    @property
    def name(self): return self.NAME.get()
    @name.setter
    def name(self, value:str): self.NAME.set(value)

    @property
    def version(self): return self.VERSION.get()
    @version.setter
    def version(self, value:str): self.VERSION.set(value)

    @property
    def namespace(self): return self.NAMESPACE.get()
    @namespace.setter
    def namespace(self, value:str): self.NAMESPACE.set(value)

    @property
    def descType(self): return self.DESC_TYPE.get()
    @descType.setter
    def descType(self, value:str): self.DESC_TYPE.set(value)

    @property
    def description(self): return self.DESCRIPTION.get()
    @description.setter
    def description(self, value:str): self.DESCRIPTION.set(value)

    @property
    def icon(self): return self._pack_icon
    @icon.setter
    def icon(self, value:dict):
        self._pack_icon = Asset(self, AssetType.TEXTURE, self.ICON, (128,128), hash=value.get('hash'), path=value.get('path'))
        self.ICON.set(self._pack_icon.path)
    
    def json(self):
        data = {
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

    def render_outline(self):
        """Render the items outline"""
        self.client.outline.delete(0, END)
        for item in self.items:
            self.client.outline.insert(END, item.name)
        return self

    def render_preview(self):
        """Render the pack preview"""
        try: self.preview.delete('all')
        except _tkinter.TclError: return
        
        title = self.client.format('dp', name=self.NAME.get(), version=self.VERSION.get())
        d = self.DESCRIPTION.get()
        if self.DESC_TYPE.get() == 'TextComponent':
            try:
                if self.desc!=None:
                    self.DESC_ERROR.set('')
                    self.desc.configure(border_color='green')

                dat = json.loads(d)
                if 'text' in dat: d = dat['text']
                elif 'translate' in dat: d = dat['translate']
                else:
                    self.DESC_ERROR.set('Missing required property "text" or "translate"')
                    self.desc.configure(border_color='red')

            except json.JSONDecodeError as err:
                if self.desc!=None:
                    self.desc.configure(border_color='red')
                    self.DESC_ERROR.set(err)

        start = self.client.max_str(d, 45)
        extra = self.client.max_str(d, 45, 'extra')
        desc = start + '\n'+ self.client.max_str(extra, 45)

        self.background_image = PhotoImage(file=os.path.join(LOCAL, 'assets', 'background.png'))
        self.preview.create_image(0,0, image=self.background_image, anchor=NW)
        
        # canvas.create_rectangle(2,2, 66,66, width=0, fill='black') # Icon
        fp = self.client.cache.get(hash=self.ICON.get())
        img = Image.open(fp=fp).resize((64,64), Image.NEAREST).convert('RGBA')
        self._icon = ImageTk.PhotoImage(img)
        self.preview.create_image(2,2, image=self._icon, anchor=NW, tags=['CHOOSE'])

        # 45 per line
        self.preview.create_text(68,1, text=str(title), font=self.client._fontBold, anchor=NW, justify=LEFT, fill='white')
        self.preview.create_text(68,20, text=str(desc), font=self.client._font, anchor=NW, justify=LEFT, fill='white')

    def render(self):
        """Render the project screen"""
        def update_desc_type(e):
            """Update the textarea size and convert from STRING to JSON vise versa"""
            if e!=self.last_descType: # only update if type is diffrent
                text = self.desc.get(0.0, 'end-1c')
                # Remove errors
                self.desc.configure(border_color='green')
                self.DESC_ERROR.set('')
                match e:
                    case 'String':
                        try:
                            data = json.loads(text)
                            if isinstance(data, dict):
                                if 'text' in data: text = data['text']
                                elif 'translate' in data: text = data['translate']
                            elif isinstance(data, list):
                                d = data[0]
                                if 'text' in d: text = d['text']
                                elif 'translate' in d: text = d['translate']
                            self.desc.delete(0.0, END)
                            self.desc.insert(0.0, str(text))

                        except (json.decoder.JSONDecodeError, IndexError): pass
                    case 'TextComponent':
                        data = {'text': text}
                        self.desc.delete(0.0, END)
                        self.desc.insert(0.0, json.dumps(data))
            # Update widget size
            match e:
                case 'String': self.desc.configure(width=140, height=2)
                case 'TextComponent': self.desc.configure(width=140, height=15)
            self.last_descType = e

        def update_desc(e): self.DESCRIPTION.set(self.desc.get(0.0, 'end-1c'))

        self.client.clear_screen()
        client:Tk = self.client.screen

        self.NAME.trace_add('write', lambda a,b,c: self.render_preview())
        self.VERSION.trace_add('write', lambda a,b,c: self.render_preview())
        self.DESCRIPTION.trace_add('write', lambda a,b,c: self.render_preview())
        self.DESC_TYPE.trace_add('write', lambda a,b,c: self.render_preview())

        project = CTkFrame(client)
        self.preview = Canvas(project, bd=0, highlightthickness=0, width=520, height=68, bg='black')
        self.preview.grid(row=0, columnspan=2,column=0, padx=10,pady=(10, 5),sticky=W)
        self.preview.tag_bind('CHOOSE', '<Button-1>', lambda e: self.icon.choose(callback=lambda e: self.render_preview()))
        self.render_preview()

        CTkLabel(project, text='Name').grid(row=1,column=0,padx=10, sticky=W)
        CTkEntry(project, textvariable=self.NAME).grid(row=2,column=0,pady=5,padx=10,sticky=EW)
        
        CTkLabel(project, text='Version').grid(row=3,column=0,padx=10, sticky=W)
        CTkEntry(project, textvariable=self.VERSION).grid(row=4,column=0,pady=5,padx=10,sticky=EW)
        
        CTkLabel(project, text='Namespace').grid(row=5,column=0,padx=10, sticky=W)
        namespace = CTkEntry(project, textvariable=self.NAMESPACE)
        self.client.validate(namespace, 'id')
        namespace.grid(row=6,column=0,pady=5,padx=10,sticky=EW)
        
        CTkLabel(project, text='Icon').grid(row=7,column=0,padx=10, sticky=W)
        CTkEntry(project, textvariable=self.ICON, state=DISABLED).grid(row=8,column=0, pady=5, padx=10, sticky=EW)
        
        CTkLabel(project, text='Description Type').grid(row=9,column=0,padx=10, sticky=W)
        CTkOptionMenu(project, values=['String', 'TextComponent'], variable=self.DESC_TYPE, command=update_desc_type).grid(row=10,column=0,pady=5,padx=10,sticky=EW)

        CTkLabel(project, text='Description').grid(row=11,column=0,padx=10, sticky=W)
        #TODO As you type (if rawjson) it should make the border red if it has invalid syntax (both JSON and JSON SCHEMA) add a little icon next to it or in the bottom corner of the Textbox.
        self.desc = CTkTextbox(project, undo=True, border_width=1, border_color='green')
        self.desc.delete(0.0, END)
        self.desc.insert(0.0, self.DESCRIPTION.get())
        self.desc.bind('<KeyRelease>', update_desc)
        self.desc.grid(row=12,column=0,pady=(5, 0),padx=10,sticky='nesw')

        CTkLabel(project, textvariable=self.DESC_ERROR, anchor=W, text_color='red').grid(row=13, column=0, pady=(0, 10),padx=10,sticky=EW)

        project.grid(row=0, column=0, padx=20, pady=20, sticky='nesw')

        # Responsive
        project.grid_columnconfigure(0, weight=1)
        project.grid_rowconfigure(12, weight=1)
        client.grid_columnconfigure(0, weight=1)
        client.grid_rowconfigure(0, weight=1)

        update_desc_type(self.DESC_TYPE.get())
        return self

    def add_item(self, item:Item):
        """Adds a new item to the project"""
        self.items.insert(0, item)
        self.adjust_index()

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
                    self.logger.warning('Failed to delete the item as it was not found!')
                    messagebox.showwarning('Item not found', 'Failed to delete the item as it was not found!', parent=self.client)

    def adjust_index(self):
        """Updates all items with their new index values"""
        self.index = 0
        for item in self.items:
            item.index = self.index
            self.index+=1

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
        if self.selectedItem!=None: self.selectedItem.render()

    def _import(self): #TODO make it import project files.
        filetypes = [('Project', '*.mcdisc')]
        fp = filedialog.askopenfilename(defaultextension='.mcdisc', parent=self.client, filetypes=filetypes, title='Import')
        if fp!='':
            if fp.endswith('.mcdisc'):
                project:Project = self.client.open(fp)
                if project!=None:
                    for item in project.items: self.items.append(item)
                    self.render_outline()
                    self.adjust_index()
                    return True

        return False

    def render_description(self):
        """Render the description as a STRING or JSON"""
        if self.descType == 'rawjson':
            try: return json.loads(self.description)
            except json.decoder.JSONDecodeError: return self.description
        else: return self.description

    def export(self, type:str):
        path = filedialog.askdirectory(mustexist=False, parent=self.client, title='Export')

        def remove_dir(path:str):
            if os.path.exists(path) and os.path.isdir(path):
                for name in os.listdir(path):
                    file = os.path.join(path, name)
                    if os.path.isfile(file): os.remove(file)
                    elif os.path.isdir(file): remove_dir(file)
                try: os.removedirs(path)
                except FileNotFoundError: pass

        if path!='':
            if type=='java':
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
                            'description': self.render_description() # Should get converted to JSON if type is set to rawjson
                        }
                    }
                    manifest.write(json.dumps(data))
                if self.icon!=None: self.icon.export(os.path.join(dp_path, 'pack.png'))

                # Resourcepack
                rp_name = self.client.format('rp', name=self.name, version=self.version)
                rp_path = os.path.join(path, rp_name)
                os.makedirs(os.path.join(rp_path, 'assets', 'record', 'models', 'item'), exist_ok=True)
                os.makedirs(os.path.join(rp_path, 'assets', self.namespace, 'lang'), exist_ok=True)
                os.makedirs(os.path.join(rp_path, 'assets', self.namespace, 'sounds', 'records'), exist_ok=True)
                os.makedirs(os.path.join(rp_path, 'assets', self.namespace, 'textures', 'item'), exist_ok=True)
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
                                                    'tag': '{id:"'+self.namespace+':'+item.id+'",record:{power_level: '+str(item.power_level)+',command:"execute as @e[tag=Jukebox,limit=1,sort=nearest] at @s run playsound '+self.namespace+':music_disc.'+item.id.replace('music_disc_', '')+' record @a ~ ~ ~ 4 1 0"},HideFlags:32,CustomModelData:'+str(item.custom_model_data)+',display:{Name:\'{"translate":"item.'+self.namespace+'.'+item.id+'","italic": false}\',Lore:[\'{"translate":"item.'+self.namespace+'.'+item.id+'.desc","color":"gray","italic": false}\']}}'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                        file.write(json.dumps(table))
                    
                    # Resroucepack
                    item.sound.export(os.path.join(rp_path, 'assets', self.namespace, 'sounds', 'records', '%s.ogg'%(item.id.replace('music_disc_',''))))
                    item.texture.export(os.path.join(rp_path, 'assets', self.namespace, 'textures', 'item', '%s.png'%(item.id)))
                    with open(os.path.join(rp_path, 'assets', 'record', 'models', 'item', '%s_%s.json'%(mc_item, item.custom_model_data)), 'w') as model:
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
                with open(os.path.join(rp_path, 'assets', self.namespace, 'lang', '%s.json'%(self.client.c.getItem('locale'))), 'w') as file: file.write(json.dumps(LANG))
                with open(os.path.join(rp_path, 'assets', self.namespace, 'sounds.json'), 'w') as file: file.write(json.dumps(SOUNDS))

                # ZIP packs
                if self.client.c.getItem('archiveOutput')=='True':
                    shutil.make_archive(dp_path, 'zip', dp_path)
                    shutil.make_archive(rp_path, 'zip', rp_path)
                    remove_dir(dp_path)
                    remove_dir(rp_path)

                confirm = messagebox.askyesno('Export', 'Successfully exported "%s". Do you want to open the output folder?'%(self.name))
                if confirm: os.startfile(path)
                return True
            
            elif type=='bedrock':
                self.logger.info('bedrock exporter has not been added yet!')
                return True

            else: return False
        return False
