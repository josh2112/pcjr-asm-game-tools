
import re, logging, more_itertools
import palettetools, drawingtools

def get_style( tag ):
    tokens = re.split( ':|;', tag['style'] )
    style = dict( zip( tokens[::2], tokens[1::2]))
    for key in ('fill','stroke'):
        if key in style:
            style[key] = None if style[key] == "none" else palettetools.parse_color( style[key] )
    return style

def get_transform( tag ):
    if not tag.has_attr( 'transform' ): return (0, 0)
    tokens = re.split( '\(|,|\)', tag['transform'] )
    if tokens[0] != 'translate':
        raise Exception( "Don't understand {}.transform: '{}'".format( tag.name, tag['transform'] ))
    else: return (float(tokens[1]), float(tokens[2]))

def parse_path( path ):
    digit_exp = '0123456789eE'
    comma_wsp = ', \t\n\r\f\v'
    cmd = 'MmZzLlHhVvCcSsQqTtAa'
    sign = '+-'
    exponent = 'eE'
    isfloat = False
    entity, entities = '', []
    for char in path:
        if char in digit_exp:
            entity += char
        elif char in comma_wsp and entity:
            entities.append( entity )
            isfloat = False
            entity = ''
        elif char in cmd:
            if entity:
                entities.append( entity )
                isfloat = False
                entity = ''
            if len(entities) > 1: yield entities[0], [float(x) for x in entities[1:]]
            elif len(entities) == 1: yield entities[0], None
            entities = []
            entities.append( char )
        elif char == '.':
            if isfloat:
                entities.append( entity )
                entity = '.'
            else:
                entity += '.'
                isfloat = True
        elif char in sign:
            if entity and entity[-1] not in exponent:
                entities.append( entity )
                isfloat = False
                entity = char
            else:
                entity += char
    if entity:
        entities.append( entity )
    if len(entities) > 1: yield entities[0], [float(x) for x in entities[1:]]
    elif len(entities) == 1: yield entities[0], None


class Polyline:
    def __init__( self, tag, offset ):
        self.tag = tag
        local_offset = get_transform( tag )
        self.offset = (offset[0]+local_offset[0], offset[1]+local_offset[1])
        self.lines = []

    @property
    def color( self ):
        style = get_style( self.tag )
        color = style['fill'] if 'fill' in style and style['fill'] else style['stroke']
        return color

    def fill_points( self, img_height ):
        desc = self.tag.find( "desc" )
        if desc:
            values = [float(v) for v in re.split( "\s*,\s*|\s+", desc.text.strip())]
            return list( zip( values[::2], [img_height - v for v in values[1::2]] ))
        else: return []

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
        for cmd, args in parse_path( tag['d'] ):
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
