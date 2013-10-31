#!/bin/sh

# strip the firmware and the EEPROM  data from firmware elf binary

usage() {
	SCRIPT_NAME=${0##*/}
	printf "usage  : ${SCRIPT_NAME} firmware_elf_binary\n"
	printf "example: ${SCRIPT_NAME} mysmartusblight_stk500_v111_b1897.elf\n"
}

if [ -z "`which avr-objcopy`" ]
then
	echo "ERROR: executable 'avr-objcopy' not found"
	echo "check the PATH environment variable or install the package 'binutils-avr'"
	exit 1
fi

if [ $# -ne 1 ]
then
	echo "ERROR: parameter missed..."
	usage
	exit 1
fi

file_name=${1%%.*}
file_ext=${1##*.}

if [ "$file_ext" != "elf" ];
then
	echo "ERROR: AVR elf binary expected... - '${1}'"
	exit 1
fi

avr-objcopy -O binary -R .eeprom -S "${file_name}.elf" "${file_name}.firmware"
avr-objcopy -O binary -j .eeprom "${file_name}.elf" "${file_name}.eeprom"
