
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


_is_colorable = lambda x,y,img: img.getpixel( (x,y) ) == 15

def flood_fill( pt, color, img ):
    print( "filling {} with {}".format( pt, color ))
    pixels = [pt]
    while pixels:
        x,y = pixels.pop()
        while x >= 0 and _is_colorable( x, y, img ): x -= 1
        x += 1

        span_down, span_up = False, False

        while x < img.size[0] and _is_colorable( x, y, img ):
            img.putpixel( (x,y), color )
            if not span_up and y > 0 and _is_colorable( x, y-1, img ):
                pixels.append( (x,y-1) )
                span_up = True
            elif span_up and (y == 0 or not _is_colorable( x, y-1, img )): span_up = False

            if not span_down and y < img.size[1]-1 and _is_colorable( x, y+1, img ):
                pixels.append( (x,y+1) )
                span_down = True
            elif span_down and (y == img.size[1]-1 and not _is_colorable( x, y+1, img )): span_down = False

            x += 1


clamp = lambda x,max_: max( 0, min( max_, x ))

def prepare( coord, size ):
    return clamp( round( coord[0]/2 ), size[0]-1 ), clamp( round( coord[1] ), size[1]-1 )

def draw_poly( lines, color, fill_points, img ):
    for pair in lines:
        pair = [i for coord in [prepare( coord, img.size ) for coord in pair] for i in coord]
        for pt in line( *pair ):
            if _is_colorable( pt[0], pt[1], img ) or not fill_points:
                img.putpixel( pt, color )
    for pt in fill_points:
        flood_fill( prepare( pt, img.size ), color, img )