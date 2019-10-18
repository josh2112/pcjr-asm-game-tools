import bs4
from PIL import Image, ImageQt
from PyQt5 import QtWidgets, QtGui, QtCore
import argparse, os, re, itertools, more_itertools, logging
import palettetools, svgtools, drawingtools, qttools

WHITE = 15

class Polyline:
    def __init__( self, tag, offset ):
        self.tag = tag
        local_offset = svgtools.get_transform( tag )
        self.offset = (offset[0]+local_offset[0], offset[1]+local_offset[1])
        self.lines = []

    def draw_into( self, img, palette ):
        style = svgtools.get_style( self.tag )
        color = style['fill'] if 'fill' in style and style['fill'] else style['stroke']
        c = palettetools.closest( color, palette )
        desc = self.tag.find( "desc" )
        if desc:
            values = [float(v) for v in re.split( "\s*,\s*|\s+", desc.text.strip())]
            fill_points = list( zip( values[::2], [img.size[1] - v for v in values[1::2]] ))
        else: fill_points = []
        drawingtools.draw_poly( self.lines, c, fill_points, img )

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
        self.initpt, self.cursor, self.lines = (0,0), (0,0), []
        for cmd, args in svgtools.parse_path( tag['d'] ):
            logging.info( "CMD %s, %s", cmd, args )
            if cmd == 'M':
                self.moveto_abs( args[:2] )
                if len(args) > 2: self.polyline_abs( args[2:] )
            elif cmd == 'm':
                if not self.lines: self.moveto_abs( args[:2] )
                else: self.moveto_rel( args[:2] )
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
                raise Exception( "Don't understand command '{}' of path {}".format( cmd, tag['id'] ))
    
    def moveto_abs( self, pt ):
        self.initpt = self.cursor = (pt[0]+self.offset[0], pt[1]+self.offset[1])
        logging.info( "  moveto %s", self.cursor )

    def moveto_rel( self, pt ):
        self.initpt = self.cursor = (pt[0]+self.cursor[0], pt[1]+self.cursor[1])
        logging.info( "  moveto %s", self.cursor )

    def polyline_abs( self, args ):
        pts = [self.cursor] + [(p[0]+self.offset[0], p[1]+self.offset[1]) for p in zip( args[::2], args[1::2] )]
        lines = list( more_itertools.pairwise( pts ))
        logging.info( "  lines %s", lines )
        self.lines += lines
        self.cursor = lines[-1][-1]
    
    def polyline_rel( self, args ):
        pts = [self.cursor] + list( zip( args[::2], args[1::2] ))
        for i in range( 1, len(pts)):
            pts[i] = (pts[i-1][0]+pts[i][0], pts[i-1][1]+pts[i][1])
        lines = list( more_itertools.pairwise( pts ))
        logging.info( "  lines %s", lines )
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
        line = (self.cursor, self.initpt)
        logging.info( "  line %s", line )
        self.lines.append( line )
        self.cursor = self.lines[-1][-1]


def render_tag( tag, offset, img ):
    if tag.name == 'path': figure = Path( tag, offset )
    elif tag.name == 'rect': figure = Rect( tag, offset )
    else: raise Exception( "Don't know how to handle tag", tag.name )
    figure.draw_into( img, palettetools.cga16 )


class SVGSimplifyWindow( QtWidgets.QWidget ):
    
    def __init__( self, parent=None ):
        super().__init__( parent )
        self.imageField = qttools.QAliasedPixmap( 320/168, 3 )
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins( QtCore.QMargins() )
        hbox.addWidget( self.imageField )
        
        self.setLayout( hbox )
    
    def set_image( self, pil_img ):
        self.imageField.setPixmap( QtGui.QPixmap.fromImage( ImageQt.ImageQt( pil_img ) ))
        self.imageField.adjustSize()

def update_image( window, img ):
    window.set_image( img )
    QtCore.QCoreApplication.processEvents()

# Algorithm:
# * Collect filled features only (fill != none), render them front to back (reverse file order).
#   * While plotting points on the boundary, if the canvas is non-white, skip it. This will prevent drawing useless paths
#     under stuff that will be filled over.
#   * After plotting the boundary, flood-fill at points stored in the SVG "description" field. It won't matter if
#     we skipped pixels while drawing the border, because _something_ will be there to stop the flood.
# * Collect stroke features only (fill == none), render them back to front (in file order)
# - If this works, serialize the paths to a simple format:
#   - lines first, individually, chopping out the parts of lines we didn't draw
#   - flood fill points next
# - Write Python script to render the simple serialized format to make sure it works
# - Further optimize by removing empty lines and combining adjacent lines with the same slope

if __name__ == '__main__':
    #logging.basicConfig( level=logging.INFO )

    parser = argparse.ArgumentParser( description='Convert an SVG file into a simplified vector format' )
    parser.add_argument( 'svgpath', type=argparse.FileType('rb'), help='path to SVG file' )
    args = parser.parse_args()

    img = Image.new( 'P', (160,168), WHITE )
    img.putpalette( palettetools.pil_palette( palettetools.cga16 ))

    app = QtWidgets.QApplication( [] )
    app.setApplicationName( os.path.basename( args.svgpath.name ) + ' - SVG Simplify' )
    #with open( "style.qss", 'r' ) as f:
    #    app.setStyleSheet( f.read())

    window = SVGSimplifyWindow()
    window.set_image( img )
    window.show()
    QtCore.QCoreApplication.processEvents()

    soup = bs4.BeautifulSoup( args.svgpath, 'html.parser' )
    layer = soup.select( '#layer1' )[0]
    offset = svgtools.get_transform( layer )
    logging.info( "OFFSET %s", offset )

    alltags = layer.find_all( True, recursive=False )
    #alltags = [t for t in alltags if t['id'] in ('path1065')]

    polys = [t for t in alltags if 'fill:none' not in t['style']]
    lines = [t for t in alltags if 'fill:none' in t['style']]
    
    for tag in reversed( polys ):
        render_tag( tag, offset, img )
        update_image( window, img )

    for tag in lines:
        render_tag( tag, offset, img )
        update_image( window, img )
    
    window.set_image( img )
    img.save( "test.png" )
    
    app.exec_()
