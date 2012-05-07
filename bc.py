#!/usr/bin/env python
from contextlib import contextmanager

from bccmd import Bccmd, BccmdHCI
from cache import CachedRAM
from regs import Registers


class Bluecore(object):
  def __init__(self, bccmd):
    self.bccmd = bccmd
    self.cache = CachedRAM(bccmd)
    self.regs = Registers(self)

  def is_flash(self):
    return self.regs.chipinfo & 0x4000

  @contextmanager
  def flashpage(self, page):
    oldpage = self.regs.flashpage
    self.regs.flashpage = page
    yield oldpage
    self.regs.flashpage = oldpage



def test_flash(bc):
  with bc.flashpage(0):
    print hci.hexdump(bc.bccmd.read(0x8000, 0x40))
  print
  with bc.flashpage(0x40):
    print hci.hexdump(bc.bccmd.read(0x8000, 0x40))

def dump_flash(bc):
  oldpage = bc.regs.flashpage
  for page in range(0x40):
    bc.regs.flashpage = page
    for i in range(0x8000, 0x9000, 0x40 * 2):
      sys.stdout.write(bc.bccmd.read(i, 0x40))

  bc.regs.flashpage = oldpage


if __name__ == '__main__':
  import sys
  import hci
  from optparse import OptionParser

  handlers = [
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

  bc = Bluecore(Bccmd(BccmdHCI(s)))

  handler(bc, *args[1:])


