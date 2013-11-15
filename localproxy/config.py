import keyring
import os
import common
import copy
import re

__conf_dict = None

if os.name == 'nt':
    keyring.set_keyring(keyring.backend.Win32CryptoKeyring())

def __parse_conf(confFile=common.DEF_CONF_FILE):
    global __conf_dict
    __conf_dict = {}
    # read config file
    try:
        fp = open(confFile, "r")
    except IOError:
        # use default parameters
        return
    # parse user defined parameters
    while True:
        line = fp.readline()
        if line == "":
            # end
            break
        # parse line
        line = line.strip()
        if line == "":
            # empty line
            continue
        if line.startswith("#"):
            # comments
            continue
        (name, sep, value) = line.partition("=")
        if sep == "=":
            name = name.strip().lower()
            value = value.strip()
            __conf_dict[name] = value
    fp.close()
    
    #Get the password in the keyring.
    #Avoid doing so if fetch_server isn't set.
    if 'fetch_server' in __conf_dict:
        pwd = keyring.get_password('secure-gappproxy', 'password')
        if pwd and pwd!='':
            __conf_dict['password'] = pwd
    
def SaveConfig(conf_file=common.DEF_CONF_FILE):
    global __conf_dict
    conf_copy = copy.deepcopy(__conf_dict)
    if 'password' in conf_copy:
        keyring.set_password('secure-gappproxy', 'password', conf_copy['password'])
        del conf_copy['password']
    else:
        keyring.set_password('secure-gappproxy', 'password', '')

    try:
        fp = open(conf_file, 'w+')

        fp.write( '\n'.join( map(lambda s:'='.join(s),
                                 conf_copy.items()
                                 )
                             )
                  )
    except IOError:
        return
    finally:
        fp.close()

    
    
def __port_validate(i, get):
    if get:
        ret = None
        try:
            ret = int(i)
            if ret <= 0 or ret >=65536:
                return False
        except:
            return False
    return True

def __proxytext_validate(proxy, get):
    return proxy == '' or re.match("(\\S+:\\S+@)?\\S+:\d+", proxy)

def __protocol_validate(protocol, get):
    return protocol.lower() in ['http', 'https']

def __bool_validate(b, get):
    if get:
        return b in ['0', '1']
    else:
        return b in [True, False]

def __bool_convertor(s, get):
    if get:
        return {'0':False, '1':True}[s]
    else:
        return {False:'0', True:'1'}[s]


def __int_convertor(s, get):
    if get:
        return int(s)
    else:
        return str(s)

def __base64_convertor(s, get):
    import base64
    if get:
        return base64.urlsafe_b64decode(str(s))
    else:
        return base64.urlsafe_b64encode(s)
    

__dont_validate = lambda x,y:True
__no_convertor = lambda x,y:x
__conf_default = { 'listen_port':       (common.DEF_LISTEN_PORT,       __port_validate,        __int_convertor),
                   'local_proxy':       ('',                           __proxytext_validate,   __no_convertor),
                   'fetch_server':      ('',                           __dont_validate,        __no_convertor),
                   'fetch_protocol':    (common.DEF_FETCH_PROTOCOL,    __protocol_validate,    __no_convertor),
                   'fetch_rekey':       (common.DEF_REKEY_NAME,        __dont_validate,        __no_convertor),
                   'password':          (None,                         __dont_validate,        __base64_convertor),
                   'auto_redirect':     (True,                         __bool_validate,        __bool_convertor),
                   }

def GetParam(key, default=None, validator=__dont_validate, convertor=__no_convertor):
    if not __conf_dict:
        __parse_conf(common.DEF_CONF_FILE)
    if key in __conf_default:
        default, validator, convertor = __conf_default[key]
        
    if key not in __conf_dict:
        return default
    else:
        val = __conf_dict[key]

    if not validator(val, True):
        return default
    else:
        return convertor(val, True)

def DeleteParam(key):
    if not __conf_dict:
        __parse_conf(common.DEF_CONF_FILE)
    __conf_dict.pop(key, None)
        
def SetParam(key, value, validator=__dont_validate, convertor=__no_convertor):
    if not __conf_dict:
        __parse_conf(common.DEF_CONF_FILE)

    if key in __conf_default:
        default, validator, convertor = __conf_default[key]

    if validator(value, False):
        __conf_dict[key] = convertor(value, False)
    else:
        DeleteParam(key)






