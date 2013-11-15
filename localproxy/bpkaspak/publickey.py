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


from conversion import *
from ellipticcurve import *

def PEPKGP_PAK(domain, private_key, password_mask):
    """With reference to IEEE 1363.2 8.2.5 PEPKGP-PAK"""
    return private_key * domain.g + password_mask

def SVDP_PAK1_CLIENT(domain, c_private, s_public):
    """With reference to IEEE 1363.2 8.2.21"""
    zg = c_private * s_public
    return GE2SVFEP(zg)

def SVDP_PAK2(domain, s_private, password_mask, c_public):
    zg=(c_public+(-1)*password_mask)*s_private
    return GE2SVFEP(zg)

def PKGP_DH(domain, s_private):
    """With reference to IEEE 1363.2 8.2.9"""
    return s_private * domain.g

def KDF1(Z, parameter, hashfunc):
    """With reference to IEEE 1363-2000 13.1 KDF1"""
    return hashfunc(Z+parameter).digest()

def KCF1(parameter, hashfunc,  c_public, s_public, shared_key, password, domain):
    oc = GE2OSP_X(c_public, domain)
    os = GE2OSP_X(s_public, domain)
    hashre = lambda x: hashfunc(x).digest()
    o = hashre(parameter + oc + os + shared_key + password)
    return o

def ValidatePublicKey(domain, public):
    """With reference to IEEE 1363-2000 A.16.10"""
    if public == INFINITY:
        return False
    if not (0 <= public.x() < domain.p):
        return False
    if not (0 <= public.y() < domain.p):
        return False
    if not domain.curve.contains_point(public.x(), public.y()):
        return False
    if domain.r * public != INFINITY:
        return False
    return True
