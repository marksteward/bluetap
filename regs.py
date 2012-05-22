from struct import pack, unpack

class Reg(object):
  def __init__(self, addr):
    self.addr = addr

class Int(Reg):
  size = 1
  def pack(self, val):
    return pack('<H', val)

  def unpack(self, val):
    return unpack('<H', val)

class Long(Reg):
  size = 2
  def pack(self, val):
    val = pack('<L', val)
    return val[2:4] + val[0:2]

  def unpack(self, val):
    return unpack('<L', val[2:4] + val[0:2])

  @property
  def high(self):
    return self.addr

  @property
  def low(self):
    return self.addr + 1


class Registers(object):
  regs = dict(
    buffer1 = Int(0x6e),
    buffer2 = Int(0x6f),
    pdend = Int(0x70),
    flashpage = Int(0x73),
    sampler = Int(0x75),
    chipinfo = Int(0xff9a),
    clock = Long(0xffb4),
  )

  def __init__(self, bc):
    object.__setattr__(self, 'bc', bc)

  def __setattr__(self, name, val):
    try:
      if name.startswith('_'):
        reg = self.regs[name[1:]]
        write = self.bc.bccmd.write
      else:
        reg = self.regs[name]
        write = self.bc.cache.write
    except KeyError:
      raise AttributeError('Unknown register %s' % name)

    write(reg.addr, reg.pack(val))

  def __getattr__(self, name):
    try:
      if name.startswith('_'):
        reg = self.regs[name[1:]]
        read = self.bc.bccmd.read
      else:
        reg = self.regs[name]
        read = self.bc.cache.read
    except KeyError:
      raise AttributeError('Unknown register %s' % name)

    val, = reg.unpack(read(reg.addr, reg.size))
    return val

  def __getitem__(self, name):
    return self.regs[name]

