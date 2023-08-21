
from tkinter.font import NORMAL
from customtkinter import ThemeManager, CTk, CTkFrame, CTkLabel, CTkToplevel, CTkButton, CTkEntry, CTkOptionMenu, CTkComboBox,CTkCheckBox, CTkScrollableFrame, CTkFont, CTkTextbox, CTkImage, CTkTabview
from tkinter import DISABLED, DOTBOX, E, END, EW, NS, SINGLE, W, BooleanVar, Listbox, Menu, StringVar, filedialog, messagebox
from UserFolder import User, Config
from platform import platform
from pygame import mixer
from PIL import Image
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
import threading
import dotenv
import pypresence
import random
import datetime

from server import Project, Item, WebConfig
from util import Cache, fetch_update, fetch_changelog, convert_cache_to_base64

user = User('com.legopitstop.music_disc_creator')
customtkinter.set_appearance_mode('System')
customtkinter.set_default_color_theme('blue')
LOCAL = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s', datefmt='%I:%M:%S',handlers=[logging.FileHandler(user.join('latest.log'),mode='w'),logging.StreamHandler(sys.stdout)], level=logging.INFO)

pyglet.options['win32_gdi_font'] = True # Fix for custom font not working
pyglet.font.add_directory(os.path.join(LOCAL,  'resources', 'fonts'))

__project_format__= 2
__beta__ = True
__version__ = '0.0.2'

dotenv.load_dotenv()

# TODO
# - Update output to match the new Record API
class App(CTk):
    def __init__(self):
        super().__init__()
        self._version = __version__
        self._format = __project_format__
        self._checking_updates = False

        self.item_clipboard:list[Item] = None

        # Web config
        self.web = WebConfig.fetch()
        
        # Create window
        self.title('Music Disc Studio [ v%s ]'%(__version__))
        self.iconbitmap(default=os.path.join(LOCAL,  'resources', 'icon.ico'))
        self.minsize(800,550)
        self.logger = logging.getLogger('Client')
        self.start_time = time.time()

        # Information
        self.logger.info('Debug Information for developers:')
        self.logger.info(' Version  : %s', __version__)
        self.logger.info(' Beta     : %s', __beta__)
        self.logger.info(' Format   : %s', __project_format__)
        self.logger.info(' TestEnv  : %s', os.getenv('TESTING').title())
        self.logger.info(' Platform : %s', platform())
        self.logger.info(' tkinter  : %s', tkinter.TkVersion)
        self.logger.info(' ctk      : %s', customtkinter.__version__)
        self.logger.info('Client ready!')

        # Variables
        self._cache = Cache(user)
        self.rpc = pypresence.Presence(client_id=os.getenv('CLIENT_ID'))
        self.project = None
        self.project_path = None
        self.project_state = 'idle'
        self.__project_saved = False
        self.advanced_options = False

        # Mixer
        mixer.init()

        # Load config
        self.c = Config(user)
        self.c.registerItem('appearance', 'System')
        self.c.registerItem('theme', 'blue')
        self.c.registerItem('dp_format', '$NAME [datapack] $VERSION')
        self.c.registerItem('rp_format', '$NAME [resources] $VERSION')
        self.c.registerItem('zip_format', '$NAME UNZIP $VERISON')
        self.c.registerItem('lore_format', '$ARTEST - $NAME')
        self.c.registerItem('dp_version', str(self.web.settings['data_format']))
        self.c.registerItem('rp_version', str(self.web.settings['resources_format']))
        self.c.registerItem('api_version', str(self.web.settings['api_format']))
        self.c.registerItem('locale', 'en_us')
        self.c.registerItem('archiveOutput', True)
        self.c.registerItem('checkUpdates', True)
        self.c.registerItem('discord_presence', True)
        customtkinter.set_appearance_mode(self.c.getItem('appearance'))
        customtkinter.set_default_color_theme(self.c.getItem('theme'))
        
        # Widgets
        self.screen = CTkScrollableFrame(self)
        self.outline = Listbox(self, bd=0, highlightthickness=0, activestyle=DOTBOX, exportselection=True, selectmode=SINGLE, fg='white', bg=self.color('bg'))
        self.outline.bind('<<ListboxSelect>>', lambda e: self.select_item())
        self.outline.bind('<Control-c>', lambda e: self.copy_item())
        self.outline.bind('<Control-v>', lambda e: self.paste_item())
        
        self.screen.grid(row=0,column=0, sticky='nesw')
        self.outline.grid(row=0, column=1, sticky=NS)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Menu
        self.menu = Menu(self, tearoff=False)

        self.file = Menu(self.menu, tearoff=False)

        self.templates = Menu(self.file, tearoff=False)
        for item in self.web.items:
            self.templates.add_command(label=item['name'], command=lambda i=item: self.new_item_screen(i))

        self.export = Menu(self.file, tearoff=False)
        self.export.add_command(label='Datapack (Java Edition)', command=lambda: self.project_export('java'))

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
        self.item.add_cascade(label='Templates', menu=self.templates)
        self.item.add_command(label='Delete', command=self.delete_item, foreground='red')

        self.edit = Menu(self.menu, tearoff=False)

        self.help = Menu(self.menu, tearoff=False)
        self.help.add_command(label='Welcome', command=self.welcome_screen)
        self.help.add_command(label='Discord', command=lambda: webbrowser.open('https://legopitstop.weebly.com/official-legopitstop-discord'))
        self.help.add_separator()
        self.help.add_command(label='Changelog', command=self.changelog_screen)
        self.help.add_command(label='Output log', command=self.log_screen)
        self.help.add_command(label='Issues', command=lambda: webbrowser.open('https://github.com/legopitstop/Record_API/issues'))
        self.help.add_separator()
        self.help.add_command(label='Check for updates...', command=self.check_updates)
        self.help.add_separator()
        self.help.add_command(label='About', command=self.about_screen)

        self.menu.add_cascade(label='File', menu=self.file)
        self.menu.add_cascade(label='Item', state=DISABLED, menu=self.item) # Replace with Edit
        self.menu.add_cascade(label='Edit', menu=self.edit)
        self.menu.add_cascade(label='Help', menu=self.help)
        self.config(menu=self.menu)

        self._ctxmenu = Menu(self, tearoff=False)
        self._ctxmenu.add_command(label='Copy', command=self.copy_item)
        self._ctxmenu.add_command(label='Paste', command=self.paste_item)
        self._ctxmenu.add_command(label='Duplicate', command=self.duplicate_item)
        self._ctxmenu.add_separator()
        self._ctxmenu.add_command(label='Rename', command=self.rename_item)
        self._ctxmenu.add_command(label='Delete', command=self.delete_item, foreground='red')

        self.outline.bind('<Button-3>', self.context_menu)

        self.welcome_screen()

        # Binds
        self.bind('<Control-s>', lambda e: self.save())
        self.bind('<Control-S>', lambda e: self.save_project_screen())
        self.bind('<Control-o>', lambda e: self.new_project_screen())
        self.bind('<Control-n>', lambda e: self.new_item_screen())
        self.bind('<Control-d>', lambda e: self.duplicate_item())
        self.bind('<Control-F11>', lambda e: self.toggle())
        self.bind('<Control-F9>', lambda e: self.stop())
        self.bind('<Delete>', lambda e: self.delete_item())

        # Open file if parsed
        if len(sys.argv) == 2: self.open(sys.argv[1])

        # Check for updates
        if self.c.getItem('checkUpdates'):
            self.check_updates(False)

    @property
    def project_saved(self) -> bool:
        return self.__project_saved
    
    @project_saved.setter
    def project_saved(self, value:bool):
        if value == None:
            self.__project_saved = False
            self.update_title()
        elif isinstance(value, bool):
            self.__project_saved = value
            self.update_title()
        
        else:
            raise TypeError(f"Expected bool but got '{value.__class__.__name__}' instead")
    
    def context_menu(self, e):
        try:
            self._ctxmenu.tk_popup(e.x_root, e.y_root)
        finally:
            self._ctxmenu.grab_release()

    def check_updates(self, ui:bool=True):
        """Check if there is an updated version"""
        def callback(ui):
            self.logger.info('Checking for updates...')
            res, dat = fetch_update()
            if res:
                if __beta__: v = dat.get('unstable')
                else: v = dat.get('stable')

                if v > __version__:
                    if __beta__:
                        self.logger.info('status: BETA_OUTDATED')
                        self.bell()
                        opn = messagebox.askyesno('Update Checker', 'A new unstable release is now available!\nDo you want to open the download page?', parent=self)
                        if opn: webbrowser.open(dat['homepage'])
                    else:
                        self.logger.info('status: OUTDATED')
                        self.bell()
                        opn = messagebox.askyesno('Update Checker', 'A new stable release is now available!\nDo you want to open the download page?', parent=self)
                        if opn: webbrowser.open(dat['homepage'])
                else:
                    self.logger.info('status: UP_TO_DATE')
                    if ui: messagebox.showinfo('Update Checker', 'You already have the latest version installed!', parent=self)

            else:
                msg = f'Failed to check for updates. Server responded with code {dat}: {res.text}'
                self.logger.warning(msg)
                # if ui:
                #     retry = messagebox.askretrycancel('Update Checker', msg, parent=self)
            self._checking_updates = False

        if self._checking_updates is False:
            self._checking_updates = True
            t = threading.Thread(target=callback, args=[ui])
            t.start()

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
        saved = self.project_saved
        if saved: self.title('Music Disc Studio [ v%s ]'%(__version__))
        else: self.title('*Music Disc Studio [ v%s ]'%__version__)

    def save(self):
        if self.project_path!=None:
            with open(self.project_path, 'w') as w:
                self.project.save()
                w.write(json.dumps(self.project.json()))
                self.project_saved=True
                self.logger.info('SAVED "%s"', self.project_path)
        else:
            self.save_project_screen()

    def validate(self, widget:tkinter.Tk, type:str):
        def callback(type, input):
            match type:
                case 'id':
                    if re.match(r'^[0-9a-z_\-.]+$', str(input)) != None: return True
                case 'custom_model_data':
                    if re.match(r'^[0-9]+$', str(input)) != None and int(input) <= 500 and int(input) >= 0: return True
                case _:
                    raise KeyError(type)
            return False

        reg = self.register(lambda i, t=type: callback(t, i))
        widget.configure(validate='key', validatecommand=(reg, '%P'))

    def upgrade(self, format:int,  data:dict, fp:str):
        """Upgrades this format"""
        if format is None or format < self._format: 
            match format:
                case _:
                    self.logger.info('None -> 2')
                    data['format'] = __project_format__
                    if 'icon' in data and 'hash' in data['icon']:
                        source = convert_cache_to_base64(data['icon']['hash'])
                        data['icon']['source'] = source
                        del data['icon']['hash']

                    if 'items' in data:
                        for item in data['items']:
                            if 'texture' in item and 'hash' in item['texture']:
                                source = convert_cache_to_base64(item['texture']['hash'])
                                item['texture']['source'] = source
                                del item['texture']['hash']

                            if 'sound' in item and 'hash' in item['sound']:
                                source = convert_cache_to_base64(item['sound']['hash'])
                                item['sound']['source'] = source
                                del item['sound']['hash']

                            if 'power_level' in item and isinstance(item['power_level'], str):
                                item['power_level'] = int(item['power_level'])

            self.logger.info(f'Upgraded project from format {format} to {self._format}')
        elif format > self._format:
            msg = 'Failed to load project "%s": Project is using a newer format! Are you using an outdated version?'%(fp)
            self.logger.warning(msg)
            messagebox.showwarning('FormatError', msg)
            return None

    def open(self, fp:str, main_file:bool=True) -> Project|None:
        """Opens the project file"""
        if os.path.isfile(fp) and fp.endswith('.mcdisc'):
            try:
                with open(fp, 'r') as f:
                    data = json.load(f)
                    format = data.get('format')
                    self.upgrade(format, data, fp)
                        
                    with open(os.path.join(LOCAL,  'resources', 'schemas', 'project.json'), 'r') as f:
                        SCHEMA =json.load(f)
                        jsonschema.validate(data, SCHEMA)
                        project = Project.from_json(self, data)

                        # Update vars if main file
                        if main_file:
                            self.menu.entryconfigure('Item', state=NORMAL)
                            self.file.entryconfigure('Project...', state=NORMAL)
                            self.project_saved = True
                            self.project_path = fp
                            self.project = project.render().render_outline()
                            self.logger.info('READ "%s"', fp)
                            self.update()

                        return project
                        
            except json.decoder.JSONDecodeError as err:
                msg = 'Failed to load project "%s": %s'%(fp, err)
                self.logger.warning(msg)
                messagebox.showwarning('JSONDecodeError', msg)

            except jsonschema.ValidationError as err:
                path = '.'.join([str(x) for x in err.absolute_path])
                msg = 'Failed to load project "%s": %s at %s'%(fp, err.message, path)
                self.logger.warning(msg)
                messagebox.showwarning('ValidationError', msg)
        else:
            messagebox.showwarning('FileNotFoundError', f'"{fp}" could not be found or is invalid!')

    def close(self):
        """Close the project"""
        if self.project!=None:
            self.project = None
            self.project_path = None
            self.project_saved = True
            self.rpc_state('idle')
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
            self.project_saved = False

    def get_item(self) -> Item|None:
        """Returns the selected item"""
        if self.project!=None:
            return self.project.selectedItem
        return None

    def select_item(self):
        """
        Select the selected item
        """
        if self.project!=None:
            try:
                index = self.outline.curselection()[0]
                self.project.set_item(index)
            except IndexError:pass
        
    def copy_item(self):
        """
        Copy the selected item to clipboard
        """
        item = self.get_item()
        if item is not None:
            self.item_clipboard = item.copy()

    def paste_item(self):
        """
        Paste item from clipboard
        """
        item = self.item_clipboard
        if self.project is not None and item is not None:
            new_item = item.copy()
            self.project.add_item(new_item)
            self.project.selectedItem.render()
            new_item.rename()

    def rename_item(self):
        """
        Rename selected item
        """
        item = self.get_item()
        if item is not None:
            item.rename()

    def duplicate_item(self):
        """
        Duplicate selected item
        """
        item = self.get_item()
        if item is not None:
            new_item = item.copy()
            new_item.name = new_item.name + ' - copy'
            self.project.add_item(new_item)
            self.project.selectedItem.render()
            new_item.rename()

    def project_import(self):
        """Import a projects items"""
        if self.project!=None:
            res = self.project._import()
            if res: self.project_saved = False

    def project_export(self, type:str):
        """Export the projects datapack and resourcepack"""
        if self.project!=None: self.project.export(type)
    
    def toggle(self):
        if self.project!=None and self.project.selectedItem!=None: self.project.selectedItem.sound.toggle()

    def stop(self):
        if self.project!=None and self.project.selectedItem!=None: self.project.selectedItem.sound.stop()
        
    def rpc_state(self, state:str):
        self.project_state = state
        self.rpc_update()

    def rpc_update(self, details:str=None):
        state = 'Unknown Project'
        if self.c.getItem('discord_presence') == 'False' and self.project_path is not None:
            state = os.path.basename(self.project_path)

        small_image = None
        small_text = None
        match self.project_state:
            case 'item':
                details = 'Making an item'
                small_image = random.choice(self.web.items).get('id')
                small_text ='item'
            case 'project':
                details = 'Making a pack'
                small_image = 'pack'
                small_text ='pack'
            case _:
                details = 'Making a undefined'

        self.rpc.update(state=state, details=details,large_image='default', large_text='Music Disc Studio', small_image=small_image, small_text=small_text, start=self.start_time)

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
            self.project = self.open(fp)

    def new_project_screen(self):
        self.close()
        self.project_saved = False
        self.project_path = None
        self.project = Project(self).render()
        self.menu.entryconfigure('Item', state=NORMAL)
        self.file.entryconfigure('Project...', state=NORMAL)        

    def new_item_screen(self, template:dict=None):
        if self.project!=None:
            item = Item.from_json(self.project, 0, {})
            if template is not None:
                item.id = template['id']
                item.name = template['name']
                item.artest = template['artest']
                item.power_level = template['power_level']
                item.obtain = template['obtain']
                
                self.logger.info(f'TEMPLATE {item.id}')

            self.project_saved = False
            self.project.save()
            self.project.add_item(item)
            self.project.set_item(0)

    def project_screen(self):
        if self.project!=None: self.project.render()

    def welcome_screen(self):
        self.clear_screen()
        welcome = CTkFrame(self.screen)
        CTkLabel(welcome, text='Music Disc Studio', font=CTkFont(size=20), anchor='w').grid(row=0, column=0, pady=(0, 20), sticky='ew')
        CTkLabel(welcome, text='Start', font=CTkFont(size=15), anchor='w').grid(row=1, column=0, sticky='ew')
        new_file = CTkLabel(welcome, text='New Project...', anchor='w', text_color=ThemeManager.theme['CTkButton']['fg_color'])
        new_file.bind('<Button-1>', lambda e: self.new_project_screen())
        new_file.grid(row=2, column=0, sticky='ew')

        open_file = CTkLabel(welcome, text='Open Project...', anchor='w', text_color=ThemeManager.theme['CTkButton']['fg_color'])
        open_file.bind('<Button-1>', lambda e: self.open_project_screen())
        open_file.grid(row=3, column=0, sticky='ew')
        welcome.grid(row=0, column=0, padx=50, pady=50, sticky='nesw')
        self.screen.grid_columnconfigure(0, weight=1)
        self.screen.grid_rowconfigure(0, weight=1)

    def settings_screen(self):
        def confirm():
            self.c.setItem('appearance', APPEARANCE.get())
            self.c.setItem('theme', THEME.get())
            self.c.setItem('dp_format', DP_FORMAT.get())
            self.c.setItem('rp_format', RP_FORMAT.get())
            self.c.setItem('zip_format', ZIP_FORMAT.get())
            self.c.setItem('lore_format', LORE_FORMAT.get())
            self.c.setItem('locale', LOCALE.get())
            self.c.setItem('archiveOutput', ARCHIVE_OUTPUT.get())
            self.c.setItem('rp_version', RP_VERSION.get())
            self.c.setItem('dp_version', DP_VERSION.get())
            self.c.setItem('api_version', API_VERSION.get())
            self.c.setItem('checkUpdates', CHECK_UPDATES.get())
            self.c.setItem('discord_presence', DISCORD_PRESENCE.get())
            self.logger.info(f"Saved settings to '{self.c.file}'")

        def cancel():
            customtkinter.set_appearance_mode(self.c.getItem('appearance'))
            customtkinter.set_default_color_theme(self.c.getItem('theme'))
            root.destroy()

        def update(e:tkinter.Event, type:str):
            match type:
                case 'appearance':
                    customtkinter.set_appearance_mode(e)
                case 'theme':
                    customtkinter.set_default_color_theme(e)
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

        def reset(value:str):
            match value:
                case 'dp_version':
                    DP_VERSION.set(str(self.web.settings['data_format']))

                case 'rp_version':
                    RP_VERSION.set(str(self.web.settings['resources_format']))

                case 'api_version':
                    API_VERSION.set(str(self.web.settings['api_format']))

        # Deprived
        def cache_size(): return str(round(self._cache.size()/(1024*1024)))+' MB'
        def cache_clear():
            confirm = messagebox.askokcancel('Clear Cache', 'Are you sure that you want to clear all cache?', parent=root)
            if confirm:
                self._cache.delete()
                
        root = CTkToplevel(self)
        root.attributes('-topmost', True)
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
        CHECK_UPDATES = BooleanVar()
        API_VERSION = StringVar()
        DISCORD_PRESENCE = BooleanVar()
        
        self.logger.info(f"Reading settings from '{self.c.file}'")
        APPEARANCE.set(self.c.getItem('appearance'))
        THEME.set(self.c.getItem('theme'))
        DP_FORMAT.set(self.c.getItem('dp_format'))
        RP_FORMAT.set(self.c.getItem('rp_format'))
        ZIP_FORMAT.set(self.c.getItem('zip_format'))
        LORE_FORMAT.set(self.c.getItem('lore_format'))
        DP_VERSION.set(self.c.getItem('dp_version'))
        RP_VERSION.set(self.c.getItem('rp_version'))
        API_VERSION.set(self.c.getItem('api_version'))
        LOCALE.set(self.c.getItem('locale'))
        ARCHIVE_OUTPUT.set(self.c.getItem('archiveOutput'))
        CACHE_SIZE.set('Calculating...')
        CHECK_UPDATES.set(self.c.getItem('checkUpdates'))
        DISCORD_PRESENCE.set(self.c.getItem('discord_presence'))
        appearance_values = ['System', 'Dark', 'Light']
        locale_values = ['en_us']

        # Populate rp and dp values
        rp_version_values = []
        for rp in range(1, self.web.settings['resources_format']+1):
            rp_version_values.insert(0, str(rp))
            
        dp_version_values = []
        for dp in range(4, self.web.settings['data_format']+1):
            dp_version_values.insert(0, str(dp))

        api_version_values = []
        for api in range(1, self.web.settings['api_format']+1):
            api_version_values.insert(0, str(api))

        tabs = CTkTabview(root)
        # tabs.configure()

        # APPEARANCE
        tab1 = tabs.add('Appearance')
        CTkLabel(tab1, text='Appearance', anchor='w', font=CTkFont(size=15)).grid(row=0,column=0,padx=10, sticky=EW)
        CTkLabel(tab1, text='The appearance mode of the app.', anchor='w').grid(row=1,column=0,padx=10, sticky=EW)
        CTkOptionMenu(tab1, values=appearance_values, variable=APPEARANCE, command=lambda e: update(e, 'appearance')).grid(row=2,column=0, pady=5,padx=10, sticky=EW)
        
        CTkLabel(tab1, text='Theme', anchor='w', font=CTkFont(size=15)).grid(row=3,column=0,padx=10, sticky=EW)
        CTkLabel(tab1, text='The color theme for the app. (Requires app restart)', anchor='w').grid(row=4,column=0,padx=10, sticky=EW)
        CTkOptionMenu(tab1, values=ThemeManager._built_in_themes, variable=THEME, command=lambda e: update(e, 'theme')).grid(row=5,column=0, pady=5,padx=10, sticky=EW)
        tab1.grid_columnconfigure(0, weight=1)

        # FORMATTING
        tab2 = tabs.add('Formatting')
        CTkLabel(tab2, text='Datapack Format', anchor='w', font=CTkFont(size=15)).grid(row=0,column=0,padx=10, sticky=EW)
        CTkLabel(tab2, text='The name of the datapack.', anchor='w').grid(row=1,column=0,padx=10, sticky=EW)
        dp_format = CTkEntry(tab2, textvariable=DP_FORMAT)
        dp_format.bind('<KeyRelease>', lambda e: update(e, 'dp'))
        dp_format.grid(row=2,column=0, pady=5, padx=(10,0), sticky=EW)
        CTkLabel(tab2, textvariable=DP_FORMAT_VIEW, anchor=W).grid(row=2, column=1, sticky=W, padx=(5,10))

        CTkLabel(tab2, text='Resource Format', anchor='w', font=CTkFont(size=15)).grid(row=3,column=0,padx=10, sticky=EW)
        CTkLabel(tab2, text='The name of the resrouce pack.', anchor='w').grid(row=4,column=0,padx=10, sticky=EW)
        rp_format = CTkEntry(tab2, textvariable=RP_FORMAT)
        rp_format.bind('<KeyRelease>', lambda e: update(e, 'rp'))
        rp_format.grid(row=5,column=0, pady=5, padx=(10,0), sticky=EW)
        CTkLabel(tab2, textvariable=RP_FORMAT_VIEW, anchor=W).grid(row=5, column=1, sticky=W, padx=5)

        CTkLabel(tab2, text='ZIP Format', anchor='w', font=CTkFont(size=15)).grid(row=6,column=0, padx=(5,10), sticky=EW)
        CTkLabel(tab2, text='The name of the zipped files', anchor='w').grid(row=7,column=0,padx=10, sticky=EW)
        zip_format = CTkEntry(tab2, textvariable=ZIP_FORMAT)
        zip_format.bind('<KeyRelease>', lambda e: update(e, 'zip'))
        zip_format.grid(row=8,column=0, pady=5, padx=(10,0), sticky=EW)
        CTkLabel(tab2, textvariable=ZIP_FORMAT_VIEW, anchor=W).grid(row=8, column=1, sticky=W, padx=(5,10))

        CTkLabel(tab2, text='Lore Format', anchor='w', font=CTkFont(size=15)).grid(row=9,column=0,padx=10, sticky=EW)
        CTkLabel(tab2, text='How to format the lore on the disc.', anchor='w').grid(row=10,column=0,padx=10, sticky=EW)
        lore_format = CTkEntry(tab2, textvariable=LORE_FORMAT)
        lore_format.bind('<KeyRelease>', lambda e: update(e, 'lore'))
        lore_format.grid(row=11,column=0, pady=5, padx=(10,0), sticky=EW)
        CTkLabel(tab2, textvariable=LORE_FORMAT_VIEW, anchor=W).grid(row=11, column=1, sticky=W, padx=(5,10))
        tab2.grid_columnconfigure(0, weight=1)

        # VERSION
        tab3 = tabs.add('Version')
        CTkLabel(tab3, text='Data Version', anchor='w', font=CTkFont(size=15)).grid(row=0,column=0,padx=10, sticky=EW)
        CTkLabel(tab3, text='The pack_format for data.', anchor='w').grid(row=1,column=0,padx=10, sticky=EW)
        CTkComboBox(tab3, variable=DP_VERSION, values=dp_version_values).grid(row=2,column=0, pady=5,padx=(10, 0), sticky=EW)
        dp_reset = CTkLabel(tab3, text='reset', text_color='red', anchor='w')
        dp_reset.bind('<Button-1>', lambda x: reset('dp_version'))
        dp_reset.grid(row=2,column=1,padx=(5,10), sticky=EW)
        
        CTkLabel(tab3, text='Resources Version', anchor='w', font=CTkFont(size=15)).grid(row=3,column=0,padx=10, sticky=EW)
        CTkLabel(tab3, text='The pack_format for resources.', anchor='w').grid(row=4,column=0,padx=10, sticky=EW)
        CTkComboBox(tab3, variable=RP_VERSION, values=rp_version_values).grid(row=5,column=0, pady=5,padx=(10, 0), sticky=EW)
        rp_reset = CTkLabel(tab3, text='reset', text_color='red', anchor='w')
        rp_reset.bind('<Button-1>', lambda x: reset('rp_version'))
        rp_reset.grid(row=5,column=1,padx=(5,10), sticky=EW)

        CTkLabel(tab3, text='API Version', anchor='w', font=CTkFont(size=15)).grid(row=6,column=0,padx=10, sticky=EW)
        CTkLabel(tab3, text='The Record API version to use.', anchor='w').grid(row=7,column=0,padx=10, sticky=EW)
        CTkOptionMenu(tab3, variable=API_VERSION, values=api_version_values).grid(row=8,column=0, pady=5,padx=(10, 0), sticky=EW)
        dp_reset = CTkLabel(tab3, text='reset', text_color='red', anchor='w')
        dp_reset.bind('<Button-1>', lambda x: reset('api_version'))
        dp_reset.grid(row=8,column=1,padx=(5,10), sticky=EW)

        CTkLabel(tab3, text='Check for Updates', anchor='w', font=CTkFont(size=15)).grid(row=9,column=0,padx=10, sticky=EW)
        CTkLabel(tab3, text='Checks for updates when the application starts up.', anchor='w').grid(row=10,column=0,padx=10, sticky=EW)
        CTkCheckBox(tab3, text='',variable=CHECK_UPDATES, onvalue=True, offvalue=False).grid(row=11,column=0, pady=5,padx=10, sticky=EW)
        tab3.grid_columnconfigure(0, weight=1)

        # MISC
        tab4 = tabs.add('Misc')
        CTkLabel(tab4, text='Archive (ZIP) Output', anchor='w', font=CTkFont(size=15)).grid(row=0,column=0,padx=10,sticky=EW)
        CTkLabel(tab4, text='When true it will pack resource and data as ZIP files.', anchor='w').grid(row=1,column=0,padx=10, sticky=EW)
        CTkCheckBox(tab4, text='', onvalue=True, offvalue=False, variable=ARCHIVE_OUTPUT).grid(row=2,column=0,padx=10, pady=5,sticky=EW)

        CTkLabel(tab4, text='Locale', anchor='w', font=CTkFont(size=15)).grid(row=3,column=0,padx=10, sticky=EW)
        CTkLabel(tab4, text='The locale code to use in-game.', anchor='w').grid(row=4,column=0,padx=10, sticky=EW)
        CTkComboBox(tab4, values=locale_values, variable=LOCALE).grid(row=5,column=0, pady=5,padx=10, sticky=EW)
        
        CTkLabel(tab4, text='Cache', anchor='w', font=CTkFont(size=15)).grid(row=6,column=0,padx=10,sticky=EW)
        CTkLabel(tab4, text='Cache stores all sounds and texture files that are used in projects', anchor='w').grid(row=7,column=0,padx=10, sticky=EW)
        CTkButton(tab4, text='Clear', command=cache_clear).grid(row=8,column=0, padx=(10,5), sticky=EW)
        CTkLabel(tab4, textvariable=CACHE_SIZE, anchor=E).grid(row=8,column=1,padx=(5,10), sticky=EW)
        
        CTkLabel(tab4, text='Discord Presence', anchor='w', font=CTkFont(size=15)).grid(row=9,column=0,padx=10, sticky=EW)
        CTkLabel(tab4, text='Obfuscate project name', anchor='w').grid(row=10,column=0,padx=10, sticky=EW)
        CTkCheckBox(tab4, text='',variable=DISCORD_PRESENCE, onvalue=True, offvalue=False).grid(row=11,column=0, pady=5,padx=10, sticky=EW)
        tab3.grid_columnconfigure(0, weight=1)
        tab4.grid_columnconfigure(0, weight=1)

        tabs.grid(row=0, column=0, columnspan=2, sticky='nesw',padx=10)
        
        # Buttons
        CTkButton(root, text='Close', command=cancel).grid(row=1,column=0, padx=10, pady=5)
        CTkButton(root, text='Save', command=confirm).grid(row=1, column=1, padx=10, pady=5)
        root.grid_columnconfigure(0, weight=1)
        CACHE_SIZE.set(cache_size())

        root.tkraise()

        # Update views
        update(None, 'all')

    def about_screen(self):
        root = CTkToplevel(self)
        root.attributes('-topmost', True)
        root.attributes('-toolwindow', True)
        root.title('About')
        root.minsize(300,100)
        root.resizable(False, False)
        root.configure(padx=10,pady=10)

        logo = Image.open(os.path.join(LOCAL, 'assets', 'jukebox.png'))
        img = CTkImage(logo, logo, (48, 48))
        CTkLabel(root, image=img, text='Music Disc Creator', font=CTkFont(size=20), compound='left').grid(row=0, column=0, sticky='ew', columnspan=2, pady=20)
        CTkLabel(root, text='Format: '+str(__project_format__), anchor='w').grid(row=1,column=0, sticky='w',padx=10, columnspan=2)
        CTkLabel(root, text='Version: '+__version__, anchor='w').grid(row=2,column=0, sticky='w',padx=10, columnspan=2)
        CTkLabel(root, text='Beta: '+str(__beta__), anchor='w').grid(row=3,column=0, sticky='w',padx=10, columnspan=2)
        CTkLabel(root, text='Platform: '+ platform(), anchor='w').grid(row=4,column=0, sticky='w',padx=10, columnspan=2)
        CTkButton(root, text='Homepage', command=lambda: webbrowser.open('https://legopitstop.weebly.com/music_disc_studio.html')).grid(row=5,column=0,pady=10,padx=5)
        CTkButton(root, text='Ok', command=root.destroy).grid(row=5,column=1,pady=10, padx=5)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)

    def changelog_screen(self):
        root = CTkToplevel(self)
        root.attributes('-topmost', True)
        root.attributes('-toolwindow', True)
        root.title('Changelog')
        root.geometry('500x500')
        root.minsize(200,200)
        root.configure(padx=10,pady=10)

        text = CTkTextbox(root)
        text.insert(0.0, 'Loading...')
        text.configure(state='disabled')
        text.grid(row=0, column=0, columnspan=2, sticky='nesw')

        CTkButton(root, text='View on Github', command=lambda: webbrowser.open('https://github.com/legopitstop/Record_API/blob/main/app/CHANGELOG.md')).grid(row=1,column=0, padx=10, pady=10, sticky='e')
        CTkButton(root, text='Close', command=root.destroy).grid(row=1,column=1, padx=10, pady=10, sticky='e')
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # get changelog
        res, log = fetch_changelog()

        if res:
            text.configure(state='normal')
            text.delete(0.0, 'end')
            text.insert(0.0, log)
            text.configure(state='disabled')

        else:
            root.destroy()
            msg = f'Failed to get changelog! Status: {log}'
            messagebox.showwarning('Changelog',msg, parent=self)
            app.logger.warning(msg)

    def log_screen(self):

        def refresh_log(x=None):
            text.configure(state='normal')
            text.insert(0.0, 'Loading...')
            text.configure(state='disabled')
            with user.open('latest.log', 'r') as r:
                text.configure(state='normal')
                text.delete(0.0, 'end')
                text.insert(0.0, r.read())
                text.configure(state='disabled')

        def save():
            filename = str(datetime.datetime.now()).replace(':', '.')
            fp = filedialog.asksaveasfilename(defaultextension='.log', filetypes=[('Log', '.log')], initialdir=os.path.join(os.path.expanduser('~'), 'Downloads'), initialfile=filename+'.log', parent=root)
            if fp!='':
                with user.open('latest.log', 'r') as r: log = r.read()
                with open(fp, 'w') as w: w.write(log)

        root = CTkToplevel(self)
        root.attributes('-topmost', True)
        root.attributes('-toolwindow', True)
        root.title('Output Log')
        root.geometry('500x500')
        root.minsize(200,200)
        root.configure(padx=10,pady=10)

        text = CTkTextbox(root)
        text.insert(0.0, 'Loading...')
        text.configure(state='disabled')
        text.grid(row=0, column=0, columnspan=2, sticky='nesw')

        CTkButton(root, text='Save as file', command=save).grid(row=1,column=0, padx=10, pady=10, sticky='e')
        CTkButton(root, text='Close', command=root.destroy).grid(row=1,column=1, padx=10, pady=10, sticky='e')
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        root.bind('<F5>', refresh_log)

        refresh_log()

    def mainloop(self):
        self.rpc.connect()
        self.rpc_update()
        super().mainloop()
        self.rpc.close()

if __name__ == '__main__':
    try:
        app=App()
        app.mainloop()
    except Exception as err: logging.exception('An unexpected error happened:')