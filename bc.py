#!/usr/bin/env python
from contextlib import contextmanager

from bccmd import Bccmd, BccmdHCI, hexdump
from cache import CachedRAM
from regs import Registers
from buffers import Buffers


class Bluecore(object):
  def __init__(self, bccmd):
    self.bccmd = bccmd
    self.cache = CachedRAM(bccmd)
    self.regs = Registers(self)
    self.buffers = Buffers(self)

  def is_flash(self):
    return bool(self.regs.chipinfo & 0x4000)

  @contextmanager
  def flashpage(self, page):
    oldpage = self.regs.flashpage
    self.regs.flashpage = page
    yield oldpage
    self.regs.flashpage = oldpage

  @contextmanager
  def sampler(self, addr):
    # TODO: this should perhaps be a couple of helpers in regs.py
    if 0xff80 <= addr <= 0xffff:
      addr -= 0xff00
    if not 0 <= addr <= 0xff:
      raise ValueError('Address %04x does not fit into a byte' % addr)
    oldreg = self.regs.sampler
    oldunknown, oldaddr = divmod(oldreg, 0x100)
    self.regs.sampler = oldunknown * 0x100 + (addr & 0xff)
    if 0x80 <= oldaddr <= 0xff:
      oldaddr += 0xff00
    yield oldaddr
    self.regs.sampler = oldreg


def test_flash(bc):
  print bc.is_flash()
  with bc.flashpage(0):
    print bc.regs.flashpage,
    bc.regs._flashpage = 0x3f
    print bc.regs.flashpage, bc.regs._flashpage
    bc.regs._flashpage = 0
    print
    print hexdump(bc.bccmd.read(0x8000, 0x40))
  print
  with bc.flashpage(0x40):
    print hexdump(bc.bccmd.read(0x8000, 0x40))


def test_sampler(bc):
  with bc.sampler(bc.regs['clock'].low):
    print hex(bc.regs._clock)
    print hexdump(bc.bccmd.read(0x9000, 0x20))
    print hexdump(bc.bccmd.read(0x9000, 0x20))
    print hex(bc.regs._clock)


def list_buffers(bc):
  print 'buffer1: %02x' % bc.regs._buffer1
  print 'buffer2: %02x' % bc.regs._buffer2
  for i, buf in enumerate(bc.buffers):
    if buf.locked:
      print '%02x (locked)>' % i
    else:
      print '%02x (%04x for %02x words): %04x' % (
        i, buf.pt, buf.numpages / 2, buf.pointer)


def dump_flash(bc):
  oldpage = bc.regs.flashpage
  for page in range(0x40):
    bc.regs.flashpage = page
    for i in range(0x8000, 0x9000, 0x40):
      sys.stdout.write(bc.bccmd.read(i, 0x40))

  bc.regs.flashpage = oldpage


def read_memory(bc, addr, size):
  print hexdump(bc.bccmd.read(int(addr, 0), int(size, 0)))


if __name__ == '__main__':
  import sys
  import hci
  from optparse import OptionParser

  handlers = [
    'testflash', test_flash,
    'testsampler', test_sampler,
    'dumpflash', dump_flash,
    'buffers', list_buffers,
    'read', read_memory,
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

  bc = Bluecore(Bccmd(BccmdHCI(s)))

  handler(bc, *args[1:])


