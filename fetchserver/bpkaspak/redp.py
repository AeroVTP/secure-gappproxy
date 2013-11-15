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
from mymath import *        
        

def ECREDP1(password, domain, hashtouse, oLen):
    """With reference to IEEE 1363.2 8.2.17 ECREDP-1"""
    assert domain.m == 1, "Not implemented for m>1."
    HashRE = lambda x:hashtouse(x).digest()
    o1 = HashRE(password)
    i1 = OS2IP(o1)
    while True:
        o2 = I2OSP(i1, oLen)
        o3 = HashRE(o2)
        x = I2FEP( OS2IP(o3) % domain.q, domain )
        assert x!=0, "See IEEE 1363.2-2008 8.2.17 Note 1"
        u = i1 % 2
        assert domain.p > 3, "Not implemented for p=3"
        alpha = (x*x*x + domain.a * x + domain.b) % domain.p

        assert alpha!=0, "See IEEE 1363.2-2008 8.2.17 Note 1"
        beta = square_mod_prime(domain.p, alpha)
        if not beta:
            i1 += 1
            continue
        y = ((domain.p-1)**u * beta) % domain.p
        T1 = Point(domain, x, y)
        e = domain.k * T1
        assert e != INFINITY, "See IEEE 1363.2-2008 8.2.17 Note 1"
        return e


                    
                    

        
    
        

    
