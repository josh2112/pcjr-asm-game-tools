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
@click.option("-c", "--color", type=click.File("rb"), required=True)
@click.option("-d", "--depth", type=click.File("rb"), required=True)
@click.argument("output", type=click.File("wb"))
def pack(color: typing.IO, depth: typing.IO, output: typing.IO):
    """Packs color and depth images into a packed image file saved as OUTPUT. COLOR and DEPTH mus
    be indexed PNG files using the 16-color CGA palette. OUTPUT will be a binary file, one byte per
    pixel, with depth as the upper 4 bits and color as the lower 4 bits."""

    cimg, dimg = Image.open(color), Image.open(depth)

    if cimg.size != dimg.size:
        raise "Color and depth files must be the same size"

    if (
        cimg.mode != dimg.mode
        or cimg.palette.colors != dimg.palette.colors
        or len(cimg.palette.colors) != 16
    ):
        raise "Color and depth files must both be 16-color indexed PNGs"

    output.write(
        bytes(
            (d << 4) | (c & 0xF)
            for d, c in zip(list(dimg.getdata()), list(cimg.getdata()))
        )
    )


@cli.command()
@click.argument("input", type=click.File("rb"))
@click.argument("output", type=str)
def unpack(input: typing.IO, output: str):
    """Unpacks the packed (depth and color) image INPUT and saves the resulting depth and color
    images as 16-color indexed (CGA palette) PNG images OUTPUT.depth.png and OUTPUT.color.png."""

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
