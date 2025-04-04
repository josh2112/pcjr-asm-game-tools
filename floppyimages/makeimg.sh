#!/bin/bash
# makeimg.sh: Makes a 360 KB floppy image containing the contents of a particular directory, suitable for being
# served by mTCP's netserve.
#
# Usage: ./makeimg.sh [-f] [-o|--output imgpath] filespath
#     filespath  the directory containing the contents of the image
#     imgpath    the image file to create (default: filespath.img)

set -o errexit -o pipefail -o noclobber -o nounset


FORCE=n OUTPUT=-

PARSED=$(getopt --options='fo:' --longoptions='force,output' --name "$0" -- "$@") || exit 2
eval set -- "$PARSED"

while true; do
    case "$1" in
        -f|--force)
            FORCE=y
            shift
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Programming error"
            exit 2
            ;;
    esac
done

if [[ $# -ne 1 ]]; then
    echo "$0: No image directory given!"
    exit 1
fi

FILESPATH="${1//\\//}"

if [[ "$OUTPUT" == "-" ]]; then
    OUTPUT="${FILESPATH%/}.img"
fi

IMGNAME="${OUTPUT##*/}"

if [[ -e "$OUTPUT" ]]; then
    if [[ "$FORCE" == 'y' ]]; then
        rm "$OUTPUT"
    else
        echo "Image file already exists. If you want to overwrite it, use -f."
        exit 1
    fi
fi

dd if=/dev/zero of="$OUTPUT" bs=1K count=360
mkfs.fat -F12 "$OUTPUT"

sudo mkdir -p "/mnt/$IMGNAME"

sudo mount "$OUTPUT" "/mnt/$IMGNAME"

sudo cp -vr "$FILESPATH"/* "/mnt/$IMGNAME"

sudo umount "/mnt/$IMGNAME"

echo "Created $OUTPUT"