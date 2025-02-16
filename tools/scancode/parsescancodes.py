# Using scan codes pulled from https://stanislavs.org/helppc/scan_codes.html

import csv

with open( 'int16scancodes.csv' ) as f:
    r = csv.reader( f )
    lines = [[c.strip() for c in row] for row in r][1:]

for line in lines:
    values = ', '.join( '-1' if not c else f'0x{c}' for c in line[1:])
    print( f"            {{ Key.{line[0]}, new( {values} ) }},")
    