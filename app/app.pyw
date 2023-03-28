
from tkinter.font import NORMAL
from customtkinter import CTk, CTkFrame, CTkLabel, CTkToplevel, CTkButton, CTkEntry, CTkOptionMenu, CTkComboBox,CTkCheckBox, CTkScrollableFrame, CTkFont
from tkinter import DISABLED, DOTBOX, E, END, EW, NS, SINGLE, W, BooleanVar, Listbox, Menu, StringVar, filedialog, messagebox
from tkinter.font import Font
from UserFolder import User, Config
from platform import platform
from pygame import mixer
from tktooltip import ToolTip
import webbrowser
import customtkinter
import os
import sys
import logging
import json
import jsonschema
import pyglet
import time
import tkinter
import re

from util import Project, Item, Cache

def setup(user:User):
    os.makedirs(user.join('objects'))

user = User('com.legopitstop.music_disc_creator', setup)
customtkinter.set_appearance_mode('System')
customtkinter.set_default_color_theme('blue')
LOCAL = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s', datefmt='%I:%M:%S',handlers=[logging.FileHandler(user.join('latest.log'),mode='w'),logging.StreamHandler(sys.stdout)], level=logging.INFO)

__version__ = '0.0.1'

class App(CTk):
    def __init__(self):
        super().__init__()
        # Load custom font
        pyglet.font.add_file(os.path.join(LOCAL, 'assets', 'minecraft.otf'))
        self._font = Font(family='Minecraft Seven')
        self._fontBold = Font(family='Minecraft Seven', weight='bold')
        
        # Create window
        self.cache = Cache(user)
        self.title('Music Disc Studio [ v%s ]'%(__version__))
        self.iconbitmap(default=LOCAL+'/assets/icon.ico')
        self.minsize(800,550)
        self.logger = logging.getLogger('Client')
        self.start_time = time.time()

        # Variables
        self.project = None
        self.project_path = None
        self.project_saved = BooleanVar()
        self.project_saved.set(False)
        self.project_saved.trace_add('write', lambda a,b,c: self.update_title())

        # Mixer
        mixer.init()

        # Load conifg
        default = Config(user)
        default.setItem('appearance', 'System')
        default.setItem('theme', 'blue')
        default.setItem('dp_format', '$NAME [datapack] $VERSION')
        default.setItem('rp_format', '$NAME [resources] $VERSION')
        default.setItem('zip_format', '$NAME UNZIP $VERISON')
        default.setItem('lore_format', '$ARTEST - $NAME')
        default.setItem('dp_version', '12')
        default.setItem('rp_version', '13')
        default.setItem('locale', 'en_us')
        default.setItem('archiveOutput', True)
        self.c = default.section('CONFIG')
        customtkinter.set_appearance_mode(self.c.getItem('appearance'))
        customtkinter.set_default_color_theme(self.c.getItem('theme'))
        
        # Widgets
        self.screen = CTkScrollableFrame(self)
        self.outline = Listbox(self, bd=0, highlightthickness=0, activestyle=DOTBOX, exportselection=True, selectmode=SINGLE, fg='white', bg=self.color('bg'))
        self.outline.bind('<<ListboxSelect>>', lambda e: self.select_item())
        
        self.screen.grid(row=0,column=0, sticky='nesw')
        self.outline.grid(row=0, column=1, sticky=NS)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Menu
        self.menu = Menu(self, tearoff=False)

        self.file = Menu(self.menu, tearoff=False)
        self.export = Menu(self.file, tearoff=False)
        self.export.add_command(label='Java Edition', command=lambda: self.project_export('java'))
        # self.export.add_command(label='Bedrock Edition (COMING SOON!)', state=DISABLED, command=lambda: self.project_export('bedrock'))

        self.file.add_command(label='Project...', state=DISABLED, command=self.project_screen)
        self.file.add_separator()
        self.file.add_command(label='Open', command=self.open_project_screen)
        self.file.add_command(label='New', command=self.new_project_screen)
        self.file.add_separator()
        self.file.add_command(label='Save Project', command=self.save)
        self.file.add_command(label='Save Project As', command=self.save_project_screen)
        self.file.add_command(label='Close Project', command=self.close)
        self.file.add_separator()
        self.file.add_command(label='Import', command=self.project_import)
        self.file.add_cascade(label='Export', menu=self.export)
        self.file.add_separator()
        self.file.add_command(label='Settings', command=self.settings_screen)

        self.item = Menu(self.menu, tearoff=False)
        self.item.add_command(label='New', command=self.new_item_screen)
        self.item.add_command(label='Delete', command=self.delete_item)

        # self.edit = Menu(self.menu, tearoff=False)
        # self.edit.add_command(label='Undo')
        # self.edit.add_command(label='Redo')
        # self.edit.add_separator()
        # self.edit.add_command(label='Cut')
        # self.edit.add_command(label='Copy')
        # self.edit.add_command(label='Paste')

        self.help = Menu(self.menu, tearoff=False)
        self.help.add_command(label='Welcome', command=self.welcome_screen)
        self.help.add_command(label='Discord', command=lambda: webbrowser.open('https://legopitstop.weebly.com/discord.html'))
        self.help.add_separator()
        self.help.add_command(label='About', command=self.about_screen)

        self.menu.add_cascade(label='File', menu=self.file)
        self.menu.add_cascade(label='Item', state=DISABLED, menu=self.item)
        # self.menu.add_cascade(label='Edit', menu=self.edit)
        self.menu.add_cascade(label='Help', menu=self.help)
        self.config(menu=self.menu)
        self.welcome_screen()

        # Binds
        self.bind('<Control-s>', lambda e: self.save())
        self.bind('<Control-S>', lambda e: self.save_project_screen())
        self.bind('<Control-o>', lambda e: self.new_project_screen())
        self.bind('<Control-n>', lambda e: self.new_item_screen())
        self.bind('<Control-F11>', lambda e: self.toggle())
        self.bind('<Control-F9>', lambda e: self.stop())
        self.bind('<Delete>', lambda e: self.delete_item())

        self.logger.info('Client ready!')
        self.logger.info('Version: %s', __version__)
        self.logger.info('OS: %s', platform())

        # Open file if parsed
        if len(sys.argv) == 2: self.open(sys.argv[1])
        
    def has_blockbench(self):
        """Checks if the user has BlockBench installed"""
        bb_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Programs', 'Blockbench', 'Blockbench.exe')
        if os.path.exists(bb_path): return True
        return False
    
    def open_blockbench(self, fp:str=None):
        """Open model with Blockbench"""
        res = self.has_blockbench()
        if res:
            path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Programs', 'Blockbench', 'Blockbench.exe')
            if fp: os.startfile(fp)
        else:
            if fp: os.startfile(fp)

    def update_title(self):
        saved = self.project_saved.get()
        if saved: self.title('Music Disc Studio [ v%s ]'%(__version__))
        else: self.title('*Music Disc Studio [ v%s ]'%__version__)

    def save(self):
        if self.project_path!=None:
            with open(self.project_path, 'w') as w:
                self.project.save()
                w.write(json.dumps(self.project.json()))
                self.project_saved.set(True)
                self.logger.info('WRITE "%s"', self.project_path)
        else:
            self.save_project_screen()

    def select_item(self):
        if self.project!=None:
            try:
                index = self.outline.curselection()[0]
                self.project.set_item(index)
            except IndexError:pass

    def validate(self, widget:tkinter.Tk, type:str):
        def callback(type, input):
            match type:
                case 'id':
                    if re.match(r'^[0-9a-z_\-.]{0,}$', str(input)) != None: return True
            return False

        reg = self.register(lambda i, t=type: callback(t, i))
        widget.configure(validate='key', validatecommand=(reg, '%P'))

    def open(self, fp:str):
        """Opens the project file"""
        if os.path.exists(fp) and os.path.isfile(fp) and fp.endswith('.mcdisc'):
            try:
                with open(fp, 'r') as f:
                    data = json.load(f)
                    with open(os.path.join(LOCAL, 'assets', 'schema.json'), 'r') as f:
                        SCHEMA =json.load(f)
                        jsonschema.validate(data, SCHEMA)
                        project = Project(self, **data)
                        self.project = project.render().render_outline()
                        self.menu.entryconfigure('Item', state=NORMAL)
                        self.file.entryconfigure('Project...', state=NORMAL)
                        self.project_saved.set(True)
                        self.project_path = fp
                        self.logger.info('READ "%s"', fp)
                        return project
                        
            except json.decoder.JSONDecodeError as err:
                msg = 'Failed to load project "%s": %s'%(fp, err)
                self.logger.warning(msg)
                messagebox.showwarning('JSONDecodeError', msg)
                return None
            except jsonschema.ValidationError as err:
                msg = 'Failed to load project "%s": %s'%(fp, err.message)
                self.logger.warning(msg)
                messagebox.showwarning('ValidationError', msg)
                return None
        else:
            messagebox.showwarning('FileNotFoundError', f'"{fp}" could not be found or is invalid!')

    def close(self):
        """Close the project"""
        if self.project!=None:
            self.project = None
            self.project_path = None
        self.menu.entryconfigure('Item', state=DISABLED)
        self.file.entryconfigure('Project...', state=DISABLED)
        self.outline.delete(0, END)
        self.welcome_screen()

    def color(self, name:str):
        if name == 'bg': return self['bg']

    def max_str(self, text:str, max:int=45, handle:str='break'):
        if len(text) >= max:
            if handle=='break': return str(text)[0:max]
            elif handle=='extra': return str(text)[max:len(text)]
            else: return text
        else:
            if handle=='extra': return ''
            else: return str(text)

    def format(self, type:str|tkinter.Variable, **kw:str):
        """Format the text using the schema in settings"""
        f = ''
        if isinstance(type, str): f = self.c.getItem(type+'_format')
        elif isinstance(type, tkinter.Variable): f = type.get()
        if f!=None:
            for k in kw:
                value = kw[k]
                f = f.replace('$'+k.upper(), str(value))
            return self.max_str(f)

    def mc_disc_power(self, power_level:int):
        """Gets the minecraft music disc from the power level"""
        match power_level:
            case 1: return 'music_disc_13'
            case 2: return 'music_disc_cat'
            case 3: return 'music_disc_blocks'
            case 4: return 'music_disc_chirp'
            case 5: return 'music_disc_far'
            case 6: return 'music_disc_mall'
            case 7: return 'music_disc_mellohi'
            case 8: return 'music_disc_stal'
            case 9: return 'music_disc_strad'
            case 10: return 'music_disc_ward'
            case 11: return 'music_disc_11'
            case 12: return 'music_disc_wait'
            case 13: return 'music_disc_pigstep'
            case 14: return 'music_disc_otherside'
            case 15: return 'music_disc_5'
            case _: return None

    def delete_item(self):
        """Removes the selected item"""
        if self.project!=None:
            self.project.remove_item()
            self.project_saved.set(False)

    def project_import(self):
        """Import a projects items"""
        if self.project!=None:
            res = self.project._import()
            if res: self.project_saved.set(False)

    def project_export(self, type:str):
        """Export the projects datapack and resourcepack"""
        if self.project!=None: self.project.export(type)
    
    def toggle(self):
        if self.project!=None and self.project.selectedItem!=None: self.project.selectedItem.sound.toggle()

    def stop(self):
        if self.project!=None and self.project.selectedItem!=None: self.project.selectedItem.sound.stop()
        
    # Screens
    def clear_screen(self):
        """Remove all children widgets"""
        if self.project!=None: self.project.save()
        for w in self.screen.winfo_children():
            w.destroy()
        self.screen.grid_rowconfigure(0, weight=0)
        self.screen.grid_columnconfigure(0, weight=0)

    def save_project_screen(self, filename:str=None):
        if self.project!=None:
            if filename is None: filename = self.project.name+'.mcdisc' 
            filetypes = [('Project', '.mcdisc')]
            fp = filedialog.asksaveasfilename(confirmoverwrite=True, defaultextension='.mcdisc', initialfile=filename, filetypes=filetypes, parent=self)
            if fp!='':
                self.project_path = fp
                self.save()

    def open_project_screen(self):
        filetypes = [('Project', '*.mcdisc')]
        fp = filedialog.askopenfilename(defaultextension='.mcdisc', filetypes=filetypes, parent=self)
        if fp!='':
            self.close()
            self.open(fp)

    def new_project_screen(self):
        self.close()
        self.project_saved.set(False)
        self.project_path = None
        self.project = Project(self).render()
        self.menu.entryconfigure('Item', state=NORMAL)
        self.file.entryconfigure('Project...', state=NORMAL)        

    def new_item_screen(self):
        if self.project!=None:
            self.project_saved.set(False)
            self.project.save()
            self.project.add_item(Item(self.project))
            self.project.set_item(0)

    def project_screen(self):
        if self.project!=None: self.project.render()

    def welcome_screen(self):
        self.clear_screen()
        welcome = CTkFrame(self.screen)
        CTkLabel(welcome, text='Music Disc Studio', font=CTkFont(size=20), anchor='w').grid(row=0, column=0, pady=(0, 20), sticky='ew')
        CTkLabel(welcome, text='Start', font=CTkFont(size=15), anchor='w').grid(row=1, column=0, sticky='ew')
        new_file = CTkLabel(welcome, text='New File...', anchor='w', text_color='#1f6aa5')
        new_file.bind('<Button-1>', lambda e: self.new_project_screen())
        new_file.grid(row=2, column=0, sticky='ew')

        open_file = CTkLabel(welcome, text='Open File...', anchor='w', text_color='#1f6aa5')
        open_file.bind('<Button-1>', lambda e: self.open_project_screen())
        open_file.grid(row=3, column=0, sticky='ew')
        welcome.grid(row=0, column=0, padx=50, pady=50, sticky='nesw')
        self.screen.grid_columnconfigure(0, weight=1)
        self.screen.grid_rowconfigure(0, weight=1)

    def settings_screen(self):
        def confirm():
            self.c.setItem('appearance', APPEARANCE.get())
            self.c.setItem('theme', THEME.get())
            customtkinter.set_default_color_theme(THEME.get())
            self.c.setItem('dp_format', DP_FORMAT.get())
            self.c.setItem('rp_format', RP_FORMAT.get())
            self.c.setItem('zip_format', ZIP_FORMAT.get())
            self.c.setItem('lore_format', LORE_FORMAT.get())
            self.c.setItem('locale', LOCALE.get())
            self.c.setItem('archiveOutput', ARCHIVE_OUTPUT.get())
            self.c.setItem('rp_version', RP_VERSION.get())
            self.c.setItem('dp_version', DP_VERSION.get())
            root.destroy()

        def cancel():
            customtkinter.set_appearance_mode(self.c.getItem('appearance'))
            customtkinter.set_default_color_theme(self.c.getItem('theme'))
            root.destroy()

        def update(e:tkinter.Event, type:str):
            match type:
                case 'appearance':
                    customtkinter.set_appearance_mode(e)
                case 'dp':
                    value = self.format(DP_FORMAT, name='Example', version=__version__)
                    DP_FORMAT_VIEW.set(value)
                case 'rp':
                    value = self.format(RP_FORMAT, name='Example', version=__version__)
                    RP_FORMAT_VIEW.set(value)
                case 'zip':
                    value = self.format(ZIP_FORMAT, name='Example', version=__version__)
                    ZIP_FORMAT_VIEW.set(value)
                case 'lore':
                    value = self.format(LORE_FORMAT, name='Cat', artest='C418')
                    LORE_FORMAT_VIEW.set(value)
                case 'all':
                    update(e, 'dp')
                    update(e, 'rp')
                    update(e, 'zip')
                    update(e, 'lore')

        def cache_size(): return str(round(self.cache.size()/(1024*1024)))+' MB'

        def cache_clear():
            confirm = messagebox.askokcancel('Clear Cache', 'Are you sure that you want to clear all cache?', parent=root)
            if confirm:
                self.cache.delete()
                # CACHE_SIZE.set(cache_size())
        root = CTkToplevel(self)
        root.attributes('-toolwindow', True)
        root.title('Settings')
        root.protocol('WM_DELETE_WINDOW', cancel)
        root.resizable(True, False)
        root.minsize(400, 200)
        root.configure(padx=10, pady=10)
        APPEARANCE = StringVar()
        THEME = StringVar()
        DP_FORMAT = StringVar()
        DP_FORMAT_VIEW = StringVar()
        RP_FORMAT = StringVar()
        RP_FORMAT_VIEW = StringVar()
        ZIP_FORMAT = StringVar()
        ZIP_FORMAT_VIEW = StringVar()
        LORE_FORMAT = StringVar()
        LORE_FORMAT_VIEW = StringVar()
        LOCALE = StringVar()
        ARCHIVE_OUTPUT = BooleanVar()
        DP_VERSION = StringVar()
        RP_VERSION = StringVar()
        CACHE_SIZE = StringVar()
        APPEARANCE.set(self.c.getItem('appearance'))
        THEME.set(self.c.getItem('theme'))
        DP_FORMAT.set(self.c.getItem('dp_format'))
        RP_FORMAT.set(self.c.getItem('rp_format'))
        ZIP_FORMAT.set(self.c.getItem('zip_format'))
        LORE_FORMAT.set(self.c.getItem('lore_format'))
        DP_VERSION.set(self.c.getItem('dp_version'))
        RP_VERSION.set(self.c.getItem('rp_version'))
        LOCALE.set(self.c.getItem('locale'))
        ARCHIVE_OUTPUT.set(self.c.getItem('archiveOutput'))
        CACHE_SIZE.set('Calculating...')
        appearance_values = ['System', 'Dark', 'Light']
        theme_values = ['blue', 'dark-blue', 'green']
        locale_values = ['en_us']
        rp_version_values = ['13','12','11','10','9','8','7','6','5','4','3','2','1']
        dp_version_values = ['12','11','10','9','8','7','6','5','4']
        CTkLabel(root, text='Appearance', anchor=E).grid(row=0,column=0,padx=10, sticky=EW)
        CTkOptionMenu(root, values=appearance_values, variable=APPEARANCE, command=lambda e: update(e, 'appearance')).grid(row=0,column=1, pady=5, sticky=EW)
        CTkLabel(root, text='Theme', anchor=E).grid(row=1,column=0,padx=10, sticky=EW)
        CTkOptionMenu(root, values=theme_values, variable=THEME).grid(row=1,column=1, pady=5, sticky=EW)
        CTkLabel(root, text='Datapack Format', anchor=E).grid(row=2,column=0,padx=10, sticky=EW)
        dp_format = CTkEntry(root, textvariable=DP_FORMAT)
        dp_format.bind('<KeyRelease>', lambda e: update(e, 'dp'))
        dp_format.grid(row=2,column=1, pady=5, sticky=EW)
        CTkLabel(root, textvariable=DP_FORMAT_VIEW, anchor=W).grid(row=2, column=2, sticky=W, padx=5)

        CTkLabel(root, text='Resource Format', anchor=E).grid(row=3,column=0,padx=10, sticky=EW)
        rp_format = CTkEntry(root, textvariable=RP_FORMAT)
        rp_format.bind('<KeyRelease>', lambda e: update(e, 'rp'))
        rp_format.grid(row=3,column=1, pady=5, sticky=EW)
        CTkLabel(root, textvariable=RP_FORMAT_VIEW, anchor=W).grid(row=3, column=2, sticky=W, padx=5)

        CTkLabel(root, text='ZIP Format', anchor=E).grid(row=4,column=0,padx=10, sticky=EW)
        zip_format = CTkEntry(root, textvariable=ZIP_FORMAT)
        zip_format.bind('<KeyRelease>', lambda e: update(e, 'zip'))
        zip_format.grid(row=4,column=1, pady=5, sticky=EW)
        CTkLabel(root, textvariable=ZIP_FORMAT_VIEW, anchor=W).grid(row=4, column=2, sticky=W, padx=5)

        CTkLabel(root, text='Lore Format', anchor=E).grid(row=5,column=0,padx=10, sticky=EW)
        lore_format = CTkEntry(root, textvariable=LORE_FORMAT)
        lore_format.bind('<KeyRelease>', lambda e: update(e, 'lore'))
        lore_format.grid(row=5,column=1, pady=5, sticky=EW)
        CTkLabel(root, textvariable=LORE_FORMAT_VIEW, anchor=W).grid(row=5, column=2, sticky=W, padx=5)

        locale_lbl = CTkLabel(root, text='Locale', anchor=E)
        ToolTip(locale_lbl, 'The locale to use in-game.')
        locale_lbl.grid(row=6,column=0,padx=10, sticky=EW)
        CTkComboBox(root, values=locale_values, variable=LOCALE).grid(row=6,column=1, pady=5, sticky=EW)
        
        CTkLabel(root, text='Archive (ZIP) Output', anchor=E).grid(row=7,column=0,padx=10, sticky=EW)
        CTkCheckBox(root, text='', onvalue=True, offvalue=False, variable=ARCHIVE_OUTPUT).grid(row=7,column=1, pady=5, sticky=EW)
        
        CTkLabel(root, text='Datapack Pack Format', anchor=E).grid(row=8,column=0,padx=10, sticky=EW)
        CTkComboBox(root, variable=DP_VERSION, values=dp_version_values).grid(row=8,column=1, pady=5, sticky=EW)
        
        CTkLabel(root, text='Resourcepack Pack Format', anchor=E).grid(row=9,column=0,padx=10, sticky=EW)
        CTkComboBox(root, variable=RP_VERSION, values=rp_version_values).grid(row=9,column=1, pady=5, sticky=EW)
        
        cache_lbl = CTkLabel(root, text='Cache', anchor=E)
        ToolTip(cache_lbl, 'Cache stores all sounds and texture files that are used in projects')
        cache_lbl.grid(row=10,column=0,padx=10, sticky=EW)
        CTkButton(root, text='Clear', command=cache_clear).grid(row=10,column=1, pady=5, sticky=EW)
        CTkLabel(root, textvariable=CACHE_SIZE, anchor=E).grid(row=10,column=2,padx=10, sticky=EW)
        CTkButton(root, text='Cancel', command=cancel).grid(row=11,column=1, padx=10, pady=5)
        CTkButton(root, text='Confirm', command=confirm).grid(row=11, column=2, padx=10, pady=5)
        root.grid_columnconfigure(1, weight=1)
        CACHE_SIZE.set(cache_size())
        # root.resizable(True, False)

        root.tkraise()

        # Update views
        update(None, 'all')

    def about_screen(self):
        root = CTkToplevel(self)
        root.attributes('-topmost', True)
        root.attributes('-toolwindow', True)
        root.title('About')
        root.geometry('200x200')
        root.resizable(False, False)
        root.configure(padx=10,pady=10)
        CTkLabel(root, text='Music Disc Creator', font=CTkFont(size=20)).grid(row=0, column=0, sticky='ew')
        CTkLabel(root, text='Version: '+__version__, anchor='w').grid(row=1,column=0, sticky='w')
        CTkLabel(root, text='OS: '+ platform(), anchor='w').grid(row=2,column=0, sticky='w')
        CTkButton(root, text='Ok', command=root.destroy).grid(row=3,column=0)
        root.grid_columnconfigure(0, weight=1)

if __name__ == '__main__':
    try:
        app=App()
        app.mainloop()
    except Exception as err: logging.exception('An unexpected error happened:')