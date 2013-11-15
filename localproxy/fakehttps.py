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

import os, socket
import common
cert_dir = common.CERT_DIR
try:
    from OpenSSL import crypto
except ImportError:
    crypto = None
try:
    import ssl
except ImportError:
    ssl = None

import threading
LOCK = threading.Lock()

def _createKeyPair(type=None, bits=1024):
    if type is None:
        type = crypto.TYPE_RSA
    pkey = crypto.PKey()
    pkey.generate_key(type, bits)
    return pkey

def _createCertRequest(pkey, subj, digest='sha1'):
    req = crypto.X509Req()
    subject = req.get_subject()
    for k,v in subj.iteritems():
        setattr(subject, k, v)
    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req

def _createCertificate(req, issuerKey, issuerCert, serial,
                       notBefore, notAfter, digest='sha1'):
    cert = crypto.X509()
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(notBefore)
    cert.gmtime_adj_notAfter(notAfter)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, digest)
    return cert

def _makeCA(dump=True):
    pkey = _createKeyPair(bits=2048)
    import os, base64
    subj = {'countryName': 'CN', 'organizationalUnitName': 'SecureGAppProxy Root',
            'stateOrProvinceName': 'Internet', 'localityName': 'Cernet',
            'organizationName': 'SecureGAppProxy',
            'commonName': 'SecureGAppProxy CA ' + base64.b64encode(os.urandom(20))}#Randomize issuer name
    req = _createCertRequest(pkey, subj)
    cert = _createCertificate(req, pkey, req, 0, 0, 60*60*24*7305) #20 years
    if dump:
        pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    return pkey, cert

def _makeCert(host, cakey, cacrt, serial, dump=True):
    pkey = _createKeyPair()
    subj = {'countryName': 'CN', 'organizationalUnitName': 'SecureGAppProxy Branch',
            'stateOrProvinceName':'Internet', 'localityName': 'Cernet',
            'organizationName': host, 'commonName': host}
    req = _createCertRequest(pkey, subj)
    cert = _createCertificate(req, cakey, cacrt, serial, 0, 60*60*24*7305)
    if dump:
        pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    return pkey, cert

def read_file(filename):
    try:
        f = open(filename, 'rb')
        c = f.read()
        f.close()
        return c
    except IOError:
        return None

def write_file(filename, content):
    try:
        f = open(filename, 'wb')
        f.write(str(content))
        f.close()
    except IOError:
        pass

_g_serial = _g_CA = None

def checkCA():
    if not crypto: return
    global _g_serial, _g_CA
    #Check cert directory
    if not os.path.isdir(cert_dir):
        if os.path.isfile(cert_dir):
            os.remove(cert_dir)
        os.mkdir(cert_dir)
    #Check CA file
    cakeyFile = os.path.join(cert_dir, '_ca.key')
    cacrtFile = os.path.join(cert_dir, '_ca.crt')
    serialFile = os.path.join(cert_dir, '_serial')
    cakey = read_file(cakeyFile)
    cacrt = read_file(cacrtFile)
    _g_serial = read_file(serialFile)
    try:
        cakey = crypto.load_privatekey(crypto.FILETYPE_PEM, cakey)
        cacrt = crypto.load_certificate(crypto.FILETYPE_PEM, cacrt)
        _g_CA = cakey, cacrt
        _g_serial = int(_g_serial)
    except:
        _g_CA = cakey, cacrt = _makeCA(False)
        _g_serial = 0
        #Remove old certifications, because ca and cert must be in pair
        for name in os.listdir(cert_dir):
            path = os.path.join(cert_dir, name)
            if os.path.isfile(path):
                os.remove(path)
        cakey = crypto.dump_privatekey(crypto.FILETYPE_PEM, cakey)
        cacrt = crypto.dump_certificate(crypto.FILETYPE_PEM, cacrt)
        write_file(cakeyFile, cakey)
        write_file(cacrtFile, cacrt)
        write_file(serialFile, _g_serial)

def getCertificate(host):
    #When two threads concurrently calls getCertificate with the same host,
    #the .key and .crt files generated might not be paired.
    #Hence, the global lock.
    LOCK.acquire()
    keyFile = os.path.join(cert_dir, '%s.key' % host)
    crtFile = os.path.join(cert_dir, '%s.crt' % host)
    if not os.path.isfile(keyFile) or not os.path.isfile(crtFile):
        if not crypto:
            return (common.DEF_KEY_FILE, common.DEF_CERT_FILE)
        global _g_serial
        _g_serial += 1
        #host variable may violate the maximum length limit of OpenSSL
        #If the host is too long, try to shorten it by omitting the subdomain.
        #super-long.example.com will be shortened to *.example.com
        if len(host) > 64:
            host_split = host.split('.')
            for i in xrange(len(host_split)):
                newhost_split = host_split[i+1:]
                newhost_split.insert(0, '*')
                newhost = '.'.join(newhost_split)
                if len(newhost) <= 64:
                    host = newhost
                    break

        key, crt = _makeCert(host, _g_CA[0], _g_CA[1], _g_serial)
        write_file(keyFile, key)
        write_file(crtFile, crt)
        write_file(os.path.join(cert_dir,'_serial'), _g_serial)
    LOCK.release()
    return keyFile, crtFile
