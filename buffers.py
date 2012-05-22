from struct import pack, unpack
from bccmd import hexdump

class Buffer(object):
  def __init__(self, bc, num):
    self.bc = bc
    self.num = num
    self.readpde()

  def readpde(self):
    pde = self.bc.cache.read(0xa000 + self.num * 2, 2)
    desc, pointer = unpack('<HH', pde)
    if desc == 0xffff:
      self.locked = True
      self.magnitude = None
      self.numpages = None
      self.pt = None
    else:
      self.locked = False
      self.magnitude, self.pt = divmod(desc, 0x2000)
      self.pt = 0xa000 + self.pt * 2
      self.numpages = 1 * 2 << self.magnitude
    self.pointer = pointer


class Buffers(object):
  def __init__(self, bc):
    self.bc = bc
    self.numpdes = None

  def __len__(self):
    if self.numpdes is None:
      pdend = self.bc.regs.pdend
      self.numpdes = (pdend - 0xa000) / 2
    return self.numpdes

  def __getitem__(self, num):
    num = int(num)

    if num < 0:
      num = len(self) + num + 1

    if num > len(self):
      raise IndexError

    return Buffer(self.bc, num)
