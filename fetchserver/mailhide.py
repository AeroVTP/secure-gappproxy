import base64

try:
    from Crypto.Cipher import AES
except:
    raise Exception ("You need the pycrpyto library: http://cheeseshop.python.org/pypi/pycrypto/")

MAIL_HIDE_BASE="https://www.google.com/recaptcha/mailhide"

def asurl (email,
                 public_key,
                 private_key):
    """Wraps an email address with reCAPTCHA mailhide and
    returns the url. public_key is the public key from reCAPTCHA
    (in the base 64 encoded format). Private key is the AES key, and should
    be 32 hex chars."""

    cryptmail = _encrypt_string (email, base64.b16decode (private_key, casefold=True), '\0' * 16)
    base64crypt = base64.urlsafe_b64encode (cryptmail)

    return "%s/d?k=%s&c=%s" % (MAIL_HIDE_BASE, public_key, base64crypt)


def _pad_string (str, block_size):
    numpad = block_size - (len (str) % block_size)
    return str + numpad * chr (numpad)

def _encrypt_string (str, aes_key, aes_iv):
    if len (aes_key) != 16:
        raise Exception ("expecting key of length 16")
    if len (aes_iv) != 16:
        raise Exception ("expecting iv of length 16")
    return AES.new (aes_key, AES.MODE_CBC, aes_iv).encrypt (_pad_string (str, 16))
