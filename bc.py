#!/usr/bin/env python
from struct import unpack_from

from bccmd import Bccmd
from csr_const import *

class Bluecore(object):
  def __init__(self, bccmd):
    self.bccmd = bccmd

  def rand(self):
    resp = self.bccmd.get(CSR_VARID_RAND, '')
    rand, = unpack_from('<H', resp)
    return rand

  def clock(self):
    resp = self.bccmd.get(CSR_VARID_BT_CLOCK, '')
    high, low = unpack_from('<HH', resp)
    return low + high * 0x10000

  def warm_reset(self):
    self.bccmd.put(CSR_VARID_WARM_RESET, '')

  def warm_halt(self):
    self.bccmd.put(CSR_VARID_WARM_HALT, '')

  def cold_reset(self):
    self.bccmd.put(CSR_VARID_COLD_RESET, '')

  def cold_halt(self):
    self.bccmd.put(CSR_VARID_COLD_HALT, '')


def test_bc(bc):

  print hex(bc.rand())
  print hex(bc.rand())
  print hex(bc.clock())
  print hex(bc.clock())
  print hex(bc.clock())
  print hex(bc.clock())
  bc.warm_reset()


if __name__ == '__main__':
  import sys
  import hci

  s = hci.open_dev(*sys.argv[1:])

  bc = Bluecore(Bccmd(s))
  test_bc(bc)

