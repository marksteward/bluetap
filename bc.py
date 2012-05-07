#!/usr/bin/env python
from struct import pack, unpack, unpack_from
from contextlib import contextmanager

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

  def read(self, addr, length):
    args = pack('<HHH', addr, length, 0)
    resp = self.bccmd.get(CSR_VARID_MEMORY, args + '\0' * length * 2)
    _addr, _length, reserved = unpack_from('<HHH', resp)
    if _addr != addr:
      raise IOError('Unexpected addr 0x%x (0x%x)' % (_addr, addr))
    elif _length != length:
      raise IOError('Unexpected length 0x%x (0x%x)' % (_length, length))
    return resp[6:]

  def write(self, addr, data):
    if len(data) % 2:
      raise ValueError('Data length not word-aligned')

    args = pack('<HHH', addr, len(data) / 2, 0)
    self.bccmd.put(CSR_VARID_MEMORY, args + data)

  def get_flashpage(self):
    page, = unpack('<H', self.read(CSR_FLASHPAGE, 1))
    return page

  def set_flashpage(self, page):
    self.write(CSR_FLASHPAGE, pack('<H', page))

  @contextmanager
  def flashpage(self, page):
    oldpage = self.get_flashpage()
    self.set_flashpage(page)
    yield oldpage
    self.set_flashpage(oldpage)


def test_bc(bc):

  print hex(bc.rand())
  print hex(bc.rand())
  print hex(bc.clock())
  print hex(bc.clock())
  print hex(bc.clock())
  print hex(bc.clock())
  bc.warm_reset()

def test_read(bc):
  print hci.hexdump(bc.read(0x0, 0x60))
  print
  print hci.hexdump(bc.read(0x20, 0x60))
  print
  print hci.hexdump(bc.read(0x100, 0x10))
  print
  #while True:
  #  print hci.hexdump(bc.read(0x100, 0x10))

def test_flash(bc):
  with bc.flashpage(0):
    print hci.hexdump(bc.read(0x8000, 0x40))
  print
  with bc.flashpage(0x40):
    print hci.hexdump(bc.read(0x8000, 0x40))

def dump_flash(bc):
  oldpage = bc.get_flashpage()
  for page in range(0x40):
    bc.set_flashpage(page)
    for i in range(0x8000, 0x9000, 0x40 * 2):
      sys.stdout.write(bc.read(i, 0x40))

  bc.set_flashpage(oldpage)

if __name__ == '__main__':
  import sys
  import hci
  from optparse import OptionParser

  handlers = [
    'coldreset', Bluecore.cold_reset,
    'warmreset', Bluecore.warm_reset,
    'test',      test_bc,
    'testread',  test_read,
    'testflash', test_flash,
    'dumpflash', dump_flash,
  ]

  usage = 'usage: %prog [options] command\n\nCommands:\n'
  usage += '\n  '.join([''] + handlers[::2])

  opt = OptionParser(usage)
  opt.add_option('-i', '--device', dest='dev', help='HCI device')
  (opts, args) = opt.parse_args()

  if len(args) < 1:
    opt.error('command required')
  try:
    handler = dict(zip(*[iter(handlers)] * 2))[args[0]]
  except KeyError:
    opt.error('invalid command')

  s = hci.open_dev(opts.dev)

  bc = Bluecore(Bccmd(s))

  handler(bc, *args[1:])


