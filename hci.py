#!/usr/bin/env python
from bluetooth._bluetooth import *

def hexdump(d):
  return '\n'.join(
    ' '.join('%02x' % ord(c) for c in d[i:i+16])
      for i in range(0, len(d), 16) )

def get_dev(addr=''):
  if addr:
    id = hci_devid(addr)
  else:
    id = hci_devid()
  return id

def open_dev(addr=''):
  return hci_open_dev(get_dev(addr=addr))

class hci_filter(object):
  def __init__(self, sock, flt=None):
    self.sock = sock
    if flt:
      self.flt = flt
    else:
      self.flt = hci_filter_new()
      hci_filter_all_ptypes(self.flt)
      hci_filter_all_events(self.flt)

  def __enter__(self):
    self.oldflt = self.sock.getsockopt(SOL_HCI, HCI_FILTER, len(self.flt))
    self.sock.setsockopt(SOL_HCI, HCI_FILTER, self.flt)

    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.sock.setsockopt(SOL_HCI, HCI_FILTER, self.oldflt)


def test_bdaddr(s):

  with hci_filter(s):

    hci_send_cmd(s, OGF_INFO_PARAM, OCF_READ_BD_ADDR)
    d = s.recv(255)
    print 'bdaddr:', hexdump(d)


if __name__ == '__main__':
  import sys

  s = open_dev(*sys.argv[1:])
  #s.setsockopt(SOL_HCI, HCI_DATA_DIR, 1)
  #s.setsockopt(SOL_HCI, HCI_TIME_STAMP, 1)

  #hci_send_cmd(s, OGF_HOST_CTL, OCF_READ_INQUIRY_MODE)

  test_bdaddr(s)

