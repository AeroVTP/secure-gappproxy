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

import wsgiref.handlers, logging
from google.appengine.ext import webapp
from google.appengine.ext import db

import key
import bpkaspak
import agreestate

import base64
import os
import pendingreq
import mailhide

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        return
    
    def post(self):
        self.response.headers["Content-Type"] = "application/octet-stream"
        
        try:
            if self.request.get("e")=='':
                self.response.out.write(os.urandom(65))
                return
            data = base64.urlsafe_b64decode(self.request.get("e").encode('utf-8'))
                
            pending_request = pendingreq.RetrievePendingRequest(data)
            known_state = agreestate.find_state(data)

            if pending_request is None and known_state is None:
                if pendingreq.GetPwdGuessCnt() >= 5:
                    challenge = pendingreq.PendRequest(data)
                    public_key, private_key = key.GetRecaptchaKey()
                    self.redirect(mailhide.asurl(challenge, public_key, private_key))
                    return
            elif pending_request is not None:
                data = pending_request

            if known_state is not None:
                try:
                    
                    known_state.Phase2(data)
                    key.SetKey(known_state.DeriveKey("Encrypt"),
                               known_state.DeriveKey("Authenticate")
                               )
                    pendingreq.ClearPwdGuessCnt()
                except:
                    #ProtocolAbort return random result
                    logging.error('Protocol abort in first phase.')
                    self.response.out.write(os.urandom(65))
                    
            else:
                state = bpkaspak.KeyAgreementServer(key.GetPassword())
                resp = ''
                try:
                    pendingreq.IncrPwdGuessCnt()
                    resp = state.Phase1(data)
                    agreestate.store_state(state)
                except:
                    logging.error('Protocol abort in second phase. An attacker might be guessing password.')
                    #Give random result
                    resp = os.urandom(65)
                self.response.out.write(resp)
        except Exception, e:
            logging.error('Unknown error in authentication. %s' % str(e))
            self.response.out.write(os.urandom(65))
            
            
            
        
        


def main():
    application = webapp.WSGIApplication([("/rekey", MainHandler)])
    wsgiref.handlers.CGIHandler().run(application)
    

if __name__ == "__main__":
    main()
