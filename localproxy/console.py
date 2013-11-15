import common
import getpass, time
import proxycore
class ConsoleNotifier:
    def PushStatus(self, text):
        print text

    def PushError(self, text):
        self.PushStatus(text)

    def PushMessage(self, text):
        print ''
        print '--------------------------------------------'
        print text
        print '--------------------------------------------'
        print ''

    def RequestCaptcha(self, msg, url):
        print msg
        print url
        return raw_input('Verification code: ')

    def RequestPassword(self):
        return getpass.getpass()


print '**********Secure GAppProxy %s******************' % common.VERSION
core = proxycore.ProxyCore(ConsoleNotifier())
core.Initialize()
core.StartProxy()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    core.StopProxy()
