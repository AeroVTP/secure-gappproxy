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

import BaseHTTPServer, SocketServer, urllib, urllib2, urlparse, zlib, socket, os, common, sys, errno, base64, re
import time, threading, StringIO, random, string
import enc, nonce
import keepalive
import fakehttps
import autoupdate
import config

try:
    import ssl
    ssl_enabled = True
except:
    ssl_enabled = False


# global varibles
listen_port = common.DEF_LISTEN_PORT
local_proxy = common.DEF_LOCAL_PROXY
server = ''
fetch_server = ''
rekey_server = ''
fetch_protocol = ''
local_dns_map = lambda x:x
password = None
auto_redirect = False

global_notifier = None

class LocalProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    PostDataLimit = 0x100000

    
    def log_message(self, format, *args):
        global_notifier.PushStatus("%s" % (format % args))

    
    def do_CONNECT(self):
            
        if not ssl_enabled:
            self.send_error(501, "Local proxy error, HTTPS needs Python2.6 or later.")
            self.connection.close()
            return

        # for ssl proxy
        (https_host, _, https_port) = self.path.partition(":")
        if https_port != "" and https_port != "443":
            self.send_error(501, "Local proxy error, Only port 443 is allowed for https.")
            self.connection.close()
            return

        # continue
        self.wfile.write("HTTP/1.1 200 OK\r\n")
        self.wfile.write("\r\n")
        
        keyFile, crtFile = fakehttps.getCertificate(https_host)
        ssl_sock = ssl.wrap_socket(self.connection,
                                 server_side=True,
                                 certfile=crtFile,
                                 keyfile=keyFile)

        # rewrite request line, url to abs
        first_line = ""
        while True:
            chr = ssl_sock.read(1)
            # EOF?
            if chr == "":
                # bad request
                ssl_sock.close()
                self.connection.close()
                return
            # newline(\r\n)?
            if chr == "\r":
                chr = ssl_sock.read(1)
                if chr == "\n":
                    # got
                    break
                else:
                    # bad request
                    ssl_sock.close()
                    self.connection.close()
                    return
            # newline(\n)?
            if chr == "\n":
                # got
                break
            first_line += chr
        # got path, rewrite
        (method, path, ver) = first_line.split()
        if path.startswith("/"):
            path = "https://%s" % https_host + path

        # connect to local proxy server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", listen_port))
        sock.send("%s %s %s\r\n" % (method, path, ver))
        
        # forward https request
        ssl_sock.settimeout(1)
        while True:
            try:
                data = ssl_sock.read(8192)
            except ssl.SSLError, e:
                if str(e).lower().find("timed out") == -1:
                    # error
                    sock.close()
                    ssl_sock.close()
                    self.connection.close()
                    return
                # timeout
                break
            if data != "":
                sock.send(data)
            else:
                # EOF
                break
        ssl_sock.setblocking(True)

        # simply forward response
        while True:
            data = sock.recv(8192)
            if data != "":
                ssl_sock.write(data)
            else:
                # EOF
                break

        # clean
        sock.close()
        ssl_sock.shutdown(socket.SHUT_WR)
        ssl_sock.close()
        self.connection.close()
   
    def do_METHOD(self):
        # check http method and post data
        method = self.command
        if method == "GET" or method == "HEAD":
            # no post data
            post_data_len = 0
        elif method == "POST":
            # get length of post data
            post_data_len = 0
            for header in self.headers:
                if header.lower() == "content-length":
                    post_data_len = int(self.headers[header])
                    break
            # exceed limit?
            if post_data_len > self.PostDataLimit:
                self.send_error(413, "Local proxy error, Sorry, Google's limit, file size up to 1MB.")
                self.connection.close()
                return
        else:
            # unsupported method
            self.send_error(501, "Local proxy error, Method not allowed.")
            self.connection.close()
            return

        # get post data
        post_data = ""
        if post_data_len > 0:
            post_data = self.rfile.read(post_data_len)
            if len(post_data) != post_data_len:
                # bad request
                self.send_error(400, "Local proxy error, Post data length error.")
                self.connection.close()
                return

        # do path check
        (scm, netloc, path, params, query, _) = urlparse.urlparse(self.path)
        if (scm.lower() != "http" and scm.lower() != "https") or not netloc:
            self.send_error(501, "Local proxy error, Unsupported scheme(ftp for example).")
            self.connection.close()
            return
        # create new path
        path = urlparse.urlunparse((scm, netloc, path, params, query, ""))

        # remove disallowed header
        dhs = []
        for header in self.headers:
            hl = header.lower()
            if hl == "if-range":
                dhs.append(header)
            elif hl == "range":
                dhs.append(header)
        for dh in dhs:
            del self.headers[dh]
        # create request for GAppProxy
        plain_params = urllib.urlencode({"method": method,
                                   "path": path,
                                   "headers": self.headers,
                                   "postdata": post_data,
                                   "version": common.VERSION})

        try:
            resp_plain = open_request(fetch_server, enc.EncryptAES(plain_params))
        except urllib2.HTTPError, e:
            if e.code == 404:
                self.send_error(404, "Local proxy error, Fetchserver not found at the URL you specified, please check it.")
            elif e.code == 502:
                self.send_error(502, "Local proxy error, Transmission error, or the fetchserver is too busy.")
            else:
                self.send_error(e.code)
            self.connection.close()
            return
        except urllib2.URLError, e:
            if local_proxy == "":
                ConfigureNetwork()
            self.connection.close()
            return

	#read the response and decompress & decrypt it
        resp_encrypted = resp_plain.read()
        resp = StringIO.StringIO( enc.DecryptAES(resp_encrypted) )
        
        # parse resp
        # for status line
        line = resp.readline()
        words = line.split()
        status = int(words[1])
        reason = " ".join(words[2:])

        # for large response
        if status == 592 and method == "GET":
            self.processLargeResponse(path)
            self.connection.close()
            return

        # normal response
        try:
            self.send_response(status, reason)
        except socket.error, (err, _):
            # Connection/Webpage closed before proxy return
            if err == errno.EPIPE or err == 10053: # *nix, Windows
                return
            else:
                raise

        # for headers
        text_content = True
        while True:
            line = resp.readline().strip()
            # end header?
            if line == "":
                break
            # header
            (name, _, value) = line.partition(":")
            name = name.strip()
            value = value.strip()
            # ignore Accept-Ranges
            if name.lower() == "accept-ranges":
                continue
            self.send_header(name, value)
            # check Content-Type
            if name.lower() == "content-type":
                if value.lower().find("text") == -1:
                    # not text
                    text_content = False
        self.send_header("Accept-Ranges", "none")
        self.end_headers()

	# for page
        self.wfile.write(resp.read())
        resp.close()

        self.connection.close()

    do_GET = do_METHOD
    do_HEAD = do_METHOD
    do_POST = do_METHOD

    def processLargeResponse(self, path):
        cur_pos = 0
        part_length = 0x100000 # 1m initial, at least 64k
        first_part = True
        content_length = 0
        text_content = True
        allowed_failed = 10

        while allowed_failed > 0:
            next_pos = 0
            self.headers["Range"] = "bytes=%d-%d" % (cur_pos, cur_pos + part_length - 1)
            # create request for GAppProxy
            plain_params = urllib.urlencode({"method": "GET",
                                       "path": path,
                                       "headers": self.headers,
                                       "postdata": "",
                                       "version": common.VERSION})

            resp_plain = open_request(fetch_server, enc.EncryptAES(plain_params))
            resp_encrypted = resp_plain.read()
            resp = StringIO.StringIO( enc.DecryptAES(resp_encrypted) )
            
            # parse resp
            # for status line
            line = resp.readline()
            words = line.split()
            status = int(words[1])
            # not range response?
            if status != 206:
                # reduce part_length and try again
                if part_length > 65536:
                    part_length /= 2
                allowed_failed -= 1
                continue

            # for headers
            if first_part:
                self.send_response(200, "OK")
                while True:
                    line = resp.readline().strip()
                    # end header?
                    if line == "":
                        break
                    # header
                    (name, _, value) = line.partition(":")
                    name = name.strip()
                    value = value.strip()
                    # get total length from Content-Range
                    nl = name.lower()
                    if nl == "content-range":
                        m = re.match(r"bytes[ \t]+([0-9]+)-([0-9]+)/([0-9]+)", value)
                        if not m or int(m.group(1)) != cur_pos:
                            # Content-Range error, fatal error
                            return
                        next_pos = int(m.group(2)) + 1
                        content_length = int(m.group(3))
                        continue
                    # ignore Content-Length
                    elif nl == "content-length":
                        continue
                    # ignore Accept-Ranges
                    elif nl == "accept-ranges":
                        continue
                    self.send_header(name, value)
                    # check Content-Type
                    if nl == "content-type":
                        if value.lower().find("text") == -1:
                            # not text
                            text_content = False
                if content_length == 0:
                    # no Content-Length, fatal error
                    return
                self.send_header("Content-Length", content_length)
                self.send_header("Accept-Ranges", "none")
                self.end_headers()
                first_part = False
            else:
                while True:
                    line = resp.readline().strip()
                    # end header?
                    if line == "":
                        break
                    # header
                    (name, _, value) = line.partition(":")
                    name = name.strip()
                    value = value.strip()
                    # get total length from Content-Range
                    if name.lower() == "content-range":
                        m = re.match(r"bytes[ \t]+([0-9]+)-([0-9]+)/([0-9]+)", value)
                        if not m or int(m.group(1)) != cur_pos:
                            # Content-Range error, fatal error
                            return
                        next_pos = int(m.group(2)) + 1
                        continue

            # for body
            self.wfile.write(resp.read())
            resp.close()

            # next part?
            if next_pos == content_length:
                return
            cur_pos = next_pos


class ThreadingHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    allow_reuse_address = 1
    def SetNotifier(self, notifier):
        self.notifier = notifier

    def handle_error(self, request, client_address):
        self.notifier.PushStatus('Connection Error: %s' % client_address[0])



    
def ConfigureNetwork():
    import nettest
    global fetch_protocol
    if fetch_protocol == 'https':
        net_bestchoice = nettest.BestChoice(True)
    else:
        net_bestchoice = nettest.BestChoice(False)
    if not net_bestchoice:
        return False
    else:
        protocol, host = net_bestchoice
        def useLocalDnsMap(x):
            if x.lower() == server.lower():
                return host
            else:
                return x
        global local_dns_map
        local_dns_map = useLocalDnsMap
        
        global listen_port, local_proxy, server, \
               fetch_server, rekey_server,  \
               password, auto_redirect
        fetch_protocol = protocol
        _rekey = config.GetParam('fetch_rekey')
        if server:
            fetch_server = "%s://%s/portal" % (fetch_protocol, server)
            rekey_server = "%s://%s/%s"  % (fetch_protocol, server, _rekey)
        return True


        


def LoadConfig():
    global listen_port, local_proxy, server, \
           fetch_protocol, fetch_server, rekey_server,  \
           password, auto_redirect
    listen_port = config.GetParam('listen_port')
    local_proxy = config.GetParam('local_proxy')
    server = config.GetParam('fetch_server')
    fetch_protocol = config.GetParam('fetch_protocol')
    _rekey = config.GetParam('fetch_rekey')
    if server:
        fetch_server = "%s://%s/portal" % (fetch_protocol, server)
        rekey_server = "%s://%s/%s"  % (fetch_protocol, server, _rekey)
    password = config.GetParam('password')
    auto_redirect = config.GetParam('auto_redirect')
    
            
def open_request(path, data, timeout=None):
    params = urllib.urlencode({'e': base64.urlsafe_b64encode(data)})
    
    # accept-encoding: identity, *;q=0
    # connection: close
    request = urllib2.Request(path)
    def rand_referer():
        def reval_rep(func, times):
            result = ''
            for i in xrange(times):
                result+= func()
            return result
        rand_str = lambda: reval_rep(lambda:random.choice(string.ascii_lowercase),
                                     random.randint(2,10)
                                     )
        rand_dir = lambda: rand_str()+'/'
        rand_dirs = lambda: reval_rep(rand_dir, random.randint(0,3))
        template = 'http://www.%(domain)s.com/%(dirs)s%(filename)s.html'
        return template % dict(domain=rand_str(),
                               dirs=rand_dirs(),
                               filename=rand_str())
        
    #When connecting the fetchserver with HTTP,
    #Try to make the http header similar to IE9
    if fetch_protocol == 'http':        
        request.add_header("Accept", "text/html, application/xhtml+xml, */*")
        request.add_header("Referer", rand_referer())
        request.add_header("Accept-Language", "zh-CN")
        request.add_header("User-Agent", "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; NP06)")
        request.add_header("Accept-Encoding", "gzip, deflate")#"identity, *;q=0")
        request.add_header("Cache-Control", "no-cache")
        
    # create new opener
    if local_proxy != "":
        proxy_handler = urllib2.ProxyHandler({"http": local_proxy, "https":local_proxy})
    else:
        proxy_handler = urllib2.ProxyHandler({})

    if fetch_protocol == 'http':
        keepalive_handler = keepalive.HTTPHandler(localdnsmap=local_dns_map)
    elif fetch_protocol == 'https':
        keepalive_handler = keepalive.HTTPSHandler(localdnsmap=local_dns_map)
        
    opener = urllib2.build_opener(proxy_handler, keepalive_handler)

    
    # set the opener as the default opener
    urllib2.install_opener(opener)
    if timeout:
        return urllib2.urlopen(request, params, timeout)
    else:
        return urllib2.urlopen(request, params)

def get_reply(path, data, timeout=None):
    return open_request(path, data, timeout).read()

def rekey(password, notifier, persistent=True):
    import bpkaspak, key
    delay = 2
    while True:
        try:
            global rekey_server
            c=bpkaspak.KeyAgreementClient(password)
            notifier.PushStatus('Checking server identity...')
            c0 = c.Phase0()
            resp = open_request(rekey_server, c0)
            if resp.geturl().lower().startswith('https://www.google.com/recaptcha/mailhide'):
                msg = """The server detected an online password guess attack. Hence, further verification is required.
Please visit the link below and follow the instruction.
After solving the CAPTCHA, you'll see a verification code. Copy it and paste it here."""
                verification = notifier.RequestCaptcha(msg, resp.geturl())
                s1 = get_reply(rekey_server, verification)
            else:
                s1 = resp.read()
            c1 = c.Phase1(s1)
            notifier.PushStatus('Showing client identity...')
            s2 = get_reply(rekey_server, c1)
            key.SetKey(c.DeriveKey("Encrypt"),
                       c.DeriveKey("Authenticate")
                       )
            return True
        except urllib2.HTTPError, e:
            notifier.PushError('Incorrect server response (%s). Deployment successful?' % str(e))
            return False
        except urllib2.URLError, e:
            if persistent:
                notifier.PushStatus('Network seems to be down. Retry after %d seconds...' % delay)
                time.sleep(delay)
                delay *= 1.5
            else:
                notifier.PushError('Error occurred: %s'% str(e))
                return False
        except Exception, e:
            notifier.PushError('Error occurred: %s'% str(e))
            return False



class ProxyCore:
    def __init__(self, notifier):
        self.notifier = notifier
        self.running = False
        global global_notifier
        global_notifier = notifier

        
    def StartProxy(self, persistent=True):
        global listen_port, local_proxy, server, \
            fetch_protocol, fetch_server, rekey_server,  \
            password
        if self.running:
            self.notifier.PushError('Server already running!')
            return False

        if server == "":
            self.notifier.PushError('Fetch server not found. Please add your fetch server in proxy.conf')
            return False


        try:
            self.httpd = ThreadingHTTPServer(("localhost", listen_port), LocalProxyHandler)
            self.httpd.SetNotifier(self.notifier)
        except socket.error, (errno, errstr):
            #10048 for win, 98 for linux
            if errno==10048 or errno==98:
                self.notifier.PushError("Unable to listen on port %d.\nIs another proxy server running?" %listen_port)
            else:
                self.notifier.PushError(errstr)
            return False
        except Exception, e:
            self.notifier.PushError("Error:\n%s" % str(e))
            return False
        
        self.notifier.PushStatus('Logging into %s' % server)
        if password is None:
            import pkcs5
            password = pkcs5.PBKDF1(self.notifier.RequestPassword(), server.lower())

        if not rekey(password, self.notifier, persistent):
            self.notifier.PushStatus("Authentication failed.")
            self.httpd.socket.close()
            return False
        else:
            self.notifier.PushStatus("Authentication successful.")

            self.serve_thread = threading.Thread(target=self.httpd.serve_forever)
            self.serve_thread.setDaemon(True)
            self.serve_thread.start()
            self.running = True
            
            self.notifier.PushStatus("Start serving at localhost:%d..." % listen_port)
            
            try:
                updated, msg = autoupdate.auto_update(listen_port)
                if updated:
                    self.notifier.PushMessage(msg)
            except Exception, e:
                pass
                
            self.notifier.PushStatus("Start serving at localhost:%d..." % listen_port)

        nonce.Initialize()
        return True

            

    def StopProxy(self):
        self.httpd.shutdown()
        self.httpd.socket.close()
        self.running = False
        nonce.Finalize()
        return True

    def Running(self):
        return self.running

    def Initialize(self):
        LoadConfig()

        if auto_redirect and local_proxy == "":
            self.notifier.PushStatus("Detecting network connectivity...")
            if ConfigureNetwork():
                self.notifier.PushStatus('Use google proxy...')

        #Checking fake CA
        fakehttps.checkCA()

        self.notifier.PushStatus('Synchronizing time from Internet...')
        import synctime
        try:
            synctime.init_offset(local_proxy)
        except Exception, e:
            self.notifier.PushError('Error in time synchronization: %s' % str(e))

            

