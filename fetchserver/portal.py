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

import urlparse, StringIO, logging, base64, zlib, re, webapp2
from google.appengine.api import urlfetch, urlfetch_errors

import Cookie
import enc

class MainHandler(webapp2.RequestHandler):
    Software = "GAppProxy/2.0.0"
    # hop to hop header should not be forwarded
    H2H_Headers = ["connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"]
    Forbid_Headers = ["if-range"]
    Fetch_Max = 3

    def sendErrorPage(self, status, description):
        self.response.headers["Content-Type"] = "application/octet-stream"
        # http over http
        # header
        content = "HTTP/1.1 %d %s\r\n" % (status, description)
        content += "Server: %s\r\n" % self.Software
        content += "Content-Type: text/html\r\n"
        content += "\r\n"
        # body
        content += "<h1>Fetch Server Error</h1><p>Error Code: %d</p><p>%s</p>" % (status, description)
        self.response.out.write( enc.EncryptAES(content) )

    def post(self):
        if self.request.get('e') == '':
            self.error(404)
            return
        try:
            # decrypt post data
            t = self.request.get('e').encode('utf-8')

            dec_request = enc.DecodeAES(t)

            parse_request = urlparse.parse_qs(dec_request, keep_blank_values=True)
            # get post data
            orig_method = parse_request["method"][0]#self.request.get("method").encode("utf-8")
            orig_path = parse_request["path"][0]#base64.b64decode(self.request.get("encoded_path").encode("utf-8"))
            orig_headers = parse_request["headers"][0]#base64.b64decode(self.request.get("headers").encode("utf-8"))
            orig_post_data = parse_request["postdata"][0]#base64.b64decode(self.request.get("postdata").encode("utf-8"))

            # check method
            if orig_method != "GET" and orig_method != "HEAD" and orig_method != "POST":
                # forbid
                self.sendErrorPage(590, "Invalid local proxy, Method not allowed.")
                return
            if orig_method == "GET":
                method = urlfetch.GET
            elif orig_method == "HEAD":
                method = urlfetch.HEAD
            elif orig_method == "POST":
                method = urlfetch.POST

            # check path
            (scm, netloc, path, params, query, _) = urlparse.urlparse(orig_path)
            if (scm.lower() != "http" and scm.lower() != "https") or not netloc:
                self.sendErrorPage(590, "Invalid local proxy, Unsupported Scheme.")
                return
            # create new path
            new_path = urlparse.urlunparse((scm, netloc, path, params, query, ""))

            # make new headers
            new_headers = {}
            content_length = 0
            si = StringIO.StringIO(orig_headers)
            while True:
                line = si.readline()
                line = line.strip()
                if line == "":
                    break
                # parse line
                (name, _, value) = line.partition(":")
                name = name.strip()
                value = value.strip()
                nl = name.lower()
                if nl in self.H2H_Headers or nl in self.Forbid_Headers:
                    # don't forward
                    continue
                new_headers[name] = value
                if name.lower() == "content-length":
                    content_length = int(value)
            # predined header
            new_headers["Connection"] = "close"

            # check post data
            if content_length != 0:
                if content_length != len(orig_post_data):
                    logging.warning("Invalid local proxy, Wrong length of post data, %d!=%d." % (content_length, len(orig_post_data)))
                    #self.sendErrorPage(590, "Invalid local proxy, Wrong length of post data, %d!=%d." % (content_length, len(orig_post_data)))
                    #return
            else:
                orig_post_data = ""
            if orig_post_data != "" and orig_method != "POST":
                self.sendErrorPage(590, "Invalid local proxy, Inconsistent method and data.")
                return
        except enc.AuthenticationError, e:
            logging.error("Authentication Error: %s" % str(e))
            self.error(404)
            return
        except Exception, e:
            self.sendErrorPage(591, "Fetch server error: %s." % str(e))
            return

        # fetch, try * times
        range_request = False
        for i in range(self.Fetch_Max):
            try:
                # the last time, try with Range
                if i == self.Fetch_Max - 1 and method == urlfetch.GET and not new_headers.has_key("Range"):
                    range_request = True
                    new_headers["Range"] = "bytes=0-65535"
                # fetch
                resp = urlfetch.fetch(new_path,
                                      payload=orig_post_data,
                                      method=method,
                                      headers=new_headers,
                                      allow_truncated=False,
                                      follow_redirects=False,
                                      validate_certificate = True)
                # ok, got
                if range_request:
                    range_supported = False
                    for h in resp.headers:
                        if h.lower() == "accept-ranges":
                            if resp.headers[h].strip().lower() == "bytes":
                                range_supported = True
                                break
                        elif h.lower() == "content-range":
                            range_supported = True
                            break
                    if range_supported:
                        self.sendErrorPage(592, "Fetch server error: Retry with range header.")
                    else:
                        self.sendErrorPage(591, "Fetch server error: Sorry, file size exceeds Google's limit and the target server doesn't accept Range request.")
                    return
                break
            except Exception, e:
                logging.warning("urlfetch.fetch(%s, %s) error: %s." % (new_path, range_request and "Range" or "", str(e)))
        else:
            self.sendErrorPage(591, "Fetch server error: The target server may be down or not exist. Another possibility: try to request the URL directly.")
            return

        # forward
        self.response.headers["Content-Type"] = "application/octet-stream"
        # clear content
        content = ''
        # status line
        content += "HTTP/1.1 %d %s\r\n" % (resp.status_code, self.response.http_status_message(resp.status_code))
        # headers
        for header in resp.headers:
            if header.strip().lower() in self.H2H_Headers:
                # don't forward
                continue
            # there may have some problems on multi-cookie process in urlfetch.
            # Set-Cookie: "wordpress=lovelywcm%7C1248344625%7C26c45bab991dcd0b1f3bce6ae6c78c92; expires=Thu, 23-Jul-2009 10:23:45 GMT; path=/wp-content/plugins; domain=.wordpress.com; httponly, wordpress=lovelywcm%7C1248344625%7C26c45bab991dcd0b1f3bce6ae6c78c92; expires=Thu, 23-Jul-2009 10:23:45 GMT; path=/wp-content/plugins; domain=.wordpress.com; httponly,wordpress=lovelywcm%7C1248344625%7C26c45bab991dcd0b1f3bce6ae6c78c92; expires=Thu, 23-Jul-2009 10:23:45 GMT; path=/wp-content/plugins; domain=.wordpress.com; httponly
            if header.lower() == "set-cookie":
                scs = resp.headers[header].split(",")
                nsc = ""
                for sc in scs:
                    if nsc == "":
                        nsc = sc
                    elif re.match(r"[ \t]*[0-9]", sc):
                        # expires 2nd part
                        nsc += "," + sc
                    else:
                        # new one
                        content += "%s: %s\r\n" % (header, nsc.strip())
                        nsc = sc
                content += "%s: %s\r\n" % (header, nsc.strip())
                continue
            # other
            content += "%s: %s\r\n" % (header, resp.headers[header])

        content += "\r\n"

        content += resp.content
        # always compress and encrypt
        self.response.out.write( enc.EncryptAES(content) )

    def get(self):
        self.error(404)

app = webapp2.WSGIApplication([("/portal", MainHandler)],debug=True)
