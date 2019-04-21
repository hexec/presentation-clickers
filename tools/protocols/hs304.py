from protocol import Protocol
from lib import common
import crcmod
import logging
import struct
import time


# HS304 keyboard/mouse transceiver
class HS304(Protocol):

  # Constructor
  def __init__(self):
    super(HS304, self).__init__("HS304")

    self.CRC16 = crcmod.mkCrcFun(0x11021, initCrc=0x422e, rev=False, xorOut=0x0000)
    self.CRC8 = crcmod.mkCrcFun(0x101, initCrc=0x1d, rev=False, xorOut=0x00)

    # Lookup table for payload byte 0 (Keyboard HID byte 2)
    self.LUT0 = [[0xa1, 0x21, 0xe1, 0x61, 0x81, 0x01, 0xc1, 0x41, 0xb1, 0x31, 0xf1, 0x71, 0x91, 0x11, 0xd1, 0x51, 0xa9, 0x29, 0xe9, 0x69, 0x89, 0x09, 0xc9, 0x49, 0xb9, 0x39, 0xf9, 0x79, 0x99, 0x19, 0xd9, 0x59, 0xa5, 0x25, 0xe5, 0x65, 0x85, 0x05, 0xc5, 0x45, 0xb5, 0x35, 0xf5, 0x75, 0x95, 0x15, 0xd5, 0x55, 0xad, 0x2d, 0xed, 0x6d, 0x8d, 0x0d, 0xcd, 0x4d, 0xbd, 0x3d, 0xfd, 0x7d, 0x9d, 0x1d, 0xdd, 0x5d, 0xa3, 0x23, 0xe3, 0x63, 0x83, 0x03, 0xc3, 0x43, 0xb3, 0x33, 0xf3, 0x73, 0x93, 0x13, 0xd3, 0x53, 0xab, 0x2b, 0xeb, 0x6b, 0x8b, 0x0b, 0xcb, 0x4b, 0xbb, 0x3b, 0xfb, 0x7b, 0x9b, 0x1b, 0xdb, 0x5b, 0xa7, 0x27, 0xe7, 0x67, 0x87, 0x07, 0xc7, 0x47, 0xb7, 0x37, 0xf7, 0x77, 0x97, 0x17, 0xd7, 0x57, 0xaf, 0x2f, 0xef, 0x6f, 0x8f, 0x0f, 0xcf, 0x4f, 0xbf, 0x3f, 0xff, 0x7f, 0x9f, 0x1f, 0xdf, 0x5f, 0xa0, 0x20, 0xe0, 0x60, 0x80, 0x00, 0xc0, 0x40, 0xb0, 0x30, 0xf0, 0x70, 0x90, 0x10, 0xd0, 0x50, 0xa8, 0x28, 0xe8, 0x68, 0x88, 0x08, 0xc8, 0x48, 0xb8, 0x38, 0xf8, 0x78, 0x98, 0x18, 0xd8, 0x58, 0xa4, 0x24, 0xe4, 0x64, 0x84, 0x04, 0xc4, 0x44, 0xb4, 0x34, 0xf4, 0x74, 0x94, 0x14, 0xd4, 0x54, 0xac, 0x2c, 0xec, 0x6c, 0x8c, 0x0c, 0xcc, 0x4c, 0xbc, 0x3c, 0xfc, 0x7c, 0x9c, 0x1c, 0xdc, 0x5c, 0xa2, 0x22, 0xe2, 0x62, 0x82, 0x02, 0xc2, 0x42, 0xb2, 0x32, 0xf2, 0x72, 0x92, 0x12, 0xd2, 0x52, 0xaa, 0x2a, 0xea, 0x6a, 0x8a, 0x0a, 0xca, 0x4a, 0xba, 0x3a, 0xfa, 0x7a, 0x9a, 0x1a, 0xda, 0x5a, 0xa6, 0x26, 0xe6, 0x66, 0x86, 0x06, 0xc6, 0x46, 0xb6, 0x36, 0xf6, 0x76, 0x96, 0x16, 0xd6, 0x56, 0xae, 0x2e, 0xee, 0x6e, 0x8e, 0x0e, 0xce, 0x4e, 0xbe, 0x3e, 0xfe, 0x7e, 0x9e, 0x1e, 0xde, 0x5e].index(x) for x in range(256)]

    # Lookup table for payload byte 3 (Mouse HID byte 0)
    self.LUT3 = [[0x66, 0xe6, 0x26, 0xa6, 0x46, 0xc6, 0x06, 0x86, 0x76, 0xf6, 0x36, 0xb6, 0x56, 0xd6, 0x16, 0x96, 0x6e, 0xee, 0x2e, 0xae, 0x4e, 0xce, 0x0e, 0x8e, 0x7e, 0xfe, 0x3e, 0xbe, 0x5e, 0xde, 0x1e, 0x9e, 0x62, 0xe2, 0x22, 0xa2, 0x42, 0xc2, 0x02, 0x82, 0x72, 0xf2, 0x32, 0xb2, 0x52, 0xd2, 0x12, 0x92, 0x6a, 0xea, 0x2a, 0xaa, 0x4a, 0xca, 0x0a, 0x8a, 0x7a, 0xfa, 0x3a, 0xba, 0x5a, 0xda, 0x1a, 0x9a, 0x64, 0xe4, 0x24, 0xa4, 0x44, 0xc4, 0x04, 0x84, 0x74, 0xf4, 0x34, 0xb4, 0x54, 0xd4, 0x14, 0x94, 0x6c, 0xec, 0x2c, 0xac, 0x4c, 0xcc, 0x0c, 0x8c, 0x7c, 0xfc, 0x3c, 0xbc, 0x5c, 0xdc, 0x1c, 0x9c, 0x60, 0xe0, 0x20, 0xa0, 0x40, 0xc0, 0x00, 0x80, 0x70, 0xf0, 0x30, 0xb0, 0x50, 0xd0, 0x10, 0x90, 0x68, 0xe8, 0x28, 0xa8, 0x48, 0xc8, 0x08, 0x88, 0x78, 0xf8, 0x38, 0xb8, 0x58, 0xd8, 0x18, 0x98, 0x67, 0xe7, 0x27, 0xa7, 0x47, 0xc7, 0x07, 0x87, 0x77, 0xf7, 0x37, 0xb7, 0x57, 0xd7, 0x17, 0x97, 0x6f, 0xef, 0x2f, 0xaf, 0x4f, 0xcf, 0x0f, 0x8f, 0x7f, 0xff, 0x3f, 0xbf, 0x5f, 0xdf, 0x1f, 0x9f, 0x63, 0xe3, 0x23, 0xa3, 0x43, 0xc3, 0x03, 0x83, 0x73, 0xf3, 0x33, 0xb3, 0x53, 0xd3, 0x13, 0x93, 0x6b, 0xeb, 0x2b, 0xab, 0x4b, 0xcb, 0x0b, 0x8b, 0x7b, 0xfb, 0x3b, 0xbb, 0x5b, 0xdb, 0x1b, 0x9b, 0x65, 0xe5, 0x25, 0xa5, 0x45, 0xc5, 0x05, 0x85, 0x75, 0xf5, 0x35, 0xb5, 0x55, 0xd5, 0x15, 0x95, 0x6d, 0xed, 0x2d, 0xad, 0x4d, 0xcd, 0x0d, 0x8d, 0x7d, 0xfd, 0x3d, 0xbd, 0x5d, 0xdd, 0x1d, 0x9d, 0x61, 0xe1, 0x21, 0xa1, 0x41, 0xc1, 0x01, 0x81, 0x71, 0xf1, 0x31, 0xb1, 0x51, 0xd1, 0x11, 0x91, 0x69, 0xe9, 0x29, 0xa9, 0x49, 0xc9, 0x09, 0x89, 0x79, 0xf9, 0x39, 0xb9, 0x59, 0xd9, 0x19, 0x99].index(x) for x in range(256)]

    # Lookup table for payload byte 4 (Mouse HID byte 1)
    self.LUT4 = [[0xb1, 0x31, 0xf1, 0x71, 0x91, 0x11, 0xd1, 0x51, 0xa1, 0x21, 0xe1, 0x61, 0x81, 0x00, 0xc1, 0x41, 0xb9, 0x39, 0xf9, 0x79, 0x99, 0x19, 0xd9, 0x59, 0xa9, 0x29, 0xe9, 0x69, 0x89, 0x09, 0xc9, 0x49, 0xb5, 0x35, 0xf5, 0x75, 0x95, 0x15, 0xd5, 0x55, 0xa5, 0x25, 0xe5, 0x65, 0x85, 0x05, 0xc5, 0x45, 0xbd, 0x3d, 0xfd, 0x7d, 0x9d, 0x1d, 0xdd, 0x5d, 0xad, 0x2d, 0xed, 0x6d, 0x8d, 0x0d, 0xcd, 0x4d, 0xb3, 0x33, 0xf3, 0x73, 0x93, 0x13, 0xd3, 0x53, 0xa3, 0x23, 0xe3, 0x63, 0x83, 0x03, 0xc3, 0x43, 0xbb, 0x3b, 0xfb, 0x7b, 0x9b, 0x1b, 0xdb, 0x5b, 0xab, 0x2b, 0xeb, 0x6b, 0x8b, 0x0b, 0xcb, 0x4b, 0xb7, 0x37, 0xf7, 0x77, 0x97, 0x17, 0xd7, 0x57, 0xa7, 0x27, 0xe7, 0x67, 0x87, 0x07, 0xc7, 0x47, 0xbf, 0x3f, 0xff, 0x7f, 0x9f, 0x1f, 0xdf, 0x5f, 0xaf, 0x2f, 0xef, 0x6f, 0x8f, 0x0f, 0xcf, 0x4f, 0xb0, 0x30, 0xf0, 0x70, 0x90, 0x10, 0xd0, 0x50, 0xa0, 0x20, 0xe0, 0x60, 0x80, 0x01, 0xc0, 0x40, 0xb8, 0x38, 0xf8, 0x78, 0x98, 0x18, 0xd8, 0x58, 0xa8, 0x28, 0xe8, 0x68, 0x88, 0x08, 0xc8, 0x48, 0xb4, 0x34, 0xf4, 0x74, 0x94, 0x14, 0xd4, 0x54, 0xa4, 0x24, 0xe4, 0x64, 0x84, 0x04, 0xc4, 0x44, 0xbc, 0x3c, 0xfc, 0x7c, 0x9c, 0x1c, 0xdc, 0x5c, 0xac, 0x2c, 0xec, 0x6c, 0x8c, 0x0c, 0xcc, 0x4c, 0xb2, 0x32, 0xf2, 0x72, 0x92, 0x12, 0xd2, 0x52, 0xa2, 0x22, 0xe2, 0x62, 0x82, 0x02, 0xc2, 0x42, 0xba, 0x3a, 0xfa, 0x7a, 0x9a, 0x1a, 0xda, 0x5a, 0xaa, 0x2a, 0xea, 0x6a, 0x8a, 0x0a, 0xca, 0x4a, 0xb6, 0x36, 0xf6, 0x76, 0x96, 0x16, 0xd6, 0x56, 0xa6, 0x26, 0xe6, 0x66, 0x86, 0x06, 0xc6, 0x46, 0xbe, 0x3e, 0xfe, 0x7e, 0x9e, 0x1e, 0xde, 0x5e, 0xae, 0x2e, 0xee, 0x6e, 0x8e, 0x0e, 0xce, 0x4e].index(x) for x in range(256)]

    # Lookup table for payload byte 5 (Mouse HID byte 2)
    self.LUT5 = [[0x75, 0xf5, 0x35, 0xb5, 0x55, 0xd5, 0x15, 0x95, 0x65, 0xe5, 0x25, 0xa5, 0x45, 0xc5, 0x05, 0x85, 0x7d, 0xfd, 0x3d, 0xbd, 0x5d, 0xdd, 0x1d, 0x9d, 0x6d, 0xed, 0x2d, 0xad, 0x4d, 0xcd, 0x0d, 0x8d, 0x71, 0xf1, 0x31, 0xb1, 0x51, 0xd1, 0x11, 0x91, 0x61, 0xe1, 0x21, 0xa1, 0x41, 0xc1, 0x01, 0x81, 0x79, 0xf9, 0x39, 0xb9, 0x59, 0xd9, 0x19, 0x99, 0x69, 0xe9, 0x29, 0xa9, 0x49, 0xc9, 0x09, 0x89, 0x77, 0xf7, 0x37, 0xb7, 0x57, 0xd7, 0x17, 0x97, 0x67, 0xe7, 0x27, 0xa7, 0x47, 0xc7, 0x07, 0x87, 0x7f, 0xff, 0x3f, 0xbf, 0x5f, 0xdf, 0x1f, 0x9f, 0x6f, 0xef, 0x2f, 0xaf, 0x4f, 0xcf, 0x0f, 0x8f, 0x73, 0xf3, 0x33, 0xb3, 0x53, 0xd3, 0x13, 0x93, 0x63, 0xe3, 0x23, 0xa3, 0x43, 0xc3, 0x03, 0x83, 0x7b, 0xfb, 0x3b, 0xbb, 0x5b, 0xdb, 0x1b, 0x9b, 0x6b, 0xeb, 0x2b, 0xab, 0x4b, 0xcb, 0x0b, 0x8b, 0x74, 0xf4, 0x34, 0xb4, 0x54, 0xd4, 0x14, 0x94, 0x64, 0xe4, 0x24, 0xa4, 0x44, 0xc4, 0x04, 0x84, 0x7c, 0xfc, 0x3c, 0xbc, 0x5c, 0xdc, 0x1c, 0x9c, 0x6c, 0xec, 0x2c, 0xac, 0x4c, 0xcc, 0x0c, 0x8c, 0x70, 0xf0, 0x30, 0xb0, 0x50, 0xd0, 0x10, 0x90, 0x60, 0xe0, 0x20, 0xa0, 0x40, 0xc0, 0x00, 0x80, 0x78, 0xf8, 0x38, 0xb8, 0x58, 0xd8, 0x18, 0x98, 0x68, 0xe8, 0x28, 0xa8, 0x48, 0xc8, 0x08, 0x88, 0x76, 0xf6, 0x36, 0xb6, 0x56, 0xd6, 0x16, 0x96, 0x66, 0xe6, 0x26, 0xa6, 0x46, 0xc6, 0x06, 0x86, 0x7e, 0xfe, 0x3e, 0xbe, 0x5e, 0xde, 0x1e, 0x9e, 0x6e, 0xee, 0x2e, 0xae, 0x4e, 0xce, 0x0e, 0x8e, 0x72, 0xf2, 0x32, 0xb2, 0x52, 0xd2, 0x12, 0x92, 0x62, 0xe2, 0x22, 0xa2, 0x42, 0xc2, 0x02, 0x82, 0x7a, 0xfa, 0x3a, 0xba, 0x5a, 0xda, 0x1a, 0x9a, 0x6a, 0xea, 0x2a, 0xaa, 0x4a, 0xca, 0x0a, 0x8a].index(x) for x in range(256)]

    # Lookup table for payload byte 6 (Keyboard HID byte 1)
    self.LUT6 = [[0x31, 0xb1, 0x71, 0xf1, 0x11, 0x91, 0x51, 0xd1, 0x21, 0xa1, 0x61, 0xe1, 0x01, 0x81, 0x41, 0xc1, 0x39, 0xb9, 0x79, 0xf9, 0x19, 0x99, 0x59, 0xd9, 0x29, 0xa9, 0x69, 0xe9, 0x09, 0x89, 0x49, 0xc9, 0x35, 0xb5, 0x75, 0xf5, 0x15, 0x95, 0x55, 0xd5, 0x25, 0xa5, 0x65, 0xe5, 0x05, 0x85, 0x45, 0xc5, 0x3d, 0xbd, 0x7d, 0xfd, 0x1d, 0x9d, 0x5d, 0xdd, 0x2d, 0xad, 0x6d, 0xed, 0x0d, 0x8d, 0x4d, 0xcd, 0x33, 0xb3, 0x73, 0xf3, 0x13, 0x93, 0x53, 0xd3, 0x23, 0xa3, 0x63, 0xe3, 0x03, 0x83, 0x43, 0xc3, 0x3b, 0xbb, 0x7b, 0xfb, 0x1b, 0x9b, 0x5b, 0xdb, 0x2b, 0xab, 0x6b, 0xeb, 0x0b, 0x8b, 0x4b, 0xcb, 0x37, 0xb7, 0x77, 0xf7, 0x17, 0x97, 0x57, 0xd7, 0x27, 0xa7, 0x67, 0xe7, 0x07, 0x87, 0x47, 0xc7, 0x3f, 0xbf, 0x7f, 0xff, 0x1f, 0x9f, 0x5f, 0xdf, 0x2f, 0xaf, 0x6f, 0xef, 0x0f, 0x8f, 0x4f, 0xcf, 0x30, 0xb0, 0x70, 0xf0, 0x10, 0x90, 0x50, 0xd0, 0x20, 0xa0, 0x60, 0xe0, 0x00, 0x80, 0x40, 0xc0, 0x38, 0xb8, 0x78, 0xf8, 0x18, 0x98, 0x58, 0xd8, 0x28, 0xa8, 0x68, 0xe8, 0x08, 0x88, 0x48, 0xc8, 0x34, 0xb4, 0x74, 0xf4, 0x14, 0x94, 0x54, 0xd4, 0x24, 0xa4, 0x64, 0xe4, 0x04, 0x84, 0x44, 0xc4, 0x3c, 0xbc, 0x7c, 0xfc, 0x1c, 0x9c, 0x5c, 0xdc, 0x2c, 0xac, 0x6c, 0xec, 0x0c, 0x8c, 0x4c, 0xcc, 0x32, 0xb2, 0x72, 0xf2, 0x12, 0x92, 0x52, 0xd2, 0x22, 0xa2, 0x62, 0xe2, 0x02, 0x82, 0x42, 0xc2, 0x3a, 0xba, 0x7a, 0xfa, 0x1a, 0x9a, 0x5a, 0xda, 0x2a, 0xaa, 0x6a, 0xea, 0x0a, 0x8a, 0x4a, 0xca, 0x36, 0xb6, 0x76, 0xf6, 0x16, 0x96, 0x56, 0xd6, 0x26, 0xa6, 0x66, 0xe6, 0x06, 0x86, 0x46, 0xc6, 0x3e, 0xbe, 0x7e, 0xfe, 0x1e, 0x9e, 0x5e, 0xde, 0x2e, 0xae, 0x6e, 0xee, 0x0e, 0x8e, 0x4e, 0xce].index(x) for x in range(256)]


  # Configure the radio
  def configure_radio(self):

    # Put the radio in promiscuous mode
    common.radio.enter_promiscuous_mode_generic("\x44\x75\x94\xE1", rate=common.RF_RATE_1M)

    # Set the channel to 7
    common.channels = [7]

    # Set the initial channel
    common.radio.set_channel(common.channels[0])


  # Send a HID keystroke packet
  def send_hid_event(self, scan_code=0, shift=False, ctrl=False, win=False):

    # Skeleton payload (with two "magic" bytes)
    payload = "\x00\x31\x78\x00\x00\x00\x00\x00"

    # Sync word
    sync = "\x44\x75\x94\xE1"

    # Keystroke modifiers
    modifiers = 0x00
    if shift: modifiers |= 0x20
    if ctrl: modifiers |= 0x01
    if win: modifiers |= 0x08

    # Mouse X/Y and button flags
    mouse_y = 0
    mouse_x = 0
    mouse_b = 0

    # Construct the payload
    payload = chr(self.LUT0[scan_code]) + \
              payload[1:3] + \
              chr(self.LUT3[mouse_b]) + \
              chr(self.LUT4[mouse_x]) + \
              chr(self.LUT5[mouse_y]) + \
              chr(self.LUT6[modifiers])

    # Append CRC-8
    p = sync + payload + chr(self.CRC8(sync+payload))

    # Append CRC-16
    p += struct.pack("!H", self.CRC16(p))

    # Transmit the packet 10x on channel 2407
    for x in range(10):
      common.radio.transmit_payload_generic(address="\x00\x00\x00\x00\x00", 
                                            payload="\xF1\x0F\x55" + p + "\xAF\xFF")
      time.sleep(0.002)


  # Discovery loop
  def discovery_loop(self, cancel):

    while not cancel:

      # Receive payloads
      value = common.radio.receive_payload()
      if value[0] == 0xFF: continue
      if len(value) < 15: continue

      # Verify the CRC
      crc_calc = self.CRC16(value[0:12])
      crc = struct.unpack("!H", value[12:14])[0]
      if crc != crc_calc:
        logging.debug("CRC failure")
        continue

      # Parse the payload
      sync, payload = value[0:4], value[4:]
      code = self.LUT0.index(payload[0])
      mouse_b = self.LUT3.index(payload[3])
      mouse_x = self.LUT4.index(payload[4])
      mouse_y = self.LUT5.index(payload[5])
      modifiers = self.LUT6.index(payload[6])

      # Log the packet
      logging.info("Scan Code: %02x, Modifier: %02x, Mouse Button: %02x, Mouse X: %i, Mouse Y: %i" % (code, mouse_b, mouse_x, mouse_y, modifiers))


  # Enter injection mode
  def start_injection(self):
    return


  # Leave injection mode
  def stop_injection(self):
    return