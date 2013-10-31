#!/usr/bin/python

__author__="SubOptimal"
__date__ ="$31.10.2013$"
__version__="v0.2"
__url__="https://github.com/SubOptimal/mysmartusb-firmware-flasher"

from os.path import exists, basename
import struct
import sys
import time

import serial

def failure (message):
    print (message)
    quit (1)

def read_field (fd):
    s = ""
    while True:
        x = fd.read (1)
        if x == '\r':
            break
        s += x
    return s

def usage():
    print ("ERROR: missed parameter\n")
    print ("usage: " + basename(sys.argv[0]) + " *.firmware *.eeprom")
    print ("  *.firmware - the firmware data")
    print ("  *.eeprom   - the EEPROM data\n")
    print ("NOTE: firmware and eeprom binaries must have been stripped from the same firmware elf binary.")
    quit(1)

if (len(sys.argv) != 3):
    usage()

if not exists(sys.argv[1]):
    failure("firmware file not found: " + sys.argv[1])

if not exists(sys.argv[2]):
    failure("eeprom file not found: " + sys.argv[2])

# read firmware (raw binary format)
firmware_bin = file(sys.argv[1]).read()
if len(firmware_bin) < 112 or firmware_bin[106:112] <> "msuLso":
    failure("the file seems not to contain a valid firmware image - " + sys.argv[1])

# read EEPROM data
eeprom_bin = file(sys.argv[2]).read()
if eeprom_bin[0:1] <> "\x69\x35":
    failure("the file seems not to contain valid EEPROM data - " + sys.argv[2])

fd = serial.Serial ("/dev/ttyUSB0", 115200, bytesize = serial.EIGHTBITS, stopbits = serial.STOPBITS_ONE, parity = serial.PARITY_NONE)

print ("reset the adapter...")
fd.write("\xE6\xB5\xBA\xB9\xB2\xB3\xA9R")
fd.flush()

time.sleep (0.5)

print ("enter bootloader mode...")
fd.baudrate=19200
fd.write (chr (0xAB) + "myBurn" + chr (0xBB))
fd.flush()

# wait for bootloader response
tries = 0
time.sleep(0.2)
while True:
    if fd.inWaiting() > 0 and fd.read(7) == 'myBurn\r':
        print ("")
        break
    tries += 1
    if tries > 20:
        print "give up"
        exit()

# get programmer information
hw    = read_field (fd)
hwver = read_field (fd)
swver = read_field (fd)
proc  = read_field (fd)
freq  = int (read_field (fd), 16)
blks  = int (read_field (fd), 16)
maxs  = int (read_field (fd), 16)
baud  = int (read_field (fd), 16)
unknown  = int (read_field (fd), 16)

if fd.read (1) <> "\n":
    failure ("failed to get adapter information")

print "Hardware        : " + hw
print "Hardware version: " + hwver
print "Software version: " + swver
print "Processor       : " + proc
print "Processor clock : " + str (freq)
print "Block size      : " + str (blks)
print "Max. size       : " + str (maxs)
print "Baudrate        : " + str (baud)
# print "unknown         : " + str (unknown)

if (hw != "mySmartUSB Light"):
    # TODO properly reset the adapter
    fd.close()
    failure("only the 'mySmartUSB Light' adapter has been tested")

print ("\nWriting firmware")

# set burn baudrate
fd.baudrate = baud

# send firmware header
fd.write ("F" + chr (0x00) + chr (0x00) + chr (0x00) + struct.pack("<I", len (firmware_bin))[:-1] + "\n")
fd.flush ()

if fd.read (2) <> "F\n":
    # TODO properly reset the adapter
    fd.close()
    failure ("send firmware header failed")

for i in range (0, len (firmware_bin), blks):
    sys.stdout.write (".")
    sys.stdout.flush ()
    l = (blks if (i + blks <= len (firmware_bin)) else (len (firmware_bin) - i))
    fd.write ("f" + struct.pack("<H", l) + "\n" + firmware_bin [i:i+l])
    if fd.read (3) <> "f0\n":
        failure ("failed to write block #" + str(i))

# signalise end of burning
fd.write ("e\n")
if fd.read (2) <> "e0":
    failure ("unexpected respond at the end of burning")

print (" end.")

checksum = int (fd.read (10), 16)
print ("checksum bootloader: %X" % checksum)
# read the newline
fd.read(1)

checksum=0
for i in range (0, len(firmware_bin), 1):
    checksum += ord(firmware_bin[i])
print ("checksum file      : %X" % checksum)

# exit bootloader
fd.write ("X\n")
fd.flush ()
if fd.read (2) <> "X\n":
    failure ("unexpected respond to exit the bootloader")

print ("")

while True:
    if fd.inWaiting () > 0:
        fd.flushInput ()
        time.sleep (0.1)
    else:
        break

fd.close()

print ("Finished writing!")

