#!/usr/bin/env python3

import sys, math, os
import serial
import argparse

url = "socket://localhost:7000"
#url = "/dev/tty.UC-232AC"

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
                self.serial.write( bytes( packet ) )
                response = self.serial.read( 1 )[0]
                if response == ACK:
                    break
                elif response == NAK:
                    print( "NAK received, resending packet" )
                else:
                    print( "Unknown response received ({})!".format( response ) )
                    return
            print( "{}%".format( file.tell() / size * 100 ))
    
    def make_packet( self, file, header=None ):
        packet = [SOH]
        if header: packet += header
        packet += file.read( 133-len(packet))
        packet.extend( [0] * (133-len(packet))) # pad with zeroes up to 133
        packet += [sum( packet ) % 256]
        return packet

    def make_first_packet( self, name, size ):
        name, ext = os.path.splitext( name )
        packet = [SOH]
        packet += bytes( (name[:8] + ext[:3]).ljust( 12, '\0' ), 'ascii' )
        packet += size.to_bytes( 4, 'little' )
        packet += [sum( packet ) % 256]
        return packet


if __name__=="__main__":
    parser = argparse.ArgumentParser( description='Sends a file over the serial port.' )
    parser.add_argument( 'path', help='path to the file to send' )
    args = parser.parse_args()

    with serial.serial_for_url( url ) as serial:
        print( "Opened port {}".format( serial.name ) )
        
        filesize = os.stat( args.path ).st_size
        if filesize > 32000:
            print( "Too big to send!" )
            sys.exit

        with open( args.path, 'rb' ) as file:
            print( "Sending file '{}' ({} bytes)...".format( args.path, filesize ))
            JModemSender( serial ).send( file, os.path.basename( args.path ), filesize )

        print( "Done!" )
