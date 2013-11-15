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

def square_mod_prime(p, g):
    """With reference to IEEE 1363-2000 A.2.5"""
    assert 0 < g < p
    if pow(g, (p-1)/2, p) != 1:
        return None
    if p % 4 == 3:
        k = p /4
        z = pow(g, k+1, p)
    elif p % 8 == 5:
        k = p / 8
        gamma = pow(2*g, k, p)
        i = 2*g*(gamma**2) % p
        z = g * gamma * (i - 1) % p
    elif p % 8 == 1:
        assert False, "Not implemented for 8k+1 primes."
    else:
        assert False, "Should not be here."
    assert z*z % p==g, "Check answer correctness."
    return z
        
     
