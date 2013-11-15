#!/usr/bin/env python
# coding=utf-8
#======================================================================
# SecureGAppProxy is a security-strengthened version of GAppProxy.
# http://secure-gappproxy.googlecode.com                               
# This file is a part of SecureGAppProxy.                              
# Copyright (C) 2011  nleven <www.nleven.com i@nleven.com>             
#                                                                      
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or    
# (at your option) any later version.                                  
#                                                                      
# This program is distributed in the hope that it will be useful,      
# but WITHOUT ANY WARRANTY; without even the implied warranty of       
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        
# GNU General Public License for more details.                         
#                                                                      
# You should have received a copy of the GNU General Public License    
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#                                                                      
# ACKNOWLEDGEMENT                                                      
# SecureGAppProxy is a based on the work of GAppProxy                  
# <http://gappproxy.googlecode.com> by Du XiaoGang <dugang@188.com>
#======================================================================


from google.appengine.api import memcache
import base64
from google.appengine.ext import db
import logging
import password

class Key(db.Model):
    storedkey = db.StringProperty(required=True)

DEFAULT_SECRET = "unsafesecret!!!!"

def get_key(name, get_default_func=lambda:DEFAULT_SECRET):
    key = memcache.get(name)
    if key:
        return base64.b64decode(key)
    else:
        secret = Key.get_by_key_name(name)
        if secret:
            memcache.set(name, secret.storedkey)
            return base64.b64decode(secret.storedkey)
        else:
            default = get_default_func()
            set_key(name, default)
            return default

def set_key(name, key):
    key = base64.b64encode(key)
    memcache.set(name, key)
    Key(key_name = name,
        storedkey = key
        ).put()

def GetEncryptKey():
    return get_key("EncryptionKey")

def GetAuthKey():
    return get_key("AuthenticationKey")

def SetKey(encrypt_key, auth_key):
    set_key("EncryptionKey", encrypt_key)
    set_key("AuthenticationKey", auth_key)

def GetPassword():
    return base64.urlsafe_b64decode(password.password)

def GetRecaptchaKey():
    return get_key('RecaptchaKey', get_default_func=RetrieveRecaptchaKey).split('|')

def RetrieveRecaptchaKey():
    import google.appengine.api as r
    import re
    try:
        resp = r.urlfetch.fetch( 'http://www.google.com/recaptcha/mailhide/apikey',
                                 allow_truncated=True,
                                 follow_redirects=True)
        if resp.status_code != 200:
            raise Exception('Status code: %d' % resp.status_code)
        data = resp.content
        public_key = re.search('<p><b>Public Key:</b> (?P<key>\S+)</p>', data).group('key')
        private_key = re.search('<p><b>Private Key:</b> (?P<key>\S+)</p>', data).group('key')
        return public_key + '|' + private_key
    except Exception, e:
        logging.error('Failed to get recaptcha key. %s' % str(e))
        raise e
        
    
