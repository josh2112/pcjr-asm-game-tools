import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("filename")
path = parser.parse_args().filename

with open(path, "r") as fin:
    path = os.path.join(
        os.path.dirname(path), os.path.splitext(os.path.basename(path))[0] + ".bin"
    )
    with open(path, "wb") as fout:
        while line := fin.readline():
            line = line.split("   ")[1].strip().split()
            fout.write(bytes(int(b, 16) for b in line))
