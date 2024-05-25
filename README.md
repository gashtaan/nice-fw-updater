# Nice Firmware Updater

When I bricked motor control unit after unsuccessful firmware update using Nice BiDi-WiFi module and MyNice Pro app, I reverse engineered the process and decided to make this tool to update firmware without need of any additional proprietary Nice hardware/software. I've tested it on a RBA3R10 motor control unit, but I assume it should work on any R10 device.

## How to use
Connect your serial port to T4 bus of the control unit. UART RX/TX signals of this bus are exposed on dedicated T4 connector or radio receiver module connector, doesn't matter which one you choose.

Run the provided Python script:
```
updater.py COM3 FG01h.hex
```
The first argument specifies the serial port and the second argument is a path to the firmware file.

The tool will reboot the control unit to bootloader and initiate the firmware update. If everything goes right, the control unit should automatically reboot to updated firmware.

*AFAIK the firmware files are not freely available, so I won't publish any of them there, it's up to you how you obtain them.*