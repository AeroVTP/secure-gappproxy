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

import os, sys

def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""
    return hasattr(sys, "frozen")

def module_dir():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""

    if we_are_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


dir = module_dir()

VERSION = "0.31"
BUILD_NUM = 55

NETWORK_CHECKER = 'http://www.appspot.com/'

DEF_LISTEN_PORT = 8000
DEF_FETCH_PROTOCOL = 'http'
DEF_LOCAL_PROXY = ''
DEF_FETCH_SERVER = ''
DEF_REKEY_NAME = 'rekey'
DEF_CONF_FILE = os.path.join(dir, 'proxy.conf')
DEF_CERT_FILE = os.path.join(dir, 'cert_default/LocalProxyServer.cert')
DEF_KEY_FILE  = os.path.join(dir, 'cert_default/LocalProxyServer.key')
CERT_DIR = os.path.join(dir, 'cert_gen')
