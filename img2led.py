import logging
import socket
import time

from PIL import Image, ImageOps
import numpy as np

DISPLAY_SIZE = (16, 32)
PANEL_SIZE = (16, 16)
#DISPLAY_LAYOUT = ((0, 2), (1, 3))
DISPLAY_LAYOUT = ((0,), (1,))
UDP_IP_ADDRESS = "192.168.1.122"
UDP_PORT_NO = 21324
SLEEP_MS = 15

logging.basicConfig(level=logging.DEBUG)

im = Image.open("input.png").convert('RGB')

im = ImageOps.invert(im)

logging.debug(f"opened input file 'input.png' ({im.format}, {im.size}, {im.mode})")
#im.show()

re_im = im.resize(DISPLAY_SIZE, resample=Image.Resampling.BOX)

logging.debug(f"resized image to ({re_im.format}, {re_im.size}, {re_im.mode})")

#re_im.show()

th_im = im.copy()
th_im.thumbnail(DISPLAY_SIZE, resample=Image.Resampling.BOX)

logging.debug(f"thumbnailed image to ({th_im.format}, {th_im.size}, {th_im.mode})")

#th_im.show()

my_im_npa = np.asarray(re_im) # could be th_im as well
assert my_im_npa.size / 3 == DISPLAY_SIZE[0] * DISPLAY_SIZE[1]
my_im_npa.shape

packets = []

# 4 is the packet type (DNRGB)
# 255 is not to return to the prior setting after a delay
# another number (n) would be to return after n seconds
packet_base = [4, 10]

# row by row through the panels
for panel_idx, panel_x in enumerate(DISPLAY_LAYOUT):
    for panel_idy, panel_y in enumerate(panel_x):
        # let's go through this panel row by row
        logging.debug(f"panel: {(DISPLAY_LAYOUT[panel_idx][panel_idy])}")
        # send one packet per row with size[1] per packet
        for row_i in range(PANEL_SIZE[1]):
            pidxs = panel_idx * PANEL_SIZE[0]
            pidys = panel_idy * PANEL_SIZE[1]
            #logging.debug(Ipanel_idx, panel_idy)
            # the panels go left to right in even rows
            # and right to left in odd rows
            #row_data = my_im_npa[pidys+row_i, pidxs:pidxs+PANEL_SIZE[0], :]
            row_data = my_im_npa[pidxs:pidxs+PANEL_SIZE[0], pidys+row_i, :]
            if row_i % 2 != 0:
                # reverse the first axis
                row_data = np.flip(row_data, 0)
            row_data = list(np.clip(row_data.flatten(), 0, 255))
            # let's build the packet
            packet = packet_base.copy()
            # calculate the index
            # index = (panel*panel_size) + row*row_size
            index = (DISPLAY_LAYOUT[panel_idx][panel_idy] * \
                        (PANEL_SIZE[0] * PANEL_SIZE[1])) + \
                        row_i * PANEL_SIZE[0]
            # add the low byte and high byte
            itb = index.to_bytes(2, 'big')
            packet.append(itb[0])
            packet.append(itb[1])
            packet.extend(row_data)
            #print(packet)
            packets.append(bytearray(packet))

logging.debug(packets[0])
logging.debug(packets[len(packets)-1])

clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

start_time = time.time()
for packet in packets:
    clientSock.sendto(packet, (UDP_IP_ADDRESS, UDP_PORT_NO))
    time.sleep(SLEEP_MS/1000)
rtt = time.time() - start_time
logging.info(f"took {rtt} seconds to send the frame of {len(packets)} packets")

