from google.appengine.ext import db
from google.appengine.api import memcache
import os, base64, time
import random

class PwdGuessCnt(db.Model):
    count = db.IntegerProperty(required=True, default=0)

class PendingRequest(db.Model):
    request = db.BlobProperty(required=True)
    timestamp = db.IntegerProperty(required=True)

def GetPwdGuessCnt():
    cnt = memcache.get('TheCount')
    if cnt:
        return cnt
    else:
        model = PwdGuessCnt.get_by_key_name('TheCount')
        cnt = model.count if model else 0
        memcache.set('TheCount', cnt)
        return cnt


def IncrPwdGuessCnt():
    model = PwdGuessCnt.get_by_key_name('TheCount')
    if not model:
        model = PwdGuessCnt(key_name = 'TheCount',
                            default=0)
    model.count += 1
    memcache.set('TheCount', model.count)
    model.put()

def DecrPwdGuessCnt():
    model = PwdGuessCnt.get_by_key_name('TheCount')
    if not model:
        model = PwdGuessCnt(key_name = 'TheCount',
                            default=0)
    model.count -= 1
    memcache.set('TheCount', model.count)
    model.put()

def ClearPwdGuessCnt():
    memcache.set('TheCount', 0)
    PwdGuessCnt(key_name = 'TheCount',
                count = 0).put()

def PendRequest(request):
    challenge = str(random.getrandbits(128))
    PendingRequest(key_name = base64.b64encode(challenge),
                   request = request,
                   timestamp = int(time.time())
                   ).put()
    return challenge

def RetrievePendingRequest(p):
    model = PendingRequest.get_by_key_name(base64.b64encode(p))
    if model is not None:
        r = model.request[:]
        model.delete()
        return r
    else:
        return None
