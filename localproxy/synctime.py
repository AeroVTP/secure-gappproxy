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

import urllib2
import time
import calendar
import locale

def __median(pool):
    '''Statistical median to demonstrate doctest.
    >>> median([2, 9, 9, 7, 9, 2, 4, 5, 8])
    7
    '''
    copy = sorted(pool)
    size = len(copy)
    if size % 2 == 1:
        return copy[(size - 1) / 2]
    else:
        return (copy[size/2 - 1] + copy[size/2]) / 2

def __get_time(server, time_result, *args):
    try:
        date_header = urllib2.urlopen(server).headers['date']
        net_time = calendar.timegm(time.strptime(date_header, "%a, %d %b %Y %H:%M:%S GMT"))
        time_result.append(net_time)
    except:
        pass
    time_result[0] -= 1



import threading

def get_network_time(local_proxy):
    """Get time from a list of servers through http. Time is from the "date" header in http.
Due to the nature of http, the precision of time isn't high, but should be adequate for our purposes."""
    time_servers = ['http://www.google.com/',
                    'http://www.baidu.com/',
                    'http://www.qq.com/',
                    'http://www.google.com.hk/',
                    'http://www.sohu.com/',
                    'http://www.163.com/',
                    'http://www.yahoo.com/',
                    'http://www.wikipedia.org/',
                    'http://www.microsoft.com/',
                    'http://www.amazon.com/',
                    'http://www.ebay.com/',
                    ]
    time_result = []
    #Set local proxy server
    if local_proxy != "":
        proxy_handler = urllib2.ProxyHandler({"http": local_proxy})
    else:
        proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    urllib2.install_opener(opener)

    #set the locale to english. strptime is locale dependent.
    #note: setlocale isn't threadsafe.
    try:
        locale.setlocale(locale.LC_ALL, locale.normalize('en_us'))
    except:
        #in case en_us locale doesn't exist
        pass

    threads = map(lambda server:threading.Thread(target=__get_time, args=(server,time_result), kwargs={}), time_servers)
    map(lambda x:x.start(), threads)

    time_result.append(len(threads))
    #loop while thread still remains working or time_result not enough
    while time_result[0]>0 and len(time_result)-1 < 4:
        map(lambda x:x.join(0.1), threads)
    time_result.pop(0)

    assert len(time_result) != 0, "Cannot fetch network time."

    return __median(time_result)

__offset = 0

def init_offset(local_proxy=""):
    """Initialize time offset between local time and network time."""
    global __offset
    try:
        __offset = get_network_time(local_proxy) - time.time()
    except Exception,e:
        raise Exception('%s\nIs network down?' % str(e))

def get_time():
    """Get the time adjusted by offset."""
    return time.time() + __offset

if __name__=='__main__':
    init_offset()
    print __offset
    print get_time()
