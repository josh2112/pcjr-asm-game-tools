import json
import os
import struct

from PIL import Image, ImageDraw, ImagePalette

AGIDIR = "F:/source/asm-8088/programs/KQ1"


class Picture:
    def __init__(self):
        self.pic_color, self.pri_color = 15, 4
        self.pic_draw, self.pri_draw = True, True
        self.xy = (0, 0)
        self.img = Image.new("P", (160, 168), self.pic_color)
        self.draw = ImageDraw.Draw(self.img)
        with open("cga16.pal", "r") as f:
            self.img.putpalette(ImagePalette.ImagePalette("P", json.loads(f.read())))

    def move(self, x, y):
        self.xy = (x, y)
        pass

    def line(self, x, y):
        p1 = (x, y)
        if self.pic_draw:
            self.draw.line((self.xy, p1), fill=self.pic_color)
        self.xy = p1

    def line_xy(self, is_y, d):
        p1 = (self.xy[0] if is_y else d, d if is_y else self.xy[1])
        if self.pic_draw:
            self.draw.line((self.xy, p1), fill=self.pic_color)
        self.xy = p1

    def line_rel(self, dx, dy):
        p1 = (self.xy[0] + dx, self.xy[1] + dy)
        if self.pic_draw:
            self.draw.line((self.xy, p1), fill=self.pic_color)
        self.xy = p1

    def fill(self, x, y):
        if self.pic_draw:
            ImageDraw.floodfill(self.img, (x, y), value=self.pic_color)
        self.xy = (x, y)
        pass


def parse_dir(filename):
    with open(os.path.join(AGIDIR, filename), "rb") as f:
        d = f.read()
        for r in [d[i : i + 3] for i in range(0, len(d), 3) if d[i] != 0xFF]:
            volnum = r[0] >> 4
            offset = (r[0] & 0xF) << 16 | r[1] << 8 | r[2]
            yield volnum, offset


def load(r):
    with open(os.path.join(AGIDIR, f"vol.{r[0]}"), "rb") as f:
        f.seek(r[1])
        if struct.unpack(">H", f.read(2)) != (0x1234,):
            raise Exception("Invalid file format")
        _, length = struct.unpack("<BH", f.read(3))
        return f.read(length)


def draw(vec):
    pic = Picture()
    c = 0
    while c < len(vec):
        cmd = vec[c]
        c += 1
        match cmd:
            case 0xF0:  # Pic color
                pic.pic_color = vec[c]
                pic.pic_draw = True
                c += 1
            case 0xF1:  # Disable pic
                pic.pic_draw = False
            case 0xF2:  # Pri color
                pic.pri_color = vec[c]
                pic.pri_draw = True
                c += 1
            case 0xF3:  # Disable pri
                pic.pri_draw = False
            case 0xF4 | 0xF5:  # X/Y corner
                pic.move(vec[c], vec[c + 1])
                c += 2
                is_y = cmd == 0xF4
                while (n := vec[c]) < 0xF0:
                    pic.line_xy(is_y, n)
                    is_y = not is_y
                    c += 1
            case 0xF6:  # Line
                pic.move(vec[c], vec[c + 1])
                c += 2
                while (x := vec[c]) < 0xF0:
                    pic.line(x, vec[c + 1])
                    c += 2
            case 0xF7:  # Relative line
                pic.move(vec[c], vec[c + 1])
                c += 2
                while (r := vec[c]) < 0xF0:
                    dx = ((r & 0b01110000) >> 4) * (-1 if (r & 0x80) else 1)
                    dy = (r & 0b00000111) * (-1 if (r & 0x08) else 1)
                    pic.line_rel(dx, dy)
                    c += 1
            case 0xF8:  # Fill
                while (x := vec[c]) < 0xF0:
                    pic.fill(x, vec[c + 1])
                    c += 2
            case 0xFF:
                return pic
            case _:
                raise Exception(f"Unknown command {cmd:02X}h at idx {c - 1}")


def main():
    os.makedirs("tmp", exist_ok=True)
    for i, r in enumerate(parse_dir("picdir")):
        print(f"Rendering room {i}...")
        drawing = draw(load(r))
        drawing.img.save(os.path.join("tmp", f"{i}.png"))


if __name__ == "__main__":
    main()
