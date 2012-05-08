from struct import pack, unpack

class Registers(object):
  regs = dict(
    flashpage = 0x73,
    chipinfo = 0xff9a,
  )

  def __init__(self, bc):
    object.__setattr__(self, 'bc', bc)

  def __setattr__(self, name, val):
    if name.startswith('_'):
      addr = self.regs[name[1:]]
      self.bc.bccmd.write(addr, pack('<H', val))
      return

    self.bc.cache.writeint(self.regs[name], val)

  def __getattr__(self, name):
    if name.startswith('_'):
      addr = self.regs[name[1:]]
      val, = unpack('<H', self.bc.bccmd.read(addr, 1))
      return val

    if name in self.regs:
      return self.bc.cache.readint(self.regs[name])
    raise AttributeError('Unknown register %s' % name)


