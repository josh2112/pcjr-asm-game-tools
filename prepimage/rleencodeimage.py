'''
Compresses the given 
'''

import argparse, array
import os
from PIL import Image, ImageOps, ImageTk

def encode( pixels ):
    '''
    Given a list of RGB tuples, performs a run-length encoding as pairs of adjacent runs packed into 3-byte chunks:
        byte 1: color 1 in upper nibble, color 2 in lower nibble
        byte 2: number of pixels of color 1
        byte 3: number of pixels of color 2
    The RGB pixel values must be in the given palette.
    Example: [3, 3, 3, 3, 3, 3, 3, 8, 8, 8, 8, 8, 2, 2, 2, 7, 7, 7, 7]
        7 pixels of color 3 followed by 5 pixels of color 8
        byte 1: 3 and 8 => (3 << 4) | 8 = 56
        byte 2: 7
        byte 3: 5
        following 3 bytes will be 39, 3, 4
    '''
    code, runcolor, runlength = [], None, 0
    # First do a standard run-length encoding into 'code':
    # color, numPixels, color, numPixels, ...
    for color in pixels:
        if color != runcolor:
            if runlength > 0:
                code += [runcolor, runlength]
                runlength = 0
        elif runlength == 255: 
            code += [runcolor, runlength]
            runlength = 0
        runcolor = color
        runlength += 1
    if runlength > 0:
        code += [runcolor, runlength]
    
    # Ensure there are an even number of runs, adding an empty one if not
    if len(code) % 4 == 2: code += [0,0]
    packedcode = []
    # For each pair of runs, encode the two colors, then add the lengths.
    for i in range( 0, len(code), 4 ):
        packedcode += [(code[i] << 4) | code[i+2], code[i+1], code[i+3]]
    return packedcode


def decode( code, size, pal ):
    '''
    For testing: Decodes the RLE, looking up each color index in the given
    palette, and returns the resulting image
    '''
    pixels = []
    for i in range( 0, len(code), 3 ):
        col1, col2 = code[i] >> 4, code[i] & 0xf
        pixels += [col1] * code[i+1]
        pixels += [col2] * code[i+2]
    img = Image.new( "P", size )
    img.putdata( pixels )
    img.putpalette( pal )
    return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run-length encodes an image' )
    parser.add_argument( 'input_path', type=argparse.FileType( 'rb' ))
    parser.add_argument( 'output_path', type=argparse.FileType( 'wb' ))
    args = parser.parse_args()

    img = Image.open( args.input_path )
    encoded = encode( list(img.getdata()))
    args.output_path.write( bytes( encoded ))
    args.output_path.close()

    #decode( encoded, img.size, img.getpalette() ).show()
      
    print( "Encoded {} to {} ({} bytes)".format( args.input_path.name, args.output_path.name, len(encoded)))
