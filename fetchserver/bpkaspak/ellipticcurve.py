#! /usr/bin/env python
#
# Implementation of elliptic curves, for cryptographic applications.
#
# This module doesn't provide any way to choose a random elliptic
# curve, nor to verify that an elliptic curve was chosen randomly,
# because one can simply use NIST's standard curves.
#
# Notes from X9.62-1998 (draft):
#   Nomenclature:
#     - Q is a public key.
#     The "Elliptic Curve Domain Parameters" include:
#     - q is the "field size", which in our case equals p.
#     - p is a big prime.
#     - G is a point of prime order (5.1.1.1).
#     - n is the order of G (5.1.1.1).
#   Public-key validation (5.2.2):
#     - Verify that Q is not the point at infinity.
#     - Verify that X_Q and Y_Q are in [0,p-1].
#     - Verify that Q is on the curve.
#     - Verify that nQ is the point at infinity.
#   Signature generation (5.3):
#     - Pick random k from [1,n-1].
#   Signature checking (5.4.2):
#     - Verify that r and s are in [1,n-1].
#
# Version of 2008.11.25.
#
# Revision history:
#    2005.12.31 - Initial version.
#    2008.11.25 - Change CurveFp.is_on to contains_point.
#
# Written in 2005 by Peter Pearson and placed in the public domain.
class Domain:
    def __init__(self, p=None, m=None, a=None, b=None, gx=None, gy=None,
                 r=None, k=None, length=None):
        self.p = p
        self.m = m
        self.q = p ** m
        self.a = a
        self.b = b
        self.r = r
        self.k = k
        self.curve = CurveFp(p, a, b)
        if gx and gy:
            self.g = Point(self, gx, gy)
        self.len = length
        
    


def inverse_mod(a, p):
    '''
    The multiplicitive inverse of a in the integers modulo p.
    Return b s.t.
    a * b == 1 mod p
    '''
    
    r = a
    d = 1
    count = 0L
    while count < p:
        count += 1
        d = ((p // r + 1) * d) % p
        r = (d * a) % p
        if r == 1:
            break
    else:
        raise ValueError('%d has no inverse mod %d' % (a, p))
    return d


class CurveFp( object ):
  """Elliptic Curve over the field of integers modulo a prime."""
  def __init__( self, p, a, b ):
    """The curve of points satisfying y^2 = x^3 + a*x + b (mod p)."""
    self.__p = p
    self.__a = a
    self.__b = b

  def p( self ):
    return self.__p

  def a( self ):
    return self.__a

  def b( self ):
    return self.__b

  def contains_point( self, x, y ):
    """Is the point (x,y) on this curve?"""
    return ( y * y - ( x * x * x + self.__a * x + self.__b ) ) % self.__p == 0



class Point( object ):
  """A point on an elliptic curve. Altering x and y is forbidding,
     but they can be read by the x() and y() methods."""
  def __init__( self, domain, x, y ):
    """curve, x, y, order; order (optional) is the order of this point."""
    self.__domain = domain
    if domain:
        self.__curve = domain.curve
        self.__order = domain.r
    else:
        self.__curve = None
        self.__order = None
    self.__x = x
    self.__y = y
    # self.curve is allowed to be None only for INFINITY:
    if self.__curve: assert self.__curve.contains_point( x, y )
    if self.__order: assert self * self.__order == INFINITY
 
  def __cmp__( self, other ):
    """Return 0 if the points are identical, 1 otherwise."""
    if self.__curve == other.__curve \
       and self.__x == other.__x \
       and self.__y == other.__y:
      return 0
    else:
      return 1

  def __add__( self, other ):
    """Add one point to another point."""
    
    # X9.62 B.3:

    if other == INFINITY: return self
    if self == INFINITY: return other
    assert self.__curve == other.__curve
    if self.__x == other.__x:
      if ( self.__y + other.__y ) % self.__curve.p() == 0:
        return INFINITY
      else:
        return self.double()

    p = self.__curve.p()

    l = ( ( other.__y - self.__y ) * \
          inverse_mod( other.__x - self.__x, p ) ) % p

    x3 = ( l * l - self.__x - other.__x ) % p
    y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
    
    return Point( self.__domain, x3, y3 )

  def __mul__( self, other ):
    """Multiply a point by an integer."""

    def leftmost_bit( x ):
      assert x > 0
      result = 1L
      while result <= x: result = 2 * result
      return result / 2

    e = other
    if self.__order: e = e % self.__order
    if e == 0: return INFINITY
    if self == INFINITY: return INFINITY
    assert e > 0

    # From X9.62 D.3.2:

    e3 = 3 * e
    negative_self = Point( self.__domain, self.__x, -self.__y )
    i = leftmost_bit( e3 ) / 2
    result = self
    # print "Multiplying %s by %d (e3 = %d):" % ( self, other, e3 )
    while i > 1:
      result = result.double()
      if ( e3 & i ) != 0 and ( e & i ) == 0: result = result + self
      if ( e3 & i ) == 0 and ( e & i ) != 0: result = result + negative_self
      # print ". . . i = %d, result = %s" % ( i, result )
      i = i / 2

    return result

  def __rmul__( self, other ):
    """Multiply a point by an integer."""
    
    return self * other

  def __str__( self ):
    if self == INFINITY: return "infinity"
    return "(%d,%d)" % ( self.__x, self.__y )

  def double( self ):
    """Return a new point that is twice the old."""

    # X9.62 B.3:

    p = self.__curve.p()
    a = self.__curve.a()

    l = ( ( 3 * self.__x * self.__x + a ) * \
          inverse_mod( 2 * self.__y, p ) ) % p

    x3 = ( l * l - 2 * self.__x ) % p
    y3 = ( l * ( self.__x - x3 ) - self.__y ) % p
    
    return Point( self.__domain, x3, y3 )

  def x( self ):
    return self.__x

  def y( self ):
    return self.__y

  def curve( self ):
    return self.__curve
  
  def order( self ):
    return self.__order


# This one point is the Point At Infinity for all purposes:
INFINITY = Point( None, None, None )  

