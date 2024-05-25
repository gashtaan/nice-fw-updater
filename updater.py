# https://github.com/gashtaan/nice-fw-updater
#
# Copyright (C) 2024, Michal Kovacik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import serial
import binascii
import time
import struct

# example of usage:
# updater.py COM3 FG01h.hex

# control unit address/endpoint will be updated when unit responds to communication
# tool address/endpoint is hard-coded to 50/90 (BiDi-WiFi module)
cu_address = 0xFF
cu_endpoint = 0xFF

com = serial.Serial(sys.argv[1], 19200, timeout=2)

# send T4 command to initiate reboot to bootloader, do not check the response in case the control unit is already in there
com.send_break(0.0007)
com.write(b'\x55\x0D\xFF\xFF\x50\x90\x08\x06\xCE\x00\xF0\xA9\x00\x00\x59\x0D')
com.read(500)

def send_packet_checked(data):
	assert send_packet(data)[6] == 0x00, 'Invalid control unit response'

def send_packet(data):
	global com

	hash = (len(data) + 4) ^ cu_address ^ cu_endpoint ^ 0x50 ^ 0x90
	for b in data:
		hash ^= b

	buffer = bytearray()
	buffer.append(0xF0)
	buffer.append(len(data) + 4)
	buffer.append(cu_address)
	buffer.append(cu_endpoint)
	buffer.append(0x50)
	buffer.append(0x90)
	buffer.extend(data)
	buffer.append(hash)

	com.send_break(0.0007)
	com.write(buffer)
	assert read_packet() == buffer, 'Corrupted packet echo'

	return read_packet()

def read_packet():
	global com

	assert com.read()[0] == 0x00, 'Unexpected packet start'

	packet_data = bytearray()
	packet_data.extend(com.read())
	assert packet_data[0] == 0xF0, 'Unexpected packet type'

	packet_data.extend(com.read())
	packet_data.extend(com.read(packet_data[1]))
	packet_data.extend(com.read())

	hash = 0
	for b in packet_data[1:-1]:
		hash ^= b
	assert packet_data[-1] == hash, 'Invalid packet hash'

	return packet_data

with open(sys.argv[2]) as hex:
	hex_checksum1 = int(hex.readline().rstrip())
	hex_marker = hex.readline().rstrip()
	hex_version = hex.readline().rstrip()
	hex_hardware = hex.readline().rstrip()
	hex_checksum2 = int(hex.readline().rstrip())

	assert hex_marker == 'NICE.FIRMWARE', 'Invalid firmware file'

	# recognize the control unit
	response = send_packet(b'\x02')
	cu_address = response[4]
	cu_endpoint = response[5]
	cu_hardware = response[7:-3].decode('ascii')

	print('Control unit address/endpoint: %02X:%02X' % (cu_address, cu_endpoint))
	print('Control unit hardware: %s' % cu_hardware)

	for hw in hex_hardware.split(','):
		if hw == cu_hardware:
			break
	else:
		assert False, "Firmware file is not compatible with control unit hardware"

	print('Starting the update...')

	send_packet_checked(b'\x10')

	while True:
		line = hex.readline().rstrip()
		assert line[0] == ':', 'Invalid firmware data'

		print(line)

		if line == ':00000001FF':
			break

		# send firmware data to the control unit
		send_packet_checked(b'\x01' + binascii.unhexlify(line[1:]))

		time.sleep(0.010)

	print('Finishing the update...')

	# check if checksum computed by control unit matches the checksum in the firmware file
	assert int(send_packet(b'\x03')[8:11].hex(), 16) == hex_checksum2, 'Firmware checksum mismatch'

	# commit the firmware and reboot the control unit
	send_packet_checked(b'\x01\x00\x00\x00\x01\xFF')

	print('Done')
