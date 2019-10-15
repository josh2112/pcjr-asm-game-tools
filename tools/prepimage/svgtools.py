
import re
import palettetools

def get_style( tag ):
    tokens = re.split( ':|;', tag['style'] )
    style = dict( zip( tokens[::2], tokens[1::2]))
    for key in ('fill','stroke'):
        if key in style:
            style[key] = None if style[key] == "none" else palettetools.parse_color( style[key] )
    return style

def get_transform( tag ):
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
            if len(entities) > 1: yield [entities[0]] + [float(x) for x in entities[1:]]
            elif len(entities) == 1: yield entities
            entities = []
            entities.append( char )
        elif char == '.':
            if isfloat:
                yield entity
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
    if len(entities) > 1: yield [entities[0]] + [float(x) for x in entities[1:]]
    elif len(entities) == 1: yield entities