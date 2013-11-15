import sys
sys.path.append('../fetchserver/bpkaspak')
from __init__ import *

if __name__ == '__main__':
    ms= "*j2W@fS"
    c = KeyAgreementClient(ms)
    s = KeyAgreementServer(ms)

    import binascii, time
    start_time = time.time()
    c0 = c.Phase0()
    print 'c0 :', binascii.hexlify(c0)
    s1 = s.Phase1(c0)
    print 's1 : ', binascii.hexlify(s1)
    c1 = c.Phase1(s1)
    print 'c1 : ', binascii.hexlify(c1)
    s2 = s.Phase2(c1)
    print 's2 : ', s2

    print s.shared_string == c.shared_string
    print 'Test completed in %s s.' % (time.time() - start_time)

from conversion import *

if __name__ == '__main__':
    print I2OSP(1323123123123)
    print OS2IP('asdf')
    print I2OSP(OS2IP('asdf'))
    print OS2IP(I2OSP(1323123123123))
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
    import binascii
    test_point = secp256r1.g*256
    print OS2ECPP(ECP2OSP(test_point, secp256r1), secp256r1) == test_point
    test_point = secp256r1.g*257
    print OS2ECPP(ECP2OSP(test_point, secp256r1), secp256r1) == test_point
    test_point = secp256r1.g*258
    print OS2ECPP(ECP2OSP(test_point, secp256r1), secp256r1) == test_point
    test_point = secp256r1.g*259
    print OS2ECPP(ECP2OSP(test_point, secp256r1), secp256r1) == test_point

from ellipticcurve import *

if __name__ == "__main__":


  def test_add( c, x1, y1, x2,  y2, x3, y3 ):
    """We expect that on curve c, (x1,y1) + (x2, y2 ) = (x3, y3)."""
    p1 = Point( c, x1, y1 )
    p2 = Point( c, x2, y2 )
    p3 = p1 + p2
    print "%s + %s = %s" % ( p1, p2, p3 ),
    if p3.x() != x3 or p3.y() != y3:
      print " Failure: should give (%d,%d)." % ( x3, y3 )
    else:
      print " Good."

  def test_double( c, x1, y1, x3, y3 ):
    """We expect that on curve c, 2*(x1,y1) = (x3, y3)."""
    p1 = Point( c, x1, y1 )
    p3 = p1.double()
    print "%s doubled = %s" % ( p1, p3 ),
    if p3.x() != x3 or p3.y() != y3:
      print " Failure: should give (%d,%d)." % ( x3, y3 )
    else:
      print " Good."

  def test_multiply( c, x1, y1, m, x3, y3 ):
    """We expect that on curve c, m*(x1,y1) = (x3,y3)."""
    p1 = Point( c, x1, y1 )
    p3 = p1 * m
    print "%s * %d = %s" % ( p1, m, p3 ),
    if p3.x() != x3 or p3.y() != y3:
      print " Failure: should give (%d,%d)." % ( x3, y3 )
    else:
      print " Good."

  # A few tests from X9.62 B.3:
  d = Domain(p=23, m=1, a=1, b=1)
  c = d.curve#CurveFp( 23, 1, 1 )
  test_add( d, 3, 10, 9, 7, 17, 20 )
  test_double( d, 3, 10, 7, 12 )
  test_add( d, 3, 10, 3, 10, 7, 12 )	# (Should just invoke double.)
  test_multiply( d, 3, 10, 2, 7, 12 )

  # From X9.62 I.1 (p. 96):

  g = Point( d, 13, 7 )

  check = INFINITY
  for i in range( 7 + 1 ):
    p = ( i % 7 ) * g
    print "%s * %d = %s, expected %s . . ." % ( g, i, p, check ),
    if p == check:
      print " Good."
    else:
      print " Bad."
    check = check + g

  # NIST Curve P-192:
  p = 6277101735386680763835789423207666416083908700390324961279L
  r = 6277101735386680763835789423176059013767194773182842284081L
  s = 0x3045ae6fc8422f64ed579528d38120eae12196d5L
  c = 0x3099d2bbbfcb2538542dcd5fb078b6ef5f3d6fe2c745de65L
  b = 0x64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1L
  Gx = 0x188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012L
  Gy = 0x07192b95ffc8da78631011ed6b24cdd573f977a11e794811L
  d192 = Domain(p=p,m=1,a=-3,b=b,gx=Gx,gy=Gy,r=r,k=1,length=192/8)

  c192 = d192.curve#CurveFp( p, -3, b )
  p192 = Point( d192, Gx, Gy, )

  # Checking against some sample computations presented
  # in X9.62:

  d = 651056770906015076056810763456358567190100156695615665659L
  Q = d * p192
  if Q.x() != 0x62B12D60690CDCF330BABAB6E69763B471F994DD702D16A5L:
    print "p192 * d came out wrong."
  else:
    print "p192 * d came out right."

  k = 6140507067065001063065065565667405560006161556565665656654L
  R = k * p192
  if R.x() != 0x885052380FF147B734C330C43D39B2C4A89F29B0F749FEADL \
     or R.y() != 0x9CF9FA1CBEFEFB917747A3BB29C072B9289C2547884FD835L:
    print "k * p192 came out wrong."
  else:
    print "k * p192 came out right."

  u1 = 2563697409189434185194736134579731015366492496392189760599L
  u2 = 6266643813348617967186477710235785849136406323338782220568L
  temp = u1 * p192 + u2 * Q
  if temp.x() != 0x885052380FF147B734C330C43D39B2C4A89F29B0F749FEADL \
     or temp.y() != 0x9CF9FA1CBEFEFB917747A3BB29C072B9289C2547884FD835L:
    print "u1 * p192 + u2 * Q came out wrong."
  else:
    print "u1 * p192 + u2 * Q came out right."
