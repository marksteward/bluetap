from struct import pack, unpack
from bccmd import hexdump

class CachedRAM(object):
  def __init__(self, bccmd, linesize=0x20):
    self.bccmd = bccmd
    self.cache = {}
    self.linesize = linesize

  def read(self, addr, length):
    lines = ''
    linestart = addr / self.linesize * self.linesize

    for a in range(linestart, addr + length, self.linesize):
      line = a / self.linesize

      if line not in self.cache:
        self.cache[line] = self.bccmd.read(line * self.linesize, self.linesize)

      lines += self.cache[line]

    return lines[(addr % self.linesize) * 2:(addr % self.linesize + length) * 2]

  def evict(self, addr, length):
    linestart = addr / self.linesize * self.linesize

    for a in range(linestart, addr + length, self.linesize):
      if a / self.linesize in self.cache:
        del self.cache[a / self.linesize]

  def write(self, addr, data):
    for a in range(addr, addr + len(data) / 2, self.linesize):
      self.bccmd.write(addr, data)

    self.evict(addr, len(data) / 2)

  def readint(self, addr):
    val, = unpack('<H', self.read(addr, 1))
    return val

  def writeint(self, addr, val):
    self.write(addr, pack('<H', val))


if __name__ == '__main__':
  import sys
  import time
  import hci
  from bccmd import Bccmd, BccmdHCI

  s = hci.open_dev(*sys.argv[1:])
  bccmd = Bccmd(BccmdHCI(s))
  cache = CachedRAM(bccmd)

  print hexdump(bccmd.read(0xffb0, 0x10))
  print
  print hexdump(bccmd.read(0xffb4, 0x2))
  time.sleep(0.1)
  print hexdump(bccmd.read(0xffb4, 0x2))
  print
  print hexdump(cache.read(0xffb0, 0x10))
  print
  print hexdump(cache.read(0xffb4, 0x2))
  time.sleep(0.1)
  print hexdump(cache.read(0xffb4, 0x2))
  print
  print hexdump(cache.read(0x100, 0x10))
  print
  while True:
    print hexdump(bccmd.read(0x67, 0x40))
    print
    time.sleep(0.1)

