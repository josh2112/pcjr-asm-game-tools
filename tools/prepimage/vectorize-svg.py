from bs4 import BeautifulSoup
from PIL import Image
import palettetools, svgtools, drawingtools
import sys, re, itertools

WHITE = 15

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class Polyline:
    def __init__( self, tag, offset ):
        self.tag, self.offset = tag, offset
        self.lines = []

    def draw_into( self, img, palette ):
        style = svgtools.get_style( self.tag )
        color = style['fill'] if 'fill' in style and style['fill'] else style['stroke']
        c = palettetools.closest( color, palette )
        drawingtools.draw_polylines( self.lines, c, img )

class Rect( Polyline ):
    def __init__( self, tag, offset ):
        super().__init__( tag, offset )
        width, height = [float( tag[attr] ) for attr in ('width','height')]
        x = float( tag['x'] ) + offset[0]
        y = float( tag['y'] ) + offset[1]
        self.lines = [((x,y), (x+width,y)), ((x+width,y), (x+width, y+height)), \
            ((x+width, y+height), (x,y+height)), ((x,y+height), (x,y))]

class Path( Polyline ):
    def __init__( self, tag, offset ):
        super().__init__( tag, offset )
        self.cursor, self.lines = (0,0), []
        for segment in svgtools.parse_path( tag['d'] ):
            print( "SEGMENT ", segment )
            args, cmd = segment[1:], segment[0]
            if cmd == 'M':
                self.moveto_abs( args[:2] )
                if len(args) > 2: self.polyline_abs( args[2:] )
            elif cmd == 'm':
                self.moveto_abs( (self.cursor[0]+args[0], self.cursor[1]+args[1]) )
                if len(args) > 2: self.polyline_rel( args[2:] )
            elif cmd == 'Z'or cmd == 'z':
                self.closepath()
            elif cmd == 'L':
                self.polyline_abs( args )
            elif cmd == 'l':
                self.polyline_rel( args )
            elif cmd == 'H':
                self.hline_abs( args )
            elif cmd == 'h':
                self.hline_rel( args )
            elif cmd == 'V':
                self.vline_abs( args )
            elif cmd == 'v':
                self.vline_rel( args )
            else:
                raise Exception( "Don't understand command '{}' of path {}".format( cmd, shape['id'] ))
    
    def moveto_abs( self, pt ):
        self.cursor = (pt[0]+self.offset[0], pt[1]+self.offset[1])
        print( "moveto:", self.cursor )

    def polyline_abs( self, args ):
        pts = [self.cursor] + [(p[0]+self.offset[0], p[1]+self.offset[1]) for p in zip( args[::2], args[1::2] )]
        lines = list( pairwise( pts ))
        print( "lines:", lines )
        self.lines += lines
        self.cursor = lines[-1][-1]
    
    def polyline_rel( self, args ):
        pts = [self.cursor] + list( zip( args[::2], args[1::2] ))
        for i in range( 1, len(pts)):
            pts[i] = (pts[i-1][0]+pts[i][0], pts[i-1][1]+pts[i][1])
        lines = list( pairwise( pts ))
        print( "lines:", lines )
        self.lines += lines
        self.cursor = lines[-1][-1]
        
    def hline_abs( self, args ):
        pts = []
        for x in args: pts += [x+self.offset[0], self.cursor[1]]
        self.polyline_abs( pts )

    def hline_rel( self, args ):
        pts = []
        for x in args: pts += [x, 0]
        self.polyline_rel( pts )

    def vline_abs( self, args ):
        pts = []
        for y in args: pts += [self.cursor[0], y+self.offset[1]]
        self.polyline_abs( pts )

    def vline_rel( self, args ):
        pts = []
        for y in args: pts += [0, y]
        self.polyline_rel( pts )
    
    def closepath( self ):
        line = (self.cursor, self.lines[0][0])
        print( "line", line )
        self.lines.append( line )
        self.cursor = self.lines[-1][-1]


# TODO Tomorrow: Draw each figure to a separate .PNG (named with the figure's ID)
# so we can see which paths are messing up

if __name__ == '__main__':
    img = Image.new( 'P', (160,168), WHITE )
    img.putpalette( palettetools.pil_palette( palettetools.cga16 ))

    with open( '../pcjr-asm-game/room1/room1.svg', ) as f:
        soup = BeautifulSoup( f, 'html.parser' )
    layer = soup.select( '#layer1' )[0]
    offset = svgtools.get_transform( layer )
    
    for tag in list( reversed( layer.find_all( True ))):
        if tag.name == 'path': figure = Path( tag, offset )
        elif tag.name == 'rect': figure = Rect( tag, offset )
        else: raise Exception( "Don't know how to handle tag", tag.name )
        figure.draw_into( img, palettetools.cga16 )
    
    img.show()
