import logging, math
import palettetools
from enum import IntEnum, unique

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


is_colorable = lambda x,y,img: img.getpixel( (x,y) ) == 15

def flood_fill( pt, color, img ):
    logging.info( "filling {} with {}".format( pt, color ))
    num_filled = 0
    pixels = [pt]
    while pixels:
        x,y = pixels.pop()
        while x >= 0 and is_colorable( x, y, img ): x -= 1
        x += 1

        span_down, span_up = False, False

        while x < img.size[0] and is_colorable( x, y, img ):
            img.putpixel( (x,y), color )
            num_filled += 1
            
            if not span_up and y > 0 and is_colorable( x, y-1, img ):
                pixels.append( (x,y-1) )
                span_up = True
            elif span_up and (y == 0 or not is_colorable( x, y-1, img )): span_up = False

            if not span_down and y < img.size[1]-1 and is_colorable( x, y+1, img ):
                pixels.append( (x,y+1) )
                span_down = True
            elif span_down and (y == img.size[1]-1 or not is_colorable( x, y+1, img )): span_down = False

            x += 1

    return num_filled


clamp = lambda x,max_: max( 0, min( max_, x ))

@unique
class Commands( IntEnum ):
    FINISHED = 0
    COLOR = 1
    MOVETO = 2
    LINETO = 3
    HLINETO = 4
    VLINETO = 5
    FILL = 6

class Plotter:
    def __init__( self ):
        self.cursor, self.point = None, None
        self.plotting, self.color = False, None

class SVGSimplifier():
    def __init__( self, img, callback_update_image=None, incremental_update=False ):
        self.img = img
        self.callback_update_image, self.incremental_update = callback_update_image, incremental_update
        self.cmds = []
        self.plotter = Plotter()

    def prepare( self, pt ):
        return clamp( round( pt[0]/2 ), self.img.size[0]-1 ), clamp( round( pt[1] ), self.img.size[1]-1 )

    def render( self, figure ):
        self.set_color( palettetools.closest( figure.color, palettetools.cga16 ))
        
        fill_points = figure.fill_points( self.img.size[1] )
        
        for pair in figure.lines:
            pair = [i for pt in [self.prepare( pt ) for pt in pair] for i in pt]
            
            for pt in line( *pair ):
                if pt == self.plotter.point:
                    continue
                if is_colorable( pt[0], pt[1], self.img ) or not fill_points:
                    self.img.putpixel( pt, self.plotter.color )
                    if not self.plotter.plotting:
                        if self.plotter.cursor != pt:
                            self.cmds.append( (Commands.MOVETO, pt[0], pt[1]) )
                            self.plotter.cursor = pt
                        self.plotter.plotting = True
                else:
                    if self.plotter.plotting:
                        self.cmds.append( (Commands.LINETO, self.plotter.point[0], self.plotter.point[1] ))
                        self.plotter.cursor = self.plotter.point
                        self.plotter.plotting = False
                self.plotter.point = pt
            
            if self.plotter.plotting:
                self.cmds.append( (Commands.LINETO, self.plotter.point[0], self.plotter.point[1] ))
                self.plotter.cursor = self.plotter.point
            self.plotter.point = pt
            
            self.update()
        
        self.plotter.plotting = False
        
        for pt in [self.prepare( p ) for p in fill_points]:
            if flood_fill( pt, self.plotter.color, self.img ) > 0:
                self.cmds.append( (Commands.FILL, pt[0], pt[1]) )
                self.update()

    def set_color( self, color ):
        if self.plotter.color != color:
            self.plotter.color = color
            self.cmds.append( (Commands.COLOR, self.plotter.color) )

    def update( self ):
        if self.incremental_update and self.callback_update_image:
            self.callback_update_image()
    
    def clean( self ):
        num_commands = len(self.cmds)
        for i in range( num_commands-1, 1, -1 ):
            if self.cmds[i] == self.cmds[i-1]:
                del self.cmds[i]
            elif self.cmds[i] == self.cmds[i-1] == self.cmds[i-2] == Commands.LINETO:
                angles = [math.atan2( self.cmds[j][2] - self.cmds[j-1][2], self.cmds[j][1] - self.cmds[j-1][1] ) for j in (i,i-1)]
                if angles[0] == angles[1]:
                    del self.cmds[i-1]
                    i -= 1
        print( "Removed {} redundant command(s)".format( num_commands - len(self.cmds)))

    
    def write_cmds( self ):
        for cmd in self.cmds:
            print( "{} {}".format( cmd[0].name, ', '.join( str(x) for x in cmd[1:] )))


class SimpleSVGRenderer:
    def __init__( self, img ):
        self.img = img
    
    def render( self, cmds ):
        for cmd in cmds:
            if cmd[0] == Commands.COLOR:
                self.color = cmd[1]
            elif cmd[0] == Commands.MOVETO:
                self.cursor = (cmd[1],cmd[2])
            elif cmd[0] == Commands.LINETO:
                for pt in line( self.cursor[0], self.cursor[1], cmd[1], cmd[2] ):
                    self.img.putpixel( pt, self.color )
                self.cursor = (cmd[1],cmd[2])
            elif cmd[0] == Commands.FILL:
                flood_fill( (cmd[1],cmd[2]), self.color, self.img )
        
        print( "{} command(s) (upper bound {} bytes)".format( len(cmds), sum( len(c) for c in cmds )))
