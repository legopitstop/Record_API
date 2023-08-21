from customtkinter import CTkLabel, CTkEntry, CTkOptionMenu, CTkTextbox, CTkFrame, CTkFont, CTkButton
from tkinter import CENTER, DISABLED, E, END, EW, LEFT, NW, S, W, Canvas, Tk, filedialog, PhotoImage, messagebox, Canvas, TclError, Menu
from tkinter.font import Font
from PIL import Image, ImageTk
from tktooltip import ToolTip
import _tkinter
import jsonschema
import textwrap
import os
import logging
import nbtlib
import json
import enum
import soundfile

LOCAL = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('Client')

def render_rawjson(canvas:Canvas, x:int, y:int, text:dict|str) -> bool|str:
    def get_color(color:str):
        color_names = {
            'dark_red': '#be0000',
            'red': '#fe3f3f',
            'gold': '#d9a334',
            'yellow': '#fefe3f',
            'dark_green': '#00be00',
            'green': '#3ffe3f',
            'aqua': '#3ffefe',
            'dark_aqua': '#00bebe',
            'dark_blue': '#0000be',
            'blue': '#3f3ffe',
            'light_purple': '#fe3ffe',
            'dark_purple': '#be00be',
            'white': '#ffffff',
            'gray': '#bebebe',
            'dark_gray': '#3f3f3f',
            'black': '#000000'
        }

        if color.startswith('#'):
            return True, color
        else:
            try:
                return True, color_names[color]
            except KeyError:
                return False, f'Invalid color name "{color}"'

    def get_font(obj:dict):
        weight = 'bold' if obj.get('bold', None) is not None and obj.get('bold', None) == True or obj.get('bold', None) == 'true' else 'normal'
        slant = 'italic' if obj.get('italic', None) is not None and obj.get('italic', None) == True or obj.get('italic', None) == 'true' else 'roman'
        underline = True if obj.get('underlined', None) is not None and obj['underlined'] == True or obj.get('underlined', None) == 'true' else False
        overstrike = True if obj.get('strikethrough', None) is not None and obj.get('strikethrough', None) == True or obj.get('strikethrough', None) == 'true' else False
        # obfuscated = True if obj.get('obfuscated', None) is not None and obj.get('obfuscated', None) == True or obj.get('obfuscated', None) == 'true' else False
        return Font(family='Monocraft Nerd Font', weight=weight, slant=slant, underline=underline, overstrike=overstrike)

    if isinstance(text, dict):
        content = str(text.get('text', text.get('translate')))
        valid, color = get_color(text.get('color', 'gray'))
        if valid is False: return color
        try:
            canvas.create_text(x,y, text=content, font=get_font(text), anchor=NW, justify=LEFT, fill=color, tags=['DESC'])
        except TclError as err:
            return err

    elif isinstance(text, list):
        _x = x
        _y = y
        for t in text:
            valid, color = get_color(t.get('color', 'gray'))
            if valid is False: return color
            context = str(t.get('text', t.get('translate')))
            font = get_font(t)
            canvas.create_text(_x,_y, text=context, font=font, anchor=NW, justify=LEFT, fill=color, tags=['DESC'])
            _x += font.measure(context)

    return True

class Picture(Canvas):
    def __init__(self, master:Tk, image:Image=None, width:int=None, height:int=None, text:str=None, fg:str='black', bg:str='white',**kw):
        """Display an image on the window"""
        super().__init__(master, borderwidth=0, highlightthickness=0)
        self.image = Image.open(os.path.join(LOCAL, 'resources', 'missing.png'))
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

class AssetType(enum.Enum):
    TEXTURE = 'texture'
    SOUND = 'sound'

class ClientAsset:
    
    def choose(self, widget=None, callback=None):
        """Choose a file"""
        if self.type==AssetType.TEXTURE:
            defaultextension = '.png'
            filetypes = [('Images', '.png .tif .tiff .bmp .jpg .jpeg .gif .eps .raw')]
        
        elif self.type==AssetType.SOUND:
            defaultextension = '.ogg'
            # exts =''
            # for i in [x.lower() for x in soundfile.available_formats().keys()]: exts+=' .'+i
            filetypes = [('Sounds', '.ogg')]
        
        else:
            defaultextension = None
            filetypes = [('Any', '*.*')]

        # TODO - move to client
        fp = filedialog.askopenfilename(defaultextension=defaultextension, filetypes=filetypes, initialdir=self.PATH.get(), parent=self.project.client)
        if os.path.exists(fp) and os.path.isfile(fp):
            if self.type == AssetType.SOUND:
                with soundfile.SoundFile(fp, 'r') as f:
                    if f.channels == 1:
                        self.path = fp
                    else:
                        msg = f"This sound file contains {f.channels} channels. Please convert it to mono channel. (I recommend using Audacity)"
                        logger.warning(msg)
                        messagebox.showwarning('Open File', msg, parent=self.project.client)

            elif self.type == AssetType.TEXTURE:
                self.path = fp
                if widget is not None: widget.configure(image=self.get_image())
            if callback!=None: callback(fp)

class ClientItem:
    def edit_menu(self, type:str=None):
        m:Menu = self.project.client.edit
        m.delete(0, 'end')
        match type:
            case 'item':
                m.add_command(label='Copy', command=self.project.client.copy_item)
                m.add_command(label='Paste', command=self.project.client.paste_item)
                m.add_command(label='Duplicate', command=self.project.client.duplicate_item)
                m.add_separator()
                m.add_command(label='Rename', command=self.project.client.rename_item)
                m.add_command(label='Delete', command=self.project.client.delete_item, foreground='red')
            case 'nbt':
                ctx_exp = Menu(m, tearoff=False)
                ctx_exp.add_command(label='NBT', command=lambda: self.export_nbt('nbt'))
                ctx_exp.add_command(label='SNBT', command=lambda: self.export_nbt('snbt'))

                m.add_command(label='Prettify', command=self.prettify_nbt)
                m.add_command(label='Minifiy', command=self.minify_nbt)
                m.add_separator()
                m.add_command(label='Cut', command=self.cut_nbt)
                m.add_command(label='Copy', command=self.copy_nbt)
                m.add_command(label='Paste', command=self.paste_nbt)
                m.add_separator()
                m.add_command(label='Import', command=self.import_nbt)
                m.add_cascade(label='Export As', menu=ctx_exp)

    def prettify_nbt(self):
        try:
            obj:nbtlib.Compound = nbtlib.parse_nbt(self.nbt)
            string = obj.snbt(indent=4, compact=False)
            self.nbt_entry.delete(0.0, 'end')
            self.nbt_entry.insert(0.0, string)
            self.nbt = string
        except: pass

    def minify_nbt(self):
        try:
            obj:nbtlib.Compound = nbtlib.parse_nbt(self.nbt)
            string = obj.snbt(compact=True)
            self.nbt_entry.delete(0.0, 'end')
            self.nbt_entry.insert(0.0, string)
            self.nbt = string
        except: pass

    def cut_nbt(self):
        try:
            if self.nbt_entry.selection_get():
                data = self.nbt_entry.selection_get()
                self.nbt_entry.clipboard_clear()
                self.nbt_entry.clipboard_append(data)
                self.nbt_entry.delete('sel.first', 'sel.last')
                self.update_nbt()
        except: pass

    def copy_nbt(self):
        try:
            if self.nbt_entry.selection_get():
                data = self.nbt_entry.selection_get()
                self.nbt_entry.clipboard_clear()
                self.nbt_entry.clipboard_append(data)
                self.update_nbt()
        except: pass

    def paste_nbt(self):
        data = self.nbt_entry.clipboard_get()
        self.nbt_entry.insert('insert', data)
        self.update_nbt()

    def import_nbt(self):
        fp = filedialog.askopenfilename(defaultextension='.snbt', filetypes=[('NBT', '.nbt .snbt')], title='Import NBT', parent=self.project.client)
        if fp!='':
            try:
                if fp.endswith('.snbt'):
                    with open(fp, 'r') as r:
                        nbtFile = nbtlib.parse_nbt(r.read())
                else:
                    nbtFile = nbtlib.load(fp)                    
                snbt = nbtFile.snbt(indent=4, compact=False)
                self.nbt_entry.delete(0.0, 'end')
                self.nbt_entry.insert(0.0, str(snbt))
                self.update_nbt()
            except Exception as err:
                msg = 'Failed to parse NBT: %s'%err
                logger.warning(msg)
                messagebox.showwarning('Import NBT', msg)

    def export_nbt(self, type:str):
        fp = filedialog.asksaveasfilename(defaultextension='.'+type.lower(), filetypes=[(type.upper(), '.'+type.lower())], initialdir=os.path.join(os.path.expanduser('~'), 'Downloads'), initialfile=self.name+'.'+type.lower(), parent=self.client, title='Export')
        if fp!='':
            match type.lower():
                case 'nbt':
                    try:
                        obj:nbtlib.Compound = nbtlib.parse_nbt(self.nbt_entry.get(0.0, 'end'))
                        if not isinstance(obj, nbtlib.Compound):
                            msg = f"Expected Compound but got '{obj.__class__.__name__}' instead"
                            logger.warning(msg)
                            messagebox.showwarning('Export', msg)
                            return
                        new_file = nbtlib.File(obj)
                        new_file.save(fp)
                    except Exception as err:
                        logger.warning(err)
                        messagebox.showwarning('Export', err)
                case 'snbt':
                    try:
                        obj:nbtlib.Compound = nbtlib.parse_nbt(self.nbt_entry.get(0.0, 'end'))
                        if not isinstance(obj, nbtlib.Compound):
                            msg = f"Expected Compound but got '{obj.__class__.__name__}' instead"
                            logger.warning(msg)
                            messagebox.showwarning('Export', msg)
                            return
                        with open(fp, 'w') as w: w.write(obj.snbt(indent=4, compact=False))
                    except Exception as err:
                        logger.warning(err)
                        messagebox.showwarning('Export', err)

    def toggle_advanced(self):
        if self.project.client.advanced_options:
            self.project.client.advanced_options = False
            self.advanced_options.grid_forget()            
        else:
            self.project.client.advanced_options = True
            self.advanced_options.grid(row=27,column=0, padx=10, sticky=EW)

    def validate_nbt(self, e:str) -> bool|str:
        try:
            tag:nbtlib.Compound = nbtlib.parse_nbt(e)
            if not isinstance(tag, nbtlib.Compound):
                return str(f"Expected Compound but got '{tag.__class__.__name__}' instead")
            return True
        except nbtlib.InvalidLiteral as err:
            return str(err)

    def update_nbt(self, e=None):
        self.NBT.set(self.nbt_entry.get(0.0, 'end-1c'))
        valid = self.validate_nbt(self.NBT.get())
        if valid == True:
            self.NBT_ERROR.set('')
            self.nbt_entry.configure(border_color='green')
        else:
            self.NBT_ERROR.set(valid)
            self.nbt_entry.configure(border_color='red')

    def render(self):
        """Render the item screen"""
        self.edit_menu('item')

        def popup(e):
            try:
                ctx.tk_popup(e.x_root, e.y_root)
            finally:
                ctx.grab_release()

        self.project.client.clear_screen()
        client:Tk = self.project.client.screen
        power_level_values = [str(x) for x in range(1, 16)]
        obtain_values = ['none', 'creeper']
        
        options = CTkFrame(client)

        # TODO
        # - Split definition (CTkLabel, etc) and geometry (.grid) & do the same for Project.
        # - Move .render() to its own class (ClientItem). Then make this class a subclass of ClientItem. do same for project.
        self.name_lbl = CTkLabel(options, text='Name', anchor=E, font=CTkFont(size=15))
        self.name_desc = CTkLabel(options, text='Name of this Music Disc.', anchor=E)
        self.name_entry = CTkEntry(options, textvariable=self.NAME)
        self.name_entry.bind('<KeyRelease>', lambda x: self.project.render_outline())

        self.artest_lbl = CTkLabel(options, text='Artest', anchor=E, font=CTkFont(size=15))
        self.artest_desc = CTkLabel(options, text='The artest who made this music.', anchor=E)
        self.artest_entry = CTkEntry(options, textvariable=self.ARTEST)

        self.id_lbl = CTkLabel(options, text='ID', anchor=E, font=CTkFont(size=15))
        self.id_desc = CTkLabel(options, text='The custom item ID for this item.', anchor=E)
        self.id_entry = CTkEntry(options, textvariable=self.ID)
        self.project.client.validate(self.id_entry, 'id')

        self.power_level_lbl = CTkLabel(options, text='Power Level', anchor=E, font=CTkFont(size=15))
        self.power_level_desc = CTkLabel(options, text='The redstone power level to output.', anchor=E)
        self.power_level_entry = CTkOptionMenu(options, values=power_level_values, variable=self.POWER_LEVEL)

        self.obtain_lbl = CTkLabel(options, text='Obtain', anchor=E, font=CTkFont(size=15))
        self.obtain_desc = CTkLabel(options, text='How to get this disc in survival.', anchor=E)
        self.obtain_entry = CTkOptionMenu(options, values=obtain_values, variable=self.OBTAIN)

        pic = Picture(options, image=self.texture.get_image(), width=100, height=100, bg=options['bg'])
        pic.bind('<Button-1>', lambda e: self.texture.choose(pic))
        ToolTip(pic, msg='Left Click to choose file')
        
        self.texture_lbl = CTkLabel(options, text='Texture', anchor=E, font=CTkFont(size=15))
        self.texture_desc = CTkLabel(options, text='The image to use for this item.', anchor=E)
        self.texture_entry = CTkEntry(options, textvariable=self.texture.PATH, state=DISABLED)
        self.texture_entry.bind('<Double-Button-1>', lambda e: self.texture.choose(pic))

        snd = Picture(options, image=Image.open(os.path.join(LOCAL, 'resources', 'jukebox.png')).convert('RGBA'), width=100, height=100, bg=options['bg'])
        snd.bind('<Button-3>', lambda e: self.sound.toggle())
        snd.bind('<Button-1>', lambda e: self.sound.choose(snd))
        ToolTip(snd, msg='Left Click to choose file\nRight Click to play/stop sound')

        self.sound_lbl = CTkLabel(options, text='Sound', anchor=E, font=CTkFont(size=15))
        self.sound_desc = CTkLabel(options, text='The sound file to play. (Recommended mono channel)', anchor=E)
        self.sound_entry = CTkEntry(options, textvariable=self.sound.PATH, state=DISABLED)
        self.sound_entry.bind('<Double-Button-1>', lambda e: self.sound.choose(snd))

        # ADVANCED
        self.advanced_btn = CTkButton(options, text='Advanced', command=self.toggle_advanced)
        self.advanced_options = CTkFrame(options)

        # Validate NBT
        self.nbt_lbl = CTkLabel(self.advanced_options, text='NBT', anchor=E, font=CTkFont(size=15))
        self.nbt_desc = CTkLabel(self.advanced_options, text='Additional NBT data to apply.', anchor=E)
        self.nbt_entry = CTkTextbox(self.advanced_options, undo=True, border_width=1, border_color='green')
        self.nbt_entry.delete(0.0, END)
        self.nbt_entry.insert(0.0, self.NBT.get())
        self.nbt_entry.bind('<KeyRelease>', self.update_nbt)
        self.nbt_entry.bind('<Button-3>', popup)
        self.nbt_entry.bind('<FocusIn>', lambda x: self.edit_menu('nbt'))
        self.nbt_entry.bind('<FocusOut>', lambda x: self.edit_menu('item'))

        ctx = Menu(self.advanced_options, tearoff=False)
        ctx_exp = Menu(ctx, tearoff=False)
        ctx_exp.add_command(label='NBT', command=lambda: self.export_nbt('nbt'))
        ctx_exp.add_command(label='SNBT', command=lambda: self.export_nbt('snbt'))

        ctx.add_command(label='Prettify', command=self.prettify_nbt)
        ctx.add_command(label='Minifiy', command=self.minify_nbt)
        ctx.add_separator()
        ctx.add_command(label='Cut', command=self.cut_nbt)
        ctx.add_command(label='Copy', command=self.copy_nbt)
        ctx.add_command(label='Paste', command=self.paste_nbt)
        ctx.add_separator()
        ctx.add_command(label='Import', command=self.import_nbt)
        ctx.add_cascade(label='Export As', menu=ctx_exp)
        
        self.nbt_error = CTkLabel(self.advanced_options, textvariable=self.NBT_ERROR, anchor=W, text_color='red')
        
        self.model_data_lbl = CTkLabel(self.advanced_options, text='Custom Model Data', anchor=E, font=CTkFont(size=15))
        self.model_data_desc = CTkLabel(self.advanced_options, text='The model data value to use. (1-500)', anchor=E)
        self.model_data_entry = CTkEntry(self.advanced_options, textvariable=self.CUSTOM_MODEL_DATA)
        self.project.client.validate(self.model_data_entry, 'custom_model_data')
        self.roll_btn = CTkLabel(self.advanced_options, text='roll', text_color='red', anchor='w')
        self.roll_btn.bind('<Button-1>', lambda x: self.roll_model_data())

        # Load the sound
        self.sound.load()
        options.grid(row=0,column=0, padx=20, pady=20, sticky='nesw')

        self.update_nbt()

        # Geometry
        self.name_lbl.grid(row=0,column=0, padx=10, sticky=W)
        self.name_desc.grid(row=1,column=0, padx=10, sticky=W)
        self.name_entry.grid(row=2, column=0, pady=5, padx=10, sticky=EW)
        self.artest_lbl.grid(row=3,column=0, padx=10, sticky=W)
        self.artest_desc.grid(row=4,column=0, padx=10, sticky=W)
        self.artest_entry.grid(row=5, column=0, pady=5, padx=10, sticky=EW)
        self.id_lbl.grid(row=6,column=0, padx=10, sticky=W)
        self.id_desc.grid(row=7,column=0, padx=10, sticky=W)
        self.id_entry.grid(row=8, column=0, pady=5, padx=10, sticky=EW)
        self.power_level_lbl.grid(row=9,column=0, padx=10, sticky=W)
        self.power_level_desc.grid(row=10,column=0, padx=10, sticky=W)
        self.power_level_entry.grid(row=11,column=0, pady=5, padx=10, sticky=EW)
        self.obtain_lbl.grid(row=12,column=0, padx=10, sticky=W)
        self.obtain_desc.grid(row=13,column=0, padx=10, sticky=W)
        self.obtain_entry.grid(row=14, column=0, pady=5, padx=10, sticky=EW)
        pic.grid(row=15, column=0, padx=10,pady=5,sticky=W)
        self.texture_lbl.grid(row=16,column=0, padx=10, sticky=W)
        self.texture_desc.grid(row=17,column=0, padx=10, sticky=W)
        self.texture_entry.grid(row=18,column=0, pady=5, padx=10, sticky=EW)
        snd.grid(row=19,column=0, padx=10,pady=5,sticky=W)
        self.sound_lbl.grid(row=20,column=0, padx=10, sticky=W)
        self.sound_desc.grid(row=21,column=0, padx=10, sticky=W)
        self.sound_entry.grid(row=22,column=0, pady=5, padx=10, sticky=EW)
        self.advanced_btn.grid(row=26,column=0, pady=(10,5), padx=10, sticky=EW)
        self.nbt_lbl.grid(row=0,column=0, padx=10, sticky=W)
        self.nbt_desc.grid(row=1,column=0, padx=10, sticky=W)
        self.nbt_entry.grid(row=2, column=0, pady=5, padx=10, sticky=EW)
        self.nbt_error.grid(row=3, column=0, pady=(0, 10),padx=10,sticky=EW)
        self.model_data_lbl.grid(row=4,column=0, padx=10, sticky=W)
        self.model_data_desc.grid(row=5,column=0, padx=10, sticky=W)
        self.model_data_entry.grid(row=6, column=0, pady=5, padx=10, sticky=EW)
        self.roll_btn.grid(row=6, column=1, pady=5, padx=10, sticky='w')

        # Show advanced options if true.
        if self.project.client.advanced_options:
            self.advanced_options.grid(row=27,column=0, padx=10, sticky=EW)

        # Responsive
        options.grid_columnconfigure(0, weight=1)
        self.advanced_options.grid_columnconfigure(0, weight=1)
        client.grid_columnconfigure(0, weight=1)
        client.grid_rowconfigure(0, weight=1)


        return self

class ClientProject:
    def edit_menu(self, type:str=None):
        m:Menu = self.client.edit
        m.delete(0, 'end')

        match type:
            case 'desc':
                ctx_export = Menu(m, tearoff=False)
                if self.descType == 'TextComponent':
                    m.add_command(label='Prettify', command=self.prettify_description)
                    m.add_command(label='Minifiy', command=self.minify_description)
                    m.add_separator()

                    ctx_export.add_command(label='JSON', command=lambda: self.export_description('json'))

                else:
                    ctx_export.add_command(label='TXT', command=lambda: self.export_description('txt'))

                m.add_command(label='Cut', command=self.cut_description)
                m.add_command(label='Copy', command=self.copy_description)
                m.add_command(label='Paste', command=self.paste_description)
                m.add_separator()
                m.add_command(label='Import', command=self.import_description)
                m.add_cascade(label='Export As', menu=ctx_export)

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
        
        self.background_image = PhotoImage(file=os.path.join(LOCAL, 'resources', 'background.png'))
        self.preview.create_image(0,0, image=self.background_image, anchor=NW)
        
        # ICON
        img = self.icon.get_image().resize((64,64), Image.NEAREST).convert('RGBA')
        self._cache = ImageTk.PhotoImage(img)
        self.preview.create_image(2,2, image=self._cache, anchor=NW, tags=['CHOOSE'])

        # TITLE
        title = self.client.format('dp', name=self.NAME.get(), version=self.VERSION.get())
        self.preview.create_text(68,1, text=str(title), font=Font(family='Monocraft Nerd Font', weight='bold'), anchor=NW, justify=LEFT, fill='white', tags=['TITLE'])
        self.preview.tag_bind('TITLE', '<Button-1>', lambda e: self.title_entry.focus())

        d = self.DESCRIPTION.get()
        if self.DESC_TYPE.get() == 'TextComponent':
            try:
                data = json.loads(d)
            except json.JSONDecodeError as err:
                logger.warning(err)
                return
        else:
            desc = textwrap.fill(d, 45)

        if self.DESC_TYPE.get() == 'TextComponent':
            res = render_rawjson(self.preview, 68, 20, data)
            if res is not True:
                self.DESC_ERROR.set(res)
                self.description_entry.configure(border_color='red')
        else:
            self.preview.create_text(68,20, text=str(desc), font=Font(family='Monocraft Nerd Font'), anchor=NW, justify=LEFT, fill='#bebebe', tags=['DESC'])

        self.preview.tag_bind('DESC', '<Button-1>', lambda e: self.description_entry.focus())

    def prettify_description(self):
        try:
            obj = json.loads(self.description)
            string = json.dumps(obj, indent=4, separators=(', ', ': '))
            self.description_entry.delete(0.0, 'end')
            self.description_entry.insert(0.0, string)
            self.description = string
        except:
            pass

    def minify_description(self):
        try:
            obj = json.loads(self.description)
            string = json.dumps(obj, separators=(',', ':'))
            self.description_entry.delete(0.0, 'end')
            self.description_entry.insert(0.0, string)
            self.description = string
        except:
            pass

    def cut_description(self):
        try:
            if self.description_entry.selection_get():
                data = self.description_entry.selection_get()
                self.description_entry.clipboard_clear()
                self.description_entry.clipboard_append(data)
                self.description_entry.delete('sel.first', 'sel.last')
                self.update_desc()
        except: pass

    def copy_description(self):
        try:
            if self.description_entry.selection_get():
                data = self.description_entry.selection_get()
                self.description_entry.clipboard_clear()
                self.description_entry.clipboard_append(data)
                self.update_desc()
        except: pass

    def paste_description(self):
        data = self.description_entry.clipboard_get()
        self.description_entry.insert('insert', data)
        self.update_desc()

    def import_description(self):
        fp = filedialog.askopenfilename(defaultextension='.mcmeta', filetypes=[('TEXT', '.txt .json .mcmeta')], initialdir=os.path.join(os.path.expanduser('~'), 'Downloads'), initialfile='pack.mcmeta', parent=self.client, title='Import')
        if fp !='':
            with open(fp, 'r') as r:
                if fp.endswith('.json'):
                    try:
                        obj = json.load(r)
                        string = json.dumps(obj, indent=4, separators=(', ', ': '))
                        self.description_entry.delete(0.0, 'end')
                        self.description_entry.insert(0.0, string)
                        self.description = string
                        self.descType = 1
                    except Exception as err:
                        logger.warning(err)
                        messagebox.showwarning('Import', err)
                elif fp.endswith('.mcmeta'):
                    obj = json.load(r)
                    if 'pack' in obj and 'description' in obj['pack']:
                        desc = obj['pack']['description']
                        if isinstance(desc, str):
                            self.description_entry.delete(0.0, 'end')
                            self.description_entry.insert(0.0, desc)
                            self.description = desc
                            self.descType = 0
                        elif isinstance(desc, (dict, list)):
                            string = json.dumps(desc, indent=4, separators=(', ', ': '))
                            self.description_entry.delete(0.0, 'end')
                            self.description_entry.insert(0.0, string)
                            self.description = string
                            self.descType = 1
                        else:
                            msg = f"Expected str, dict or list but got '{desc.__class__.__name__}' instead"
                            logger.warning(msg)
                            messagebox.showwarning('Import', msg)
                    else:
                        msg = f"pack.description was not found!"
                        logger.warning(msg)
                        messagebox.showwarning('Import', msg)
                else:
                    self.description_entry.delete(0.0, 'end')
                    self.description_entry.insert(0.0, r.read())
                    self.description = r.read()
                    self.descType = 0
        self.update_desc()

    def export_description(self,type:str):
        fp = filedialog.asksaveasfilename(defaultextension='.'+type.lower(), filetypes=[(type.upper(), '.'+type.lower())], initialdir=os.path.join(os.path.expanduser('~'), 'Downloads'), initialfile=self.name+'.'+type.lower(), parent=self.client, title='Export')
        if fp!='':
            match type.lower():
                case 'txt':
                    with open(fp, 'w') as w:
                        w.write(str(self.description_entry.get(0.0, 'end')))
                case 'json':
                    try:
                        obj = json.loads(self.description_entry.get(0.0, 'end'))
                        with open(fp, 'w') as w:
                            w.write(json.dumps(obj, indent=4, separators=(', ', ': ')))
                    except Exception as err:
                        logger.warning(err)
                        messagebox.showwarning('Export', err)

    def update_desc_type(self,e):
        """Update the textarea size and convert from STRING to JSON vise versa"""
        if e!=self.lastDescType: # only update if type is diffrent
            text = self.description_entry.get(0.0, 'end-1c')
            match e:
                case 'String':
                    try:
                        data = json.loads(text)
                        text = 'none'
                        if isinstance(data, dict):
                            text = data['text'] if data.get('text', None) is not None else data['translate'] if data.get('translate', None) is not None else ''
                        elif isinstance(data, list) and len(data) >= 1:
                            t = []
                            for i in data:
                                t.append(i['text'] if i.get('text', None) is not None else i['translate'] if i.get('translate', None) is not None else '')
                            text = ' '.join(t)
                        self.description_entry.delete(0.0, END)
                        self.description_entry.insert(0.0, str(text))
                    except (json.decoder.JSONDecodeError, IndexError): pass
                case 'TextComponent':
                    data = {'text': text}
                    self.description_entry.delete(0.0, END)
                    self.description_entry.insert(0.0, json.dumps(data))

            self.edit_menu('desc')
        self.lastDescType = e
        self.update_desc()

    def validate_desc(self,e=None) -> bool|str:
        match self.descType:
            case 'TextComponent':
                try:
                    instance = json.loads(self.description)
                    with open(os.path.join(LOCAL, 'resources', 'schemas', 'textcomponent.json')) as req:
                        schema = json.load(req)
                        jsonschema.validate(instance, schema)
                        return True
                except jsonschema.ValidationError as err:
                    return str(err.message)                    
                except Exception as err:
                    return str(err)
            case 'String':
                return True

    def update_desc(self,e=None):
        self.DESCRIPTION.set(self.description_entry.get(0.0, 'end-1c'))
        valid = self.validate_desc(self.DESCRIPTION.get())
        if valid == True:
            self.DESC_ERROR.set('')
            self.description_entry.configure(border_color='green')
        else:
            self.DESC_ERROR.set(valid)
            self.description_entry.configure(border_color='red')

    def render(self):
        """Render the project screen"""
        self.client.rpc_state('project')

        self.edit_menu()

        def popup(e):
            try:
                ctx.delete(0, 'end')
                ctx_export.delete(0, 'end')
                if self.descType == 'TextComponent':
                    ctx.add_command(label='Prettify', command=self.prettify_description)
                    ctx.add_command(label='Minifiy', command=self.minify_description)
                    ctx.add_separator()

                    ctx_export.add_command(label='JSON', command=lambda: self.export_description('json'))

                else:
                    ctx_export.add_command(label='TXT', command=lambda: self.export_description('txt'))

                ctx.add_command(label='Cut', command=self.cut_description)
                ctx.add_command(label='Copy', command=self.copy_description)
                ctx.add_command(label='Paste', command=self.paste_description)
                ctx.add_separator()
                ctx.add_command(label='Import', command=self.import_description)
                ctx.add_cascade(label='Export As', menu=ctx_export)

                ctx.tk_popup(e.x_root, e.y_root)

            finally:
                ctx.grab_release()

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

        self.title_lbl = CTkLabel(project, text='Title', font=CTkFont(size=15))
        self.title_desc = CTkLabel(project, text='The name of the pack.')
        self.title_entry = CTkEntry(project, textvariable=self.NAME)

        self.version_lbl = CTkLabel(project, text='Version', font=CTkFont(size=15))
        self.version_desc = CTkLabel(project, text='The version of the pack.')
        self.version_entry = CTkEntry(project, textvariable=self.VERSION)

        self.namespace_lbl = CTkLabel(project, text='Namespace', font=CTkFont(size=15))
        self.namespace_desc = CTkLabel(project, text='The namespace for textures, sounds and items.')
        self.namespace_entry = CTkEntry(project, textvariable=self.NAMESPACE)
        self.client.validate(self.namespace_entry, 'id')

        self.icon_lbl = CTkLabel(project, text='Icon', font=CTkFont(size=15))
        self.icon_desc = CTkLabel(project, text='The icon for the pack. (Recommended 128x128)')
        self.icon_entry = CTkEntry(project, textvariable=self.icon.PATH, state=DISABLED)
        self.icon_entry.bind('<Double-Button-1>', lambda e: self.icon.choose(callback=lambda e: self.render_preview()))

        self.description_type_lbl = CTkLabel(project, text='Description Type', font=CTkFont(size=15))
        self.description_type_desc = CTkLabel(project, text="How to interpit 'Description'. 'String' - Exact text. (Formatting is not supported). 'TextComponent' - Raw JSON text format.", anchor='w')
        self.description_type_entry = CTkOptionMenu(project, values=['String', 'TextComponent'], variable=self.DESC_TYPE, command=self.update_desc_type)

        self.description_lbl = CTkLabel(project, text='Description')
        self.description_desc = CTkLabel(project, text='Text to display under the title.')

        self.description_entry = CTkTextbox(project, undo=True, border_width=1, border_color='green')
        self.description_entry.delete(0.0, END)
        self.description_entry.insert(0.0, self.DESCRIPTION.get())
        self.description_entry.bind('<KeyRelease>', self.update_desc)
        self.description_entry.bind('<Button-3>', popup)
        self.description_entry.bind('<FocusIn>', lambda x: self.edit_menu('desc'))
        self.description_entry.bind('<FocusOut>', lambda x: self.edit_menu())

        ctx = Menu(project, tearoff=False)
        ctx_export = Menu(ctx, tearoff=False)

        self.description_error = CTkLabel(project, textvariable=self.DESC_ERROR, anchor=W, text_color='red')

        self.render_preview()
        self.update_desc()

        # Geometry
        self.title_lbl.grid(row=1,column=0,padx=10, sticky=W)
        self.title_desc.grid(row=2,column=0,padx=10, sticky=W)
        self.title_entry.grid(row=3,column=0,pady=5,padx=10,sticky=EW)
        self.version_lbl.grid(row=4,column=0,padx=10, sticky=W)
        self.version_desc.grid(row=5,column=0,padx=10, sticky=W)
        self.version_entry.grid(row=6,column=0,pady=5,padx=10,sticky=EW)
        self.namespace_lbl.grid(row=7,column=0,padx=10, sticky=W)
        self.namespace_desc.grid(row=8,column=0,padx=10, sticky=W)
        self.namespace_entry.grid(row=9,column=0,pady=5,padx=10,sticky=EW)
        self.icon_lbl.grid(row=10,column=0,padx=10, sticky=W)
        self.icon_desc.grid(row=11,column=0,padx=10, sticky=W)
        self.icon_entry.grid(row=12,column=0, pady=5, padx=10, sticky=EW)
        self.description_type_lbl.grid(row=13,column=0,padx=10, sticky=W)
        self.description_type_desc.grid(row=14,column=0,padx=10, sticky=EW)
        self.description_type_entry.grid(row=15,column=0,pady=5,padx=10,sticky=EW)
        self.description_lbl.grid(row=16,column=0,padx=10, sticky=W)
        self.description_desc.grid(row=17,column=0,padx=10, sticky=W)
        self.description_entry.grid(row=18,column=0,pady=(5, 0),padx=10,sticky='nesw')
        self.description_error.grid(row=19, column=0, pady=(0, 10),padx=10,sticky=EW)
        project.grid(row=0, column=0, padx=20, pady=20, sticky='nesw')

        # Responsive
        project.grid_columnconfigure(0, weight=1)
        project.grid_rowconfigure(12, weight=1)
        client.grid_columnconfigure(0, weight=1)
        client.grid_rowconfigure(0, weight=1)
        
        return self
