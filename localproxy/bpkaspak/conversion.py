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

from ellipticcurve import *
from mymath import *

class ConversionError(Exception):
    pass

def OS2IP(serialized):
    num = 0L
    for i in serialized:
        num = num * 256 + ord(i)
    return num

def I2OSP(num, length=None):
    serialized = ""
    while num != 0:
        serialized += chr(num % 256)
        num /= 256
    if length:
        serialized += "\x00" * (length-len(serialized))
    return serialized[::-1]

def I2FEP(x, domain=None):
    if __debug__:
        assert not domain or domain.m == 1, "Case for m > 1 hasn't been implemented."
    return x

def FE2IP(a):
    return a

def FE2OSP(a, domain):
    return I2OSP(FE2IP(a), domain.len)

def OS2FEP(s, domain):
    return I2FEP(OS2IP(s))

def GE2SVFEP(e):
    """With reference to IEEE 1363.2 5.3.2"""
    if e == INFINITY:
        return 0
    return e.x()

def GE2OSP_X(e, domain):
    return EC2OSP_X(e, domain)

def EC2OSP_X(e, domain):
    """With reference to IEEE Std 1363a-2004 5.5.6.3"""
    return I2OSP(1, 1) + FE2OSP(e.x(), domain)

def GE2OSP(point, domain):
    return ECP2OSP(point, domain)

def OS2GEP(serialized, domain):
    return OS2ECPP(serialized, domain)

def ECP2OSP(point, domain):
    """Not so compliant to standard :-)
    Assuming compressed mode."""
    result = FE2OSP(point.x(), domain)
    #In fact, only 1-bit is necessary to represent point.y()
    #But, for convenience, we are using 1-byte here.
    if point.y() % 2 == 0:
        result += '\x00'
    else:
        result += '\x01'
    return result

def OS2ECPP(e, domain):
    """Not so compliant to standard"""

    x = OS2FEP(e[:domain.len], domain)
    assert domain.p > 3, "Not implemented for p=3"
    alpha = (x*x*x + domain.a * x + domain.b) % domain.p
    beta = square_mod_prime(domain.p, alpha)
    if not beta:
        raise ConversionError()
    if beta % 2 == OS2IP(e[domain.len:domain.len+1])%2:
        y = beta
    else:
        y = ((domain.p-1) * beta) % domain.p
    return Point(domain, x, y)
