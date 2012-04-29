#!/usr/bin/env python
from struct import pack, unpack_from

from bluetooth._bluetooth import \
  hci_send_req, \
  hci_open_dev, \
  OGF_VENDOR_CMD, \
  EVT_VENDOR


class Bccmd(object):
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


