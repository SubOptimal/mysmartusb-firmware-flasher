HOWTO
-----

<pre>
<b>usage:</b><br>
   mysmartusb_firmware.py firmware eeprom
     *.firmware - the firmware data in raw binary format
     *.eeprom   - the EEPROM data

NOTE: firmware and eeprom binaries must have been stripped from the same firmware elf binary.

<b>example:</b>
   mysmartusb_firmware.py mysmartusblight_stk500_v111_b1897.firmware  mysmartusblight_stk500_v111_b1897.eeprom
     this will burn the firmware for the STK500v2 mode

   mysmartusb_firmware.py mysmartusblight_avr911_v111_b1900.firmware  mysmartusblight_avr911_v111_b1900.eeprom
     this will burn the firmware for the AVR911 mode
</pre>
