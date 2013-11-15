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

import logging, webapp2

import time
from google.appengine.ext import db
import nonce
import pendingreq
import agreestate
def Clean(kind, expire):
    time_expire = int(time.time()) - expire
    while True:
        results = db.GqlQuery("SELECT * FROM Nonce WHERE timestamp <= :1", time_expire)
        if results.count() != 0:
            db.delete(results.fetch(1000))
        else:
            break


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers["Content-Type"] = "text/html; charset=utf-8"
        Clean('Nonce', 900)
        Clean('AgreeState', 60)
        Clean('PendingRequest', 900)

app = webapp2.WSGIApplication([("/clean", MainHandler)],debug=True)
