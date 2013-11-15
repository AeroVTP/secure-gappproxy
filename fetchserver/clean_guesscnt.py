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

import wsgiref.handlers, logging
from google.appengine.ext import webapp

import time
from google.appengine.ext import db
import pendingreq

        
class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers["Content-Type"] = "text/html; charset=utf-8"
        pendingreq.ClearPwdGuessCnt()

def main():
    application = webapp.WSGIApplication([("/clean_guesscnt", MainHandler)])
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
