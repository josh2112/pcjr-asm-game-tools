
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

def clamp( x, max_ ):
    return max( 0, min( max_, x ))

def prepare( coord, size ):
    return clamp( round( coord[0]/2 ), size[0]-1 ), clamp( round( coord[1] ), size[1]-1 )

def draw_polylines( lines, color, img ):
    for pair in lines:
        pair = [i for coord in [prepare( coord, img.size ) for coord in pair] for i in coord]
        for pt in line( *pair ):
            img.putpixel( pt, color )
