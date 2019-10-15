import argparse, array
import os
from PIL import Image, ImageOps, ImageTk

IMGWIDTH, IMGHEIGHT = 160, 168
COLOR_NONE = 255
COLOR_WHITE = 15
COLOR_VISITED = 254

class PixelAccess:
    def __init__( self, pixels ):
        self.pixels = pixels
    
    def __getitem__( self, xy ):
        return COLOR_NONE if xy[0] < 0 or xy[0] >= IMGWIDTH or xy[1] < 0 or xy[1] >= IMGHEIGHT else self.pixels[xy[0],xy[1]]

    def __setitem__( self, xy, color ):
        if xy[0] >= 0 and xy[0] < IMGWIDTH and xy[1] >= 0 or xy[1] < IMGHEIGHT:
            self.pixels[xy[0],xy[1]] = color


def has4NeighborOfColor( pixels, x, y, c ): return \
        (x<IMGWIDTH-1 and pixels[x+1,y] == c) or \
        (x>0 and pixels[x-1,y] == c) or \
        (y<IMGHEIGHT-1 and pixels[x,y+1] == c) or \
        (y>0 and pixels[x,y-1] == c)

def floodFillEmpty( pixels, x, y ):
    q = [(x,y)]
    src_color = pixels[x,y]
    
    while q:
        x,y = q.pop( 0 )
        if pixels[x,y] == src_color and not has4NeighborOfColor( pixels, x, y, COLOR_NONE ):
            pixels[x,y] = COLOR_VISITED
            q += [(x+1,y), (x-1,y), (x,y+1), (x,y-1)]
    
    for y in range( IMGHEIGHT ):
        for x in range( IMGWIDTH ):
            if pixels[x,y] == COLOR_VISITED: pixels[x,y] == COLOR_NONE


def isOnFloodFillArea( pixels, x, y ):
    if pixels[x,y] == COLOR_NONE: return False
    for dy in range( -1, 2 ):
        for dx in range( -1, 2 ):
            if pixels[x,y] != pixels[x+dx,y+dy]: return False
    return True


def vectorize( pixels, pal ):
    # Set white pixels to an unused color so we don't create vector commands for them
    for y in range( IMGHEIGHT ):
        for x in range( IMGWIDTH ):
            if pixels[x,y] == COLOR_WHITE: pixels[x,y] = COLOR_NONE
    
    floodFills = []
    for c in range( 15, -1, -1 ):
        for y in range( IMGHEIGHT ):
            for x in range( IMGWIDTH ):
                if pixels[x,y] == c and isOnFloodFillArea( pixels, x, y ):
                    floodFills.append( (x,y,c) )
                    floodFillEmpty( pixels, x, y )


if __name__ == "__main__":
    parser = argparse.ArgumentParser( description='Experiments in image vectorization' )
    parser.add_argument( 'input_path', type=argparse.FileType( 'rb' ))
    args = parser.parse_args()

    pal_cga16 = (
        (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), # Bk Bl Gn Cy
        (170, 0, 0), (170, 0, 170),  (170, 85, 0), (170, 170, 170), # Rd Mg Br LGr
        (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), # DG LBl LGn LCy
        (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255) # LR LM LY Wh
    )

    img = Image.open( args.input_path )
    img.putpalette( [i for t in pal_cga16 for i in t] )
    vectorize( PixelAccess( img.load()), pal_cga16 )

    img.show()

    #args.output_path.write( bytes( encoded ))
    #args.output_path.close()
    
    #print( "Encoded {} to {} ({} bytes)".format( args.input_path.name, args.output_path.name, len(encoded)))

    #decoded = decode( encoded, pal_cga16 )
    #img2 = Image.new( img.mode, img.size )
    #img2.putdata( decoded )
    #img.show( img2 )
