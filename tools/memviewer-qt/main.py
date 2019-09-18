import sys, argparse, os, math
from PyQt5 import QtCore, QtGui, QtWidgets

def clamp( val, min, max ): return min if val < min else max if val > max else val

pal_pcjr16color = [QtGui.qRgb( c[0], c[1], c[2] ) for c in (
    (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
    (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)
)]

class QAliasedPixmap( QtWidgets.QWidget ):
    def __init__( self, parent=None ):
        super().__init__( parent )
    
    def setPixmap( self, pm ):
        self.pixmap = pm
        self.update( self.rect())

    def clear( self ):
        self.pixmap = None
        self.update( self.rect())
    
    def paintEvent( self, qpe ):
        if self.pixmap:
            painter = QtGui.QPainter( self )
            painter.setRenderHint( QtGui.QPainter.Antialiasing, False )
            if self.pixmap: self.style().drawItemPixmap( painter, self.rect(), QtCore.Qt.AlignCenter, self.pixmap.scaled( self.rect().size()))
        else: super().paintEvent( qpe )


class MemViewerWindow( QtWidgets.QWidget ):
    paramsChanged = QtCore.pyqtSignal( int, int, int )

    def __init__( self ):
        super().__init__()
        self.setObjectName( 'window' )
        self.offsetField = MemViewerWindow._make_spin_box( 'offsetField', self.on_offset_changed )
        self.lengthField = MemViewerWindow._make_spin_box( 'lengthField', self.on_length_changed )
        self.spanField = MemViewerWindow._make_spin_box( 'spanField', self.on_span_changed )

        self.imageField = QAliasedPixmap()
        self.imageField.setObjectName( 'imageField' )

        vbox = QtWidgets.QVBoxLayout()
        vbox.setAlignment( QtCore.Qt.AlignVCenter )
        vbox.setContentsMargins( 20, 20, 20, 20 )
        vbox.addWidget( QtWidgets.QLabel( 'Offset' ))
        vbox.addWidget( self.offsetField )
        vbox.addWidget( QtWidgets.QLabel( 'Length' ))
        vbox.addWidget( self.lengthField )
        vbox.addWidget( QtWidgets.QLabel( 'Span' ))
        vbox.addWidget( self.spanField )

        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins( QtCore.QMargins() )
        hbox.addLayout( vbox )
        hbox.addWidget( self.imageField )

        self.setLayout( hbox )

    def _make_spin_box( name, slot ):
        field = QtWidgets.QSpinBox()
        field.setObjectName( name )
        field.valueChanged.connect( slot )
        return field
    
    def set_image( self, img ):
        if img: self.imageField.setPixmap( QtGui.QPixmap.fromImage( img ))
        else: self.imageField.clear()
        self.imageField.adjustSize()

    @property
    def range_limit( self ): return self._range_limit

    @range_limit.setter
    def range_limit( self, newval ):
        self._range_limit = newval
        self.offsetField.setMinimum( self._range_limit[0] )
        self.offsetField.setMaximum( self._range_limit[1] - self.lengthField.minimum())
        self.lengthField.setMinimum( self.spanField.minimum())
        self.lengthField.setMaximum( self._range_limit[1] - self.offsetField.value())
        self.on_offset_changed( self.offsetField.value())
        self.spanField.setValue( 320 )
        self.lengthField.setValue( 320*200 )

    def on_offset_changed( self, value ):
        self.lengthField.setMaximum( self._range_limit[1] - self.offsetField.value())
        self.fire_params_changed()
    
    def on_length_changed( self, value ):
        self.spanField.setMaximum( self.lengthField.value())
        self.fire_params_changed()

    def on_span_changed( self, value ):
        self.fire_params_changed()

    def fire_params_changed( self ):
        of, ln, sp = self.offsetField.value(), self.lengthField.value(), self.spanField.value()
        if sp > 0 and sp <= ln: self.paramsChanged.emit( of, ln, sp )
        else: self.set_image( None )

class MemViewerApp( QtWidgets.QApplication ):
    def __init__( self ):
        super().__init__( [] )
        self.setApplicationName( 'MemViewer' )
        with open( "style.qss", 'r' ) as f:
            self.setStyleSheet( f.read())

        self.window = MemViewerWindow()
        self.window.paramsChanged.connect( self.on_params_changed )
        self.window.show()

    def on_params_changed( self, offset, length, span ):
        self.offset, self.length, self.span = offset, length, span
        self.update_image()

    def load_file( self, path ):
        self.setApplicationName( "{} - MemViewer".format( os.path.basename( path )) )
        dumpext = os.path.splitext( os.path.basename( path ))[1]
        self.memory = self.readbin( path ) if dumpext.lower() == '.bin' else self.readtxt( path )
        self.window.range_limit = (0,len(self.memory))
        self.update_image()
    
    def update_image( self ):
        imgbytes = []
        for b in self.memory[self.offset:self.offset+self.length]:
            hi = b & 0xf0
            hi |= hi >> 4
            imgbytes.append( hi & 0xf )
            lo = b & 0x0f
            imgbytes.append( lo )
        
        padBytes = math.ceil(self.length/self.span) * self.span*2 - len(imgbytes)
        imgbytes += [0] * padBytes

        width, height = self.span*2, int( len(imgbytes) / (self.span*2))
        if width > 8192 or height > 8192:
            self.window.set_image( None )
            return

        print( "width, height = ", width, height )
        img = QtGui.QImage( bytes( imgbytes ), width, height, QtGui.QImage.Format_Indexed8 )

        img.setColorTable( pal_pcjr16color )
        self.window.set_image( img )
    
    def choose_file( self ):
        path, _ = QtWidgets.QFileDialog.getOpenFileName( self.window, "Open Memory Dump", "","Memory Dump Files (*.bin;*.txt)" )
        if path: self.load_file( path )

    def readtxt( self, path ):
        with open( path, 'r' ) as f:
            lines = [line.split()[1:] for line in f.readlines()]
            return [int(v, 16) for line in lines for v in line]

    def readbin( self, path ):
        with open( path, 'rb' ) as f:
            return f.read()


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description='Views a subset of a RAM dump as an image, applying the PCjr 16-color CGA palette to it.' )
    parser.add_argument( 'dumppath', nargs='?', default=None, help='Path to the RAM dump to process. Can be either binary or a DOSBOX debug text dump.' )
    args = parser.parse_args()

    app = MemViewerApp()
    if args.dumppath: app.load_file( args.dumppath )
    else: app.choose_file()

    sys.exit( app.exec_())
