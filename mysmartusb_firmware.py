#!/usr/bin/python

__author__="SubOptimal"
__date__ ="$25.09.2013$"
__version__="v0.1"
__url__="https://github.com/SubOptimal/mysmartusb-firmware-flasher"

from os.path import exists
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

if not exists(sys.argv[1]):
    failure("file not found: " + sys.argv [1])

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

# read firmware (Intel bin format)
code = file (sys.argv [1]).read ()

# send firmware header
fd.write ("F" + chr (0x00) + chr (0x00) + chr (0x00) + struct.pack("<I", len (code))[:-1] + "\n")
fd.flush ()

if fd.read (2) <> "F\n":
    # TODO properly reset the adapter
    fd.close()
    failure ("send firmware header failed")

for i in range (0, len (code), blks):
    sys.stdout.write (".")
    sys.stdout.flush ()
    l = (blks if (i + blks <= len (code)) else (len (code) - i))
    fd.write ("f" + struct.pack("<H", l) + "\n" + code [i:i+l])
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
for i in range (0, len(code), 1):
    checksum += ord(code[i])
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

print "Finished writing!"
