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
import time
try:
    import cPickle as pickle
except:
    import pickle
    
import base64
AGREE_EXPIRE = 60

import bpkaspak

class AgreeState(db.Model):
    state = db.BlobProperty(required=True)
    timestamp = db.IntegerProperty(required=True)


def find_state(confirm_c):
    state = AgreeState.get_by_key_name(base64.b64encode(confirm_c))
    if state:
        r = pickle.loads(state.state)
        state.delete()
        return r
    else:
        return None

def store_state(state):
    AgreeState(key_name = base64.b64encode(state.confirm_c),
               state = pickle.dumps(state),
               timestamp = int(time.time())
               ).put()

        


if __name__ == "__main__":
    pass
