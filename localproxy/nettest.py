import httplib
import threading
import time

class HTTPConnection(httplib.HTTPConnection):
    def __init__(self, host, host_ip):
        httplib.HTTPConnection.__init__(self, host)
        self.host_ip = host_ip
        
    def connect(self):
        orig_host, self.host = self.host, self.host_ip
        httplib.HTTPConnection.connect(self)
        self.host = orig_host


class HTTPSConnection(httplib.HTTPSConnection):
    def __init__(self, host, host_ip):
        httplib.HTTPSConnection.__init__(self, host)
        self.host_ip = host_ip
        
    def connect(self):
        orig_host, self.host = self.host, self.host_ip
        httplib.HTTPSConnection.connect(self)
        self.host = orig_host

plans = [('http', 'www.appspot.com'),
         ('http', 'www.google.cn'),
         ('https', 'www.appspot.com'),
         ('https', 'www.google.cn'),
         ('https', 'www.google.com.hk'),
         ('https', 'www.google.com'),
         ('http', '203.208.46.208'),
         ('http', '203.208.46.209'),
         ('http', '203.208.46.210'),
         ('http', '203.208.46.211'),
         ('http', '203.208.46.212'),
         ('https', '203.208.46.208'),
         ('https', '203.208.46.209'),
         ('https', '203.208.46.210'),
         ('https', '203.208.46.211'),
         ('https', '203.208.46.212'),
         ]

def probe_conn(plan, result, event):
    conn_type, host_ip = plan
    conn_class = { 'http' : HTTPConnection, 'https' : HTTPSConnection }
    try:
        conn = conn_class[conn_type]('www.appspot.com', host_ip)
        conn.request('GET', '/')
        resp = conn.getresponse()
        if resp.status < 400:
            result.append((conn_type, host_ip))
            event.set()
    except:
        pass

def BestChoice(prefer_https=False):
    result = []
    finishEvt = threading.Event()
    if prefer_https:
        filtered_plans = filter(lambda x:x[0] == 'https', plans)
    else:
        filtered_plans = plans
    threads = map(lambda plan:threading.Thread(target=probe_conn,
                                               args=(plan,result, finishEvt),
                                               kwargs={}),
                  filtered_plans)
    map(lambda x:x.start(), threads)

    finishEvt.wait(5.0)

    if len(result) > 0:
        return result[0]
    else:
        return None
    
