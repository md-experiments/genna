import string
import os
from hashlib import sha256, md5
import datetime
import yaml
from passlib.hash import pbkdf2_sha512


def set_env(var: str):
    if not os.environ.get(var):
        with open(f"./{var.upper()}.key", "r") as f:
            os.environ[var] = f.read().strip()


def read_yaml(path):
    with open(path) as file:
        read_configs = yaml.load(file, Loader=yaml.FullLoader)
    return read_configs

def files_in_dir(path):
    fls = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    fls = [os.path.join(path,f) for f in fls]
    return fls

def remove_punctuation(s):
    return s.translate(str.maketrans('', '', string.punctuation))

def normalize_name(text):
    return remove_punctuation(text).lower().replace(' ','_')

def hash_text(txt,mode = 'md5'):
    """
    Defaults md5, also takes sha256. Converts input to string
    >>> hash_text('hey')
    '6057f13c496ecf7fd777ceb9e79ae285'    
    >>> hash_text('hey',mode = 'sha256')
    'fa690b82061edfd2852629aeba8a8977b57e40fcb77d1a7a28b26cba62591204'
    >>> hash_text(1,mode = 'md5')
    'c4ca4238a0b923820dcc509a6f75849b'

    """
    
    if not isinstance(txt,str):
        txt = str(txt)
    txt_bytes = bytes(txt, 'utf-8')
    if mode == 'md5':
        txt_hash = md5(txt_bytes.rstrip()).hexdigest()
    elif mode == 'sha256':
        txt_hash = sha256(txt_bytes.rstrip()).hexdigest()
    return txt_hash

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def files_in_dir(path, full_path = True):
    fls = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    if full_path:
        fls = [os.path.join(path,f) for f in fls]
    return fls

def files_in_dir_filter(path, flt_txt_ls):
    all_files = files_in_dir(path)
    all_files = [f for f in all_files if all([(txt in f) for txt in flt_txt_ls])]
    all_files.sort()
    print('|'.join(flt_txt_ls),':',len(all_files),'files')
    return all_files

def files_in_dir_any_filter(path, flt_txt_ls, full_path = True):
    if path!='' and isinstance(path,str):    
        all_files = files_in_dir(path, full_path)
        all_files = [f for f in all_files if any([(txt in f) for txt in flt_txt_ls])]
        all_files.sort()
        print('|'.join(flt_txt_ls),':',len(all_files),'files')
    else:
        all_files = []
    return all_files

def add_dict(dict_a, dict_b):
    return {**dict_a,**dict_b}

def switch_button_state(received_label_name):
    if 'outline' in received_label_name:
        received_label_name = received_label_name.replace('outline-','')
    else:
        received_label_name = received_label_name.replace('btn-','btn-outline-')
    return f'btn btn-{received_label_name}'

class PassUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        return pbkdf2_sha512.encrypt(password)
 
    @staticmethod
    def check_hashed_password(password: str, hashed_password: str) -> str:
        return pbkdf2_sha512.verify(password, hashed_password)