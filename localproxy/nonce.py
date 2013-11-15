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

import struct
import os

import datetime, time
import synctime

NONCE_LENGTH = 16
NONCE_EXPIRE = 900

used_nonce = {}


from threading import Timer

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
    return int(synctime.get_time())

def GenerateNonce():
    return os.urandom(8) + __ser_int(__utc_time(), 8)

def CheckNonce(nonce):
    if len(nonce) != NONCE_LENGTH:
        return False
    rand = nonce[:8]
    timestamp = __deser_int(nonce[8:])
    time_expire = __utc_time() - NONCE_EXPIRE
    if timestamp <= time_expire:
        return False
    if rand in used_nonce:
        return False
    used_nonce[rand] = timestamp
    return True


def CleanExpiredNonce():
    time_expire = __utc_time() - NONCE_EXPIRE
    for key, value in used_nonce.items():
        if value <= time_expire:
            del used_nonce[key]
        

timer = None
def Initialize():
    global timer
    timer = Timer(NONCE_EXPIRE, CleanExpiredNonce)
    timer.start()

def Finalize():
    global timer
    if timer != None:
        timer.cancel()

if __name__ == "__main__":
    import base64
    print time.mktime(datetime.datetime.utcnow().timetuple()) 
    a=GenerateNonce()
    b=GenerateNonce()
    c=GenerateNonce()
    print base64.b64encode(a)
    print CheckNonce(a)
    print CheckNonce(b)
    print CheckNonce(a)
    print CheckNonce(c)
    print CheckNonce(b)
    print used_nonce
    NONCE_EXPIRE = 0
    CleanExpiredNonce()
    NONCE_EXPIRE = 900
    print used_nonce
    print CheckNonce(b)
    
