from PIL import ImageFile, Image
import UserFolder
import logging
import os
import json
import requests
import base64
import io

from old import Cache

LOCAL = os.path.dirname(os.path.realpath(__file__))
ROOT = LOCAL.replace('\\src', '')

logger = logging.getLogger('Util')

def get_changelog() -> tuple[bool, str]:
    """
    For testing
    """
    with open(os.path.join(ROOT, 'changelog.md')) as r:
        return True, r.read()
    
def get_config() -> tuple[bool, str]:
    """
    For testing
    """
    with open(os.path.join(ROOT, 'config.json')) as r:
        return True, json.load(r)

def get_update() -> tuple[bool, str]:
    """
    For testing
    """
    with open(os.path.join(ROOT, 'update.json')) as r:
        return True, json.load(r)

def fetch_changelog() -> tuple[bool, str]:
    if os.getenv('TESTING') == 'true':
        return get_changelog()

    res = requests.get("https://raw.githubusercontent.com/legopitstop/Record_API/main/app/CHANGELOG.md")
    if res.status_code == 200:
        return True, res.text
    return False, res.status_code

def fetch_config() -> tuple[bool, str]:
    if os.getenv('TESTING') == 'true':
        return get_config()
    
    res = requests.get("https://raw.githubusercontent.com/legopitstop/Record_API/main/app/config.json")
    if res.status_code == 200:
        return True, res.json()
    return False, res.status_code

def fetch_update() -> tuple[bool, str]:
    if os.getenv('TESTING') == 'true':
        return get_update()
    
    res = requests.get("https://raw.githubusercontent.com/legopitstop/Record_API/main/app/update.json")
    if res.status_code == 200:
        return True, res.json()
    return False, res.status_code

# For upgrading newer versions only
def convert_cache_to_base64(hash:str) -> str|None:
    user = UserFolder.getUser()
    cache = Cache(user)
    fp = cache.get(hash=hash)
    if fp is not None:
        return convert_file_to_base64(fp)
    return None

def convert_file_to_base64(fp) -> str:
    with open(fp, 'rb') as rb:
        return base64.b64encode(rb.read()).decode('utf-8')

def convert_base64_to_image(base:str) -> ImageFile.ImageFile:
    return Image.open(io.BytesIO(base64.decodebytes(bytes(base, 'utf-8'))))

def convert_image_to_base64(image:ImageFile.ImageFile):
    file = io.BytesIO()
    image.save(file, format='PNG')
    return base64.b64encode(file.getvalue()).decode('utf-8')

def save_base64(fp:str, base:str):
    with open(fp, 'wb') as wb:
        wb.write(base64.decodebytes(bytes(base, 'utf-8')))
