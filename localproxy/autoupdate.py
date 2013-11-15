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

import common, urllib2

LATEST_VER = "http://secure-gappproxy.googlecode.com/svn/trunk/localproxy/latest_version"
LATEST_DESC = "http://secure-gappproxy.googlecode.com/svn/trunk/localproxy/latest_description"


def auto_update(listen_port):
    proxy_handler = urllib2.ProxyHandler({"http":"127.0.0.1:%d" % (listen_port)})
    opener = urllib2.build_opener(proxy_handler)
    urllib2.install_opener(opener)

    f = urllib2.urlopen(LATEST_VER, timeout=5)
    build = int(f.read())
    f.close()
    if build > common.BUILD_NUM:
        f = urllib2.urlopen(LATEST_DESC, timeout=5)
        msg = f.read()
        f.close()
        return True, msg
    return False, ""


    
