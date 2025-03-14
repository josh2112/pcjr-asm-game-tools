"""Tools for working with raw interleaved color and depth images for fosquest
for the IBM PCjr.

pack: Given 2 PNG images (color and depth), outputs a raw interleaved ('packed')
file with extension .bin, suitable for loading into the fosquest background buffer.

unpack: Given a packed image and an output name, unpacks the image and saves the
resulting color and depth images as [name].color.png and [name].depth.png
"""

import click

from PIL import Image
import typing
from imgtools.palettetools import pil_palette, cga16


@click.group()
def cli():
    pass


@cli.command()
@click.argument("color", type=click.File("rb"))
@click.argument("depth", type=click.File("rb"))
@click.argument("output", type=click.File("wb"))
def pack(color: typing.IO, depth: typing.IO, output: typing.IO):
    """Packs COLOR and DEPTH into a packed image file saved as OUTPUT."""

    if len(color) != len(depth):
        raise "COLOR and DEPTH files must be the same size"

    cbytes, dbytes = color.read(), depth.read()

    packed = [cbytes[i] | (dbytes[i] << 4) for i in range(len(cbytes))]

    w = 320
    h = len(packed) // w

    img = Image.new("P", (w, h))
    img.putpalette(pil_palette(cga16))
    img.putdata(packed)

    img.show()


@cli.command()
@click.argument("input", type=click.File("rb"))
@click.argument("output", type=str)
def unpack(input: typing.IO, output: str):
    """Unpacks the packed (depth and color) image INPUT into OUTPUT.depth.png and OUTPUT.color.png."""

    packed = input.read()
    w = 160
    h = len(packed) // w

    depth = Image.new("P", (w, h))
    depth.putpalette(pil_palette(cga16))
    depth.putdata([(b >> 4) for b in packed])

    color = Image.new("P", (w, h))
    color.putpalette(pil_palette(cga16))
    color.putdata([(b & 0xF) for b in packed])

    depth.save(f"{output}.depth.png")
    color.save(f"{output}.color.png")


if __name__ == "__main__":
    cli()
