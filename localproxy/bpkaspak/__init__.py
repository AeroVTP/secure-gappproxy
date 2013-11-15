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
from publickey import *
from redp import *

class ProtocolAbort(Exception):
    def __str__(self):
        return "An error occured in key agreement protocol. Password incorrect?"

import hashlib
HASH_FUNC = hashlib.sha256
HASH_LEN = 32

secp256k1 = Domain(p=
                   0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL,
                   m=1, a=
                   0x0000000000000000000000000000000000000000000000000000000000000000L,
                   b=
                   0x0000000000000000000000000000000000000000000000000000000000000007L,
                   gx=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L,
                   gy=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8L,
                   r=
                   0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L,
                   k = 0x01L, length=32, )
secp256r1 = Domain(p=0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFL,
                   m=1,
                   a=0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFCL,
                   b=0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604BL,
                   gx=0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296L,
                   gy=0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5L,
                   r=0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551L,
                   k=0x01L,
                   length=32,
                   )
DOMAIN = secp256r1
import random


class KeyAgreementBasic:
    def DeriveKey(self, parameter):
        return KDF1(self.shared_string, parameter, HASH_FUNC)


class KeyAgreementClient(KeyAgreementBasic):
    def __init__(self, password):
        self.__password = password
        self.__pasword_mask = ECREDP1(self.__password, DOMAIN, HASH_FUNC, HASH_LEN)

    def Phase0(self):
        try:
            self.__c_private = random.SystemRandom().randrange(1, DOMAIN.r)
            self.__c_epublic = PEPKGP_PAK(DOMAIN, self.__c_private, self.__pasword_mask)
            c_epublic_os = GE2OSP(self.__c_epublic, DOMAIN)
            return c_epublic_os
        except Exception, e:
            raise ProtocolAbort()

    def Phase1(self, msg):
        try:
            self.__s_public = OS2GEP(msg[:-HASH_LEN], DOMAIN)
            confirm_s = msg[-HASH_LEN:]
            if not ValidatePublicKey(DOMAIN, self.__s_public):
                raise ProtocolAbort()
            shared_element = SVDP_PAK1_CLIENT(DOMAIN, self.__c_private, self.__s_public)
            self.shared_string = FE2OSP(shared_element, DOMAIN)

            confirm_s_ = KCF1('\x03', HASH_FUNC, self.__c_epublic, self.__s_public, self.shared_string, self.__password, DOMAIN)
            if confirm_s != confirm_s_:
                raise ProtocolAbort()
            confirm_c = KCF1('\x04', HASH_FUNC, self.__c_epublic, self.__s_public, self.shared_string, self.__password, DOMAIN)
            return confirm_c
        except ProtocolAbort, e:
            raise e
        except Exception, e:
            raise ProtocolAbort()


class KeyAgreementServer(KeyAgreementBasic):
    def __init__(self, password):
        self.__password = password
        self.__password_mask = ECREDP1(self.__password, DOMAIN, HASH_FUNC, HASH_LEN)

    def Phase1(self, msg):
        try:
            self.__c_epublic = OS2GEP(msg, DOMAIN)
            if not ValidatePublicKey(DOMAIN, self.__c_epublic):
                raise ProtocolAbort()
            __s_private = random.SystemRandom().randrange(1, DOMAIN.r)
            self.__s_public = PKGP_DH(DOMAIN, __s_private)
            shared_element = SVDP_PAK2(DOMAIN, __s_private, self.__password_mask, self.__c_epublic)
            self.shared_string = FE2OSP(shared_element, DOMAIN)

            confirm_s = KCF1('\x03', HASH_FUNC, self.__c_epublic, self.__s_public, self.shared_string, self.__password, DOMAIN)
            self.confirm_c = KCF1('\x04', HASH_FUNC, self.__c_epublic, self.__s_public, self.shared_string, self.__password, DOMAIN)

            return GE2OSP(self.__s_public, DOMAIN) + confirm_s
        except ProtocolAbort, e:
            raise e
        except Exception, e:
            raise ProtocolAbort()

    def Phase2(self, msg):
        assert msg == self.confirm_c
        return None
