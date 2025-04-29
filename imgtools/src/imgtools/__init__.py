"""Tools for working with raw interleaved color and depth images for fosquest
for the IBM PCjr.
"""

import os
import typing

import click
from PIL import Image

from .bin2img import data2img
from .palettetools import cga16, pil_palette


def change_ext(option_name: str, ext: str):
    return (
        os.path.splitext(
            click.get_current_context().params.get(option_name, None).name
        )[0]
        + ".bin"
    )


@click.group()
def cli():
    pass


@cli.command()
@click.option("-c", "--color", type=click.File("rb"), required=True)
@click.option("-d", "--depth", type=click.File("rb"), required=True)
@click.option(
    "-o",
    "--output",
    type=str,
    default=lambda: change_ext("color", "bin"),
    show_default="[color].bin",
    prompt=True,
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Overwrite the existing output file",
    default=False,
)
def pack(color: typing.IO, depth: typing.IO, output: str, force: bool):
    """Packs color and depth images into a packed image file saved as OUTPUT. COLOR and DEPTH must
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

    if os.path.exists(output) and not force:
        print(f"Error: Refusing to overwrite {output}. Pass -f to force.")

    with open(output, "wb") as f:
        f.write(
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


@cli.command()
@click.argument("icon", type=click.File("rb"))
@click.option(
    "-o",
    "--output",
    type=str,
    default=lambda: change_ext("icon", "bin"),
    show_default="[icon].bin",
    prompt=True,
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Overwrite the existing output file",
    default=False,
)
def packicon(icon: typing.IO, output: str, force: bool):
    if os.path.exists(output) and not force:
        print(f"Error: Refusing to overwrite {output}. Pass -f to force.")

    img = Image.open(icon)

    if len(img.palette.colors) != 16:
        raise Exception("Icon file must be a 16-color indexed PNG")

    with open(output, "wb") as f:
        d = list(img.getdata())
        f.write(bytes((a << 4) | (b & 0xF) for a, b in zip(d[::2], d[1::2])))


@cli.command()
@click.argument("input", type=click.File("rb"))
@click.argument("offset", type=str)
@click.argument("length", type=str)
def mem2bin(input: typing.IO, offset: str, length: str):
    """Extracts a memory region from a binary file. INPUT is the binary file, OFFSET is the offset to
    start extracting from, and LEN is the number of bytes to extract."""

    offset, length = int(offset, base=16), int(length, base=16)

    # KQ1 cracked version:
    # - 453c0: interleaved depth and color are seemingly being drawn at the same time?

    with open(input.name, "rb") as f:
        f.seek(offset)
        data = f.read(length)
        data2img(data, 160, length // 160)


def main() -> None:
    cli()
