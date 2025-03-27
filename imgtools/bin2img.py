from itertools import zip_longest

from palettetools import cga16, pil_palette
from PIL import Image


def to_rows(data, row_width):
    return zip_longest(*[iter(data)] * row_width)


def bitplanes2img(b1, b2, b3, b4, w, h):
    img = Image.new("P", (w, h))
    img.putpalette(pil_palette(cga16))

    img.putdata(
        [
            p
            for grp in zip(
                to_rows(b1, w),
                to_rows(b2, w),
                to_rows(b3, w),
                to_rows(b4, w),
            )
            for row in grp
            for p in row
        ]
    )

    img.show()


def videomem2img(region, w, h):
    bitplanes2img(
        region[:8000],
        region[0x2000 : (0x2000 + 8000)],
        region[0x4000 : (0x4000 + 8000)],
        region[0x6000 : (0x6000 + 8000)],
        w,
        h,
    )


def interleaved2img(region, w, h, mask):
    region = region[: w * h]

    img = Image.new("P", (w, h))
    img.putpalette(pil_palette(cga16))

    img.putdata([mask(b) for b in region])
    img.show()


with open("../scratchpad/memdump-castle.bin", "rb") as f:
    data = f.read()

# videomem2img(data[0x18000:], 160, 200)

# Color buffer
interleaved2img(data[0x3A080:], 160, 168, lambda b: b & 0xF)

# Depth buffer
interleaved2img(data[0x3A080:], 160, 168, lambda b: b >> 4)
