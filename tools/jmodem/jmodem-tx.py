#!/usr/bin/env python3

import sys, math, os
import serial
import argparse

#url = "socket://localhost:7000"
url = "/dev/tty.UC-232AC"

SOH = 1
ACK = 6
NAK = 21

class JModemSender:
    def __init__( self, serial ):
        self.serial = serial
    
    def send( self, file, name, size ):
        first_packet_sent = False

        while file.peek():
            if not first_packet_sent:
                packet = self.make_first_packet( name, size )
                first_packet_sent = True
            else:
                packet = self.make_packet( file )
            while True:
                #print( "Writing ", bytes(packet ))
                self.serial.write( bytes( packet ) )
                response = self.serial.read( 1 )[0]
                if response == ACK:
                    break
                elif response == NAK:
                    print( "NAK received, resending packet" )
                else:
                    print( "Unknown response received ({})!".format( response ) )
                    return
            print( "{}%".format( round( file.tell() / size * 100 )))
    
    def make_packet( self, file ):
        packet = [SOH]
        packet += file.read( 126 ).ljust( 126, b'\0' )
        packet += [sum( packet ) % 256]
        return packet

    def make_first_packet( self, name, size ):
        """Makes a 16-byte packet: [SOH][filename(12,padded)][size(2)][chk]"""
        name, ext = os.path.splitext( name )
        packet = [SOH]
        packet += bytes( (name[:8] + ext[:4]).ljust( 12, '\0' ), 'ascii' )
        packet += size.to_bytes( 2, 'little' )
        packet += [sum( packet ) % 256]
        return packet


if __name__=="__main__":
    parser = argparse.ArgumentParser( description='Sends a file over the serial port.' )
    parser.add_argument( 'path', help='path to the file to send' )
    args = parser.parse_args()

    with serial.serial_for_url( url, baudrate=1200 ) as serial:
        serial.baudrate = 1200
        print( "Opened port {}".format( serial.name ) )
        
        filesize = os.stat( args.path ).st_size
        if filesize > 32767:
            print( "Too big to send!" )
            sys.exit

        with open( args.path, 'rb' ) as file:
            print( "Sending file '{}' ({} bytes)...".format( args.path, filesize ))
            JModemSender( serial ).send( file, os.path.basename( args.path ), filesize )

        print( "Done!" )
