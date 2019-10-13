from PIL import Image

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


def plotLineLow( x0, y0, x1, y1 ):
    dx, dy, yi = x1 - x0, y1 - y0, 1
    if dy < 0:
        dy, yi = -dy, -1
    y, D = y0, 2*dy - dx
    pts = []
    for x in range( x0, x1+1 ):
        pts += [(x,y)]
        if D > 0:
            y = y + yi
            D = D - 2*dx
        D = D + 2*dy
    return pts

def plotLineHigh( x0, y0, x1, y1 ):
    dx, dy, xi = x1 - x0, y1 - y0, 1
    if dx < 0:
        dx, xi = -dx, -1
    x, D = x0, 2*dx - dy
    pts = []
    for y in range( y0, y1+1 ):
        pts += [(x,y)]
        if D > 0:
            x = x + xi
            D = D - 2*dy
        D = D + 2*dx
    return pts

def line( x0, y0, x1, y1 ):
    if abs( y1 - y0 ) < abs( x1 - x0 ):
        if x0 > x1:
            pts = plotLineLow( x1, y1, x0, y0 )
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return list( zip( reversed( xs ), reversed( ys )))
        else:
            return plotLineLow( x0, y0, x1, y1 )
    else:
        if y0 > y1:
            pts = plotLineHigh( x1, y1, x0, y0 )
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return list( zip( reversed( xs ), reversed( ys )))
        else:
            return plotLineHigh( x0, y0, x1, y1 )

def perimeter( size ):
    top = list( zip( range( size[0]-1 ), [0] * (size[0]-1)))
    right = list( zip( [size[0]-1] * (size[1]-1), range( size[1]-1 )))
    bottom = list( zip( range( size[0]-1, 0, -1 ), [size[1]-1] * (size[0]-1) ))
    left = list( zip( [0] * (size[1]-1), range( size[1]-1, 0, -1 )))
    return top + right + bottom + left

def trace_polyline( pixels, x, y ):
    '''
    Traces a line from (x,y) to every border pixel, returning the one which
    covers the most pixels the same color as (x,y) and starting at (x,y).
    '''
    c = pixels[x,y]

    points = [(x,y)]

    while True:
        max_num = 0
        best_pts = None
        for p in perimeter( pixels.size ):
            pts = line( x, y, p[0], p[1] )
            for i in range(len(pts)):
                if pixels[pts[i][0],pts[i][1]] != c: break
            if i > max_num:
                max_num = i
                best_pts = pts[:i]
        if max_num == 1:
            return points
        print( "best line is ", best_pts )
        points += [best_pts[-1]]
        for p in best_pts[:-1]: pixels[p[0],p[1]] = (255,255,255)
        x,y = best_pts[-1]


if __name__ == "__main__":
    img = Image.open( "../pcjr-asm-game/room1/room1.png" )
    pixels = PixelAccess( img )
    polyline = trace_polyline( pixels, 120, 68 )
    print( polyline )
    img.show()