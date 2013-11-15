#!/usr/bin/env python
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

from Crypto.Cipher import AES
import base64, zlib
import urllib2
import hashlib
#import io
import os
import time, calendar
import nonce
import key

BLOCK_SIZE = 16

HMAC_SIZE = hashlib.sha256().digest_size


class AuthenticationError(Exception):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason


class AESCipher:
    """an AES cipher  in CBC mode"""
    def __init__(self, iv):
        self.cipher = AES.new(key.GetEncryptKey(), AES.MODE_CBC, iv)

    def encrypt(self, data):
        return self.cipher.encrypt(AESCipher.pad(data, BLOCK_SIZE))
    
    def decrypt(self, data):
        return AESCipher.unpad(self.cipher.decrypt(data), BLOCK_SIZE)

    @staticmethod
    def pad(x, block_size):
        """With reference to RFC 5652 6.3"""
        assert 1 <= block_size <= 256
        pad_len = block_size - len(x) % block_size
        return x + chr(pad_len) * pad_len

    @staticmethod
    def unpad(x, block_size):
        """With reference to RFC 5652 6.3"""
        assert 1 <= block_size <= 256
        if len(x) == 0 or x[-1] < len(x):
            raise AuthenticationError('Padding error.')
        return x[:-ord(x[-1])]
		

def CalcHMAC(msg):
    import hmac
    return hmac.new(key.GetAuthKey(), msg, hashlib.sha256).digest()

def EncryptAES(s):
    """Encrypt in AES. IV prepended. Compression applied.
       Users should always use DecryptAES as reverse function.
    """
    iv = os.urandom(BLOCK_SIZE)
    compressed = zlib.compress(nonce.GenerateNonce() + s)
    ciphertext = AESCipher(iv).encrypt(compressed)
    return iv + ciphertext + CalcHMAC(iv + ciphertext)

def DecryptAES(e):
    """Decrypt in AES. Reverse function of EncryptAES.
       Throws TimestampError() if timestamp validation fails.
    """
    try:
        if len(e) < HMAC_SIZE:
            raise AuthenticationError('Incorrect packet format.')
        if CalcHMAC(e[:-HMAC_SIZE]) != e[-HMAC_SIZE:]:
            raise AuthenticationError('The message integrity is compromised.')
        e = e[:-HMAC_SIZE]
        if len(e) < BLOCK_SIZE:
            raise AuthenticationError('Incorrect packet format.')
        iv = e[:BLOCK_SIZE]
        decrypted = AESCipher(iv).decrypt(e[BLOCK_SIZE:])
        uncompressed = zlib.decompress(decrypted)
        #get timestamp and verify it
        if len(uncompressed) < nonce.NONCE_LENGTH:
            raise AuthenticationError('Incorrect packet format.')
        ts = uncompressed[:nonce.NONCE_LENGTH]
        if not nonce.CheckNonce(ts):
            raise AuthenticationError('The message is replayed.')
        return uncompressed[nonce.NONCE_LENGTH:]
    except AuthenticationError, e:
        raise e
    except Exception, e:
        raise AuthenticationError(str(e))

#Encrypt/Decrypt with base 64 and compression
EncodeAES = lambda s: base64.urlsafe_b64encode(EncryptAES(s))
DecodeAES = lambda e: DecryptAES(base64.urlsafe_b64decode(e))



if __name__ == '__main__':
    
    from binascii import hexlify, unhexlify
    def test_encrypt(name, k, iv, testvector, result):
        cipher = AES.new(k, AES.MODE_CBC, iv).encrypt(testvector)
        plain = AES.new(k, AES.MODE_CBC, iv).decrypt(cipher)
        if cipher == result and plain == testvector:
            print name, 'Pass'
        else:
            print name, 'Fail'
    k = unhexlify('2b7e151628aed2a6abf7158809cf4f3c')
    iv = unhexlify('000102030405060708090a0b0c0d0e0f')
    test_encrypt('Encrypt1', unhexlify('2b7e151628aed2a6abf7158809cf4f3c'),
                 unhexlify('000102030405060708090a0b0c0d0e0f'),
                 unhexlify('6bc1bee22e409f96e93d7e117393172a'),
                 unhexlify('7649abac8119b246cee98e9b12e9197d')
                 )
    test_encrypt('Encrypt2', unhexlify('2b7e151628aed2a6abf7158809cf4f3c'),
                 unhexlify('7649ABAC8119B246CEE98E9B12E9197D'),
                 unhexlify('ae2d8a571e03ac9c9eb76fac45af8e51'),
                 unhexlify('5086cb9b507219ee95db113a917678b2')
                 )
    test_encrypt('Encrypt3', unhexlify('603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4'),
                 unhexlify('000102030405060708090A0B0C0D0E0F'),
                 unhexlify('6bc1bee22e409f96e93d7e117393172a'),
                 unhexlify('f58c4c04d6e5f1ba779eabfb5f7bfbd6')
                 )
    test_encrypt('Encrypt4', unhexlify('603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4'),
                 unhexlify('F58C4C04D6E5F1BA779EABFB5F7BFBD6'),
                 unhexlify('ae2d8a571e03ac9c9eb76fac45af8e51'),
                 unhexlify('9cfc4e967edb808d679f777bc6702c7d')
                 )



    def test_decrypt_error(name, error, testcase):
        try:
            DecryptAES(testcase)
            print name, 'Fail'
        except AuthenticationError, e:
            if str(e) == error:
                print name, 'Pass'
            else:
                print name, 'Fail', str(e)
                
    test_decrypt_error('Tamper_1', 'The message integrity is compromised.',
                       unhexlify('2bf0c528ce1083ca7eec0bb8b5911d35ceb18abd5746d9252c625c80e6481ce589922abefe6d7ffc0283a947650d4115'))
    test_decrypt_error('Tamper_2', 'The message integrity is compromised.',
                       unhexlify('1bf0c528ce1083ca7eec0bb8b5911d35ceb18abd5746d9252c625c80e6481ce589922abefe6d7ffc0283a947650d4114'))
    test_decrypt_error('Nothing', 'Incorrect packet format.',
                       '')
    test_decrypt_error('NoIV', 'Incorrect packet format.',
                       unhexlify('ba1e423d08a84e4425e3188fbd5b65d7bc7e166321b439a81fab787004b6e63b'))
    test_decrypt_error('NoNonce', 'Incorrect packet format.',
                       unhexlify('7abe28836691ac8c5f3fa374e6a1187515dd009210b1f116b18abb8cf8867be1f1ec400dba68d856672f750bec84762f4a71d3e3051c028ac2068b26b24ae300'))
    test_decrypt_error('OutdatedNonce', 'The message is replayed.',
                       unhexlify('04d6c570aeb2b6a8d41ffbd36e1052c4b75cdb2a6fe6ac3355652921e3f3f03e6433e60cb9308b40e1505661e994f301253ad2dc02fed4505eaab9d322a1adca42fbd209a706da688e820745e6f91665'))
    encrypt = EncryptAES('123123')
    c= DecryptAES(encrypt)
    if c=='123123':
        print 'Simple Pass'
    else:
        print 'Simple Fail'
    test_decrypt_error('ReplayMessage', 'The message is replayed.',
                       encrypt)

    def test_pad(name, x,block_size, out,func=AESCipher.pad, error=None):
        if func(x, block_size)==out:
            print name, 'Pass'
        else:
            print name, 'Fail'
            
    def test_pad_error(name, x, block_size, error):
        try:
            func(x, block_size)
            print name, 'Fail'
        except Exception, e:
            if str(e) == error:
                print name, 'Pass'
            else:
                print name, 'Fail'
    test_pad('pad1', '12367890', 5, '12367890\x02\x02')
    test_pad('pad2', '1234567890', 5, '1234567890\x05\x05\x05\x05\x05')
    test_pad('pad3', '', 5, '\x05\x05\x05\x05\x05')

    test_pad('unpad1', '1234567890\x05\x05\x05\x05\x05', 5, '1234567890', func=AESCipher.unpad)
    test_pad('unpad2', '12367890\x02\x02', 5, '12367890', func=AESCipher.unpad)
    test_pad('unpad3', '\x01', 5, '', func=AESCipher.unpad)
    test_pad_error('unpad4', '\x03', 3, 'Padding error.')
    test_pad_error('unpad5', '', 3, 'Padding error.')

    
