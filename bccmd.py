from struct import pack, unpack_from

from bluetooth._bluetooth import \
  hci_send_req, \
  hci_open_dev, \
  OGF_VENDOR_CMD, \
  EVT_VENDOR

from csr_const import *

def hexdump(d):
  def lines(d):
    for i in range(0, len(d), 32):
      l = d[i:i+32]
      ws = unpack_from('<' + 'H' * (len(l) / 2), l)
      yield ' '.join('%04x' % w for w in ws)
  return '\n'.join(lines(d))

class BccmdTransport(object):
  pass

class BccmdHCI(BccmdTransport):
  def __init__(self, sock, timeout=2000):
    self.sock = sock
    self.seqnum = 0
    self.timeout = timeout

  def get(self, varid, value):
    return self.hci_cmd(0x0000, varid, value)

  def put(self, varid, value):
    return self.hci_cmd(0x0002, varid, value)

  def hci_cmd(self, command, varid, value):
    # cmd length in words
    size = 5 + max(4, (len(value) + 1) / 2)

    cmd = pack('<HHHHH', command, size, self.seqnum, varid, 0) + value
    pkt = pack('B', 0xc2) + cmd

    #hci_send_cmd(self.sock, OGF_VENDOR_CMD, 0, pkt)
    resp = hci_send_req(self.sock, OGF_VENDOR_CMD, 0, EVT_VENDOR, 256, pkt, self.timeout)

    proto, cmd, size, seqnum, varidresp, reserved = unpack_from('<BHHHHH', resp)
    if proto != 0xc2:
      raise IOError('Unexpected protocol: 0x%x (0xc2)' % proto)
    elif cmd != 1:
      raise IOError('Unexpected command: %d (1)' % cmd)
    elif reserved != 0:
      raise IOError('Unexpected reserved: %d (0)' % reserved)
    elif varidresp != varid:
      raise IOError('Unexpected varid: 0x%x (0x%x)' % (varidresp, varid))
    elif seqnum != self.seqnum:
      raise IOError('Unexpected seqnum: %s (%s)' % (seqnum, self.seqnum))

    self.seqnum += 1
    return resp[11:size * 2 + 1]


class Bccmd(object):
  def __init__(self, transport):
    self.transport = transport

  def rand(self):
    resp = self.transport.get(CSR_VARID_RAND, '')
    rand, = unpack_from('<H', resp)
    return rand

  def clock(self):
    resp = self.transport.get(CSR_VARID_BT_CLOCK, '')
    high, low = unpack_from('<HH', resp)
    return low + high * 0x10000

  def warm_reset(self):
    self.transport.put(CSR_VARID_WARM_RESET, '')

  def warm_halt(self):
    self.transport.put(CSR_VARID_WARM_HALT, '')

  def cold_reset(self):
    self.transport.put(CSR_VARID_COLD_RESET, '')

  def cold_halt(self):
    self.transport.put(CSR_VARID_COLD_HALT, '')

  def read(self, addr, length):
    args = pack('<HHH', addr, length, 0)
    resp = self.transport.get(CSR_VARID_MEMORY, args + '\0' * length * 2)
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
    self.transport.put(CSR_VARID_MEMORY, args + data)



if __name__ == '__main__':
  import sys
  import hci

  s = hci.open_dev(*sys.argv[1:])
  bccmd = Bccmd(BccmdHCI(s))

  print hex(bccmd.rand())
  print hex(bccmd.rand())
  print hex(bccmd.clock())
  print hex(bccmd.clock())
  print hex(bccmd.clock())
  print hex(bccmd.clock())
  print hexdump(bccmd.read(0xff97, 2))
  print hexdump(bccmd.read(0xff9a, 2))
  #bccmd.warm_reset()

