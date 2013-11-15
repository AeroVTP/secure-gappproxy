#! /usr/bin/env python
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


from google.appengine.ext import db
from google.appengine.api import memcache
import os
import struct
import datetime, time

import base64
NONCE_LENGTH = 16
NONCE_EXPIRE = 900

class Nonce(db.Model):
    timestamp = db.IntegerProperty(required=True)
    random = db.StringProperty(required=True)

def __ser_int(num, length=None):
    serialized = ""
    while num != 0:
        serialized += chr(num % 256)
        num /= 256
    if length:
        serialized += "\x00" * (length-len(serialized))
    return serialized[::-1]

def __deser_int(serialized):
    num = 0
    for i in serialized:
        num = num * 256 + ord(i)
    return int(num)

def __utc_time():
    return int(time.time())

def GenerateNonce():
    return os.urandom(8) + __ser_int(__utc_time(), 8)

def CheckNonce(n):
    if len(n) != NONCE_LENGTH:
        return False
    rand = base64.b64encode(n[:8])
    timestamp = __deser_int(n[8:])
    time_expire = __utc_time() - NONCE_EXPIRE
    if timestamp <= time_expire:
        return False
    if memcache.get('nonce_' + rand):
        return False
    memcache.set('nonce_' + rand, '', NONCE_EXPIRE)
    return True

def CleanExpiredNonce():
    pass

if __name__ == "__main__":
    nonce =  GenerateNonce()
    print nonce
    print CheckNonce(nonce)
    print CheckNonce(nonce)
