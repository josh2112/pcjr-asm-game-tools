import bs4
from PIL import Image, ImageQt
from PyQt5 import QtWidgets, QtGui, QtCore
import argparse, os, re, logging
import palettetools, svgtools, drawingtools, qttools

def figure_from_tag( tag, offset ):
    if tag.name == 'path': return svgtools.Path( tag, offset )
    elif tag.name == 'rect': return svgtools.Rect( tag, offset )
    else: raise Exception( "Don't know how to handle tag", tag.name )


class SVGSimplifyWindow( QtWidgets.QWidget ):
    def __init__( self, parent=None ):
        super().__init__( parent )
        self.imageField1 = qttools.QAliasedPixmap( 320/168, 3 )
        self.imageField2 = qttools.QAliasedPixmap( 320/168, 3 )
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins( QtCore.QMargins() )
        hbox.addWidget( self.imageField1 )
        hbox.addWidget( self.imageField2 )
        
        self.setLayout( hbox )
    
    def set_image_1( self, pil_img ):
        self.imageField1.setPixmap( QtGui.QPixmap.fromImage( ImageQt.ImageQt( pil_img ) ))
        self.imageField1.adjustSize()

    def set_image_2( self, pil_img ):
        self.imageField2.setPixmap( QtGui.QPixmap.fromImage( ImageQt.ImageQt( pil_img ) ))
        self.imageField2.adjustSize()

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

    img = Image.new( 'P', (160,168), 15 )
    img.putpalette( palettetools.pil_palette( palettetools.cga16 ))

    img2 = Image.new( 'P', img.size, 15 )
    img2.putpalette( img.getpalette())

    app = QtWidgets.QApplication( [] )
    app.setApplicationName( os.path.basename( args.svgpath.name ) + ' - SVG Simplify' )
    #with open( "style.qss", 'r' ) as f:
    #    app.setStyleSheet( f.read())
    
    window = SVGSimplifyWindow()
    window.set_image_1( img )
    window.set_image_2( img )
    window.show()
    QtCore.QCoreApplication.processEvents()
    
    def update_image_1():
        window.set_image_1( img )
        QtCore.QCoreApplication.processEvents()

    simplifier = drawingtools.SVGSimplifier( img, update_image_1, False )

    soup = bs4.BeautifulSoup( args.svgpath, 'html.parser' )
    layer = soup.select( '#layer1' )[0]
    offset = svgtools.get_transform( layer )
    logging.info( "OFFSET %s", offset )

    alltags = layer.find_all( True, recursive=False )
    #alltags = [t for t in alltags if t['id'] in ('path4605')]

    polys = [t for t in alltags if 'fill:none' not in t['style']]
    lines = [t for t in alltags if 'fill:none' in t['style']]
    
    for tag in reversed( polys ):
        simplifier.render( figure_from_tag( tag, offset ))

    for tag in lines:
        simplifier.render( figure_from_tag( tag, offset ))

    update_image_1()
    img.save( "test.png" )
    
    simplifier.clean()

    renderer = drawingtools.SimpleSVGRenderer( img2 )
    renderer.render( simplifier.cmds )
    
    window.set_image_2( img2 )
    
    app.exec_()
