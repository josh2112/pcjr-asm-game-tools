
parse_color = lambda hexstr: tuple( [int(hexstr[i:i+2],16) for i in (1, 3, 5)] )

def parse( palstr ):
    return [parse_color( line ) for line in (l for l in (l.strip() for l in palstr.split( '\n' )) if l)]

def pil_palette( pal ):
    return [c for rgb in pal for c in rgb]

def closest( rgb, pal ):
    errors = [ (c[0]-rgb[0])**2 + (c[1]-rgb[1])**2 + (c[2]-rgb[2])**2 for c in pal]
    return errors.index( min( errors ))

cga16 = parse( '''
    #000000 black
    #0000AA blue
    #00AA00 green
    #00AAAA cyan
    #AA0000 red
    #AA00AA magenta
    #AA5500 brown
    #AAAAAA light gray
    #555555 dark gray
    #5555FF light blue
    #55FF55 light green
    #55FFFF light cyan
    #FF5555 light red
    #FF55FF light magenta
    #FFFF55 yellow
    #FFFFFF white
      
''' )

if __name__ == '__main__':
    print( cga16 )