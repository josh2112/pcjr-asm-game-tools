from PyQt5 import QtWidgets, QtGui, QtCore

class QAliasedPixmap( QtWidgets.QWidget ):
    def __init__( self, aspect, initial_scale, parent=None ):
        super().__init__( parent )
        self.scale, self.aspect = initial_scale, aspect
        sizePolicy = QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred )
        sizePolicy.setHeightForWidth( True )
        self.setSizePolicy( sizePolicy )

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
    
    def sizeHint( self ):
        width, height = self.pixmap.width() * self.scale, self.pixmap.height() * self.scale
        if self.aspect > width/height: width = self.aspect * height
        elif self.aspect < width/height: height = width/self.aspect
        return QtCore.QSize( width, height )
    
    def heightForWidth( self, width ):
        return width/self.aspect