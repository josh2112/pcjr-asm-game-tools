from PIL import Image
import itertools


def surrounding_block_all_in( img, x, y, colors ):
    for coord in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
        px = img.getpixel( coord )
        if px not in colors: return False
    return True

def unfill( img ):
    w,h = img.size
    for y in range( 1, h-1 ):
        for x in range( 1, w-1 ):
            if surrounding_block_all_in( img, x, y, [img.getpixel( (x, y) ), 15] ):
                img.putpixel( (x, y), 15 )


class PixelAccess:
    def __init__( self, image ):
        self.image, self.pixels = image, image.load()
    
    @property
    def size( self ):
        return self.image.size

    def __getitem__( self, xy ):
        return self.pixels[xy[0], xy[1]]
    
    def __setitem__( self, xy, color ):
        self.pixels[xy[0],xy[1]] = color


def line( x0, y0, x1, y1 ):
    '''Bresenham line drawing algorithm. Yields pixels on the line (x0,y0) to (x1,y1)'''
    dx, dy = x1 - x0, y1 - y0
    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx, dy = abs(dx), abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2*dy - dx
    y = 0

    for x in range(dx + 1):
        yield x0 + x*xx + y*yx, y0 + x*xy + y*yy
        if D >= 0:
            y += 1
            D -= 2*dx
        D += 2*dy


def perimeter( size ):
    '''Returns the pixels on the perimeter of the image'''
    width, height = size[0]-1, size[1]-1
    for x in range( width ): yield (x,0)
    for y in range( height ): yield (width,y)
    for x in range( width, 0, -1 ): yield (x,height)
    for y in range( height, 0, -1 ): yield (0,y)

def trace_polyline( pixels, x, y ):
    '''
    Traces a line from (x,y) to every border pixel, returning the one which
    covers the most pixels the same color as (x,y) and starting at (x,y).
    '''
    c = pixels[x,y]
    points = [(x,y)]

    while True:
        best_pts = []
        for p in perimeter( pixels.size ):
            pts = []
            for pt in line( x, y, p[0], p[1] ):
                if pixels[pt[0],pt[1]] != c: break
                else: pts.append( pt )
            if len(pts) > len(best_pts):
                best_pts = pts
        if len(best_pts) == 1:
            pixels[points[-1][0],points[-1][1]] = 15
            return points
        points += [best_pts[-1]]
        for p in best_pts[:-1]: pixels[p[0],p[1]] = 15
        x,y = best_pts[-1]


if __name__ == "__main__":
    img = Image.open( "../pcjr-asm-game/room1/room1.png" )
    unfill( img )
    pixels = PixelAccess( img )
    polyline = trace_polyline( pixels, 120, 69 )
    print( polyline )
    img.show()