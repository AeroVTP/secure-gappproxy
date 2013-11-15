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

import pkcs5
import base64
import getpass

import os, sys


def levenshtein_dist(a, b):
    d = list(range(len(a)+1))
    new_d = [0] * (len(a)+1)
    for i in xrange(1, len(b)+1):
        new_d[0] = i
        for j in xrange(1, len(a)+1):
            if j <= len(a) and i <= len(b) and a[j-1]==b[i-1]:
                new_d[j] = d[j-1]
            else:
                new_d[j] = min(d[j]+1, new_d[j-1]+1, d[j-1]+1)
        new_d, d = d, new_d
    return d[len(a)]

def longest_common_substring(a, b):
    d = [0] * len(a)
    new_d = [0] * len(a)
    maximum = 0
    for i in xrange(len(b)):
        for j in xrange(0, len(a)):
            if j < len(a) and i < len(b) and a[j] == b[i]:
                if i==0 or j==0:
                    new_d[j] = 1
                else:
                    new_d[j] = d[j-1] + 1
            else:
                new_d[j] = 0
            maximum = max(maximum, new_d[j])
        new_d, d = d, new_d
    return maximum




def load_dictionary():
    dict_path = os.path.join(os.path.dirname(sys.argv[0]),'pwddict')
    f = open(dict_path)
    dictionary = f.read().split('\n')
    f.close()
    return dictionary

def check_dictionary(dictionary, password, criterion, selector = min):
    min_dist = -1
    closest_word = selector(dictionary, key=lambda x:criterion(password,x))
    min_dist = criterion(password, closest_word)
    return min_dist, closest_word


def check_rule(password):
    pwd_space = 0
    import re
    if re.search('[a-z]', password):
        pwd_space += 26
    if re.search('[A-Z]', password):
        pwd_space += 26
    if re.search('[0-9]', password):
        pwd_space += 10
    if re.search('[!@£#\$%\^&\*\(\)\-_=\+]', password):
        pwd_space += 15
    if re.search("""[\?\/\.>\,<`~\\|"';:\]\}\[\{\s]""", password):
        pwd_space += 19
    return pwd_space ** len(password) >= 2 ** 29


def filter_repitition(password, least_len=3):
    if least_len > len(password)/2:
        return len(password)
    mask = [True]*len(password)
    for i in xrange(len(password)-least_len):
        sub = password[i:i+least_len]
        if password.count(sub) > 1:
            start = password.find(sub)
            while start!=-1:
                for j in xrange(start, start+least_len):
                    mask[j] = False
                start = password.find(sub, start+1)
    minlen = 0
    for j in xrange(len(password)):
        if mask[j]:
            minlen+=1
    return min(minlen, filter_repitition(password, least_len+1))

def get_password_hash(server):
    dictionary = None
    pwd = ''
    while True:
        pwd = getpass.getpass('Password for SecureGAppProxy: ')

        if len(pwd) < 6:
            print "This password is too short. Passwords must be at least 6 in length. Please try again."
            continue
        if not check_rule(pwd):
            print "This password is too simple. Consider adding more letters or numbers."
            continue
        if filter_repitition(pwd) <= 4:
            print "Password contains too many repititions. Try another one."
            continue

        pwd_confirm = getpass.getpass('Confirm password: ')
        if pwd != pwd_confirm:
            print "Two passwords aren't consistent, please try again."
            continue
        
        if not dictionary:
            print "Loading dictionary..."
            dictionary = load_dictionary()

        print "Checking password security..."
        length, closest = check_dictionary(dictionary, pwd.lower(), longest_common_substring, max)

        if len(pwd)-length <=3:
            print "Your password looks similar to a known weak password. Try another one."
            if raw_input("See the weak password?(y/n)").lower() =='y':
                print closest
            continue
            
        dist, closest = check_dictionary(dictionary, pwd.lower(), levenshtein_dist)
        if dist <= 3:
            print "Your password looks similar to a known weak password. Try another one."
            if raw_input("See the weak password?(y/n)").lower() =='y':
                print closest
            continue
        break

    print "Computing hash...\n"
    storage = pkcs5.PBKDF1(pwd, server.lower())
    #print "The password hash for %s: " % server
        
    return base64.urlsafe_b64encode(storage)

if __name__ == '__main__':
    print get_password_hash('test')
