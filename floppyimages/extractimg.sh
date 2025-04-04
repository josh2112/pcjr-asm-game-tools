#!/bin/bash
# makeimg.sh: Makes a 360 KB floppy image containing the contents of a particular directory, suitable for being
# served by mTCP's netserve.
#
# Usage: ./extractimg.sh [-o|--output destdir] imgpath
#     imgpath  the image file to extract
#     destdir  the destination directory (default: imgpath with extension removed )

set -o errexit -o pipefail -o noclobber -o nounset

FORCE=n OUTPUT=-

PARSED=$(getopt --options='fo:' --longoptions='force,output:' --name "$0" -- "$@") || exit 2
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
    echo "$0: No disk image name given!"
    exit 1
fi

IMGPATH="${1//\\//}"
IMGNAME="${IMGPATH##*/}"

if [[ "$OUTPUT" == "-" ]]; then
    OUTPUT="${IMGPATH%.img}"
fi


if [[ -e "$OUTPUT" ]]; then
    if [[ "$FORCE" == 'y' ]]; then
        rm -r "$OUTPUT"
    else
        echo "Output directory already exists. If you want to overwrite it, use -f."
        exit 1
    fi
fi

mkdir -p "$OUTPUT"

sudo mkdir -p "/mnt/$IMGNAME"

sudo mount $IMGPATH "/mnt/$IMGNAME"
echo "Mounted $IMGPATH at /mnt/$IMGNAME"

echo "Copying contents of image to $OUTPUT..."
sudo cp -vr "/mnt/$IMGNAME"/* "$OUTPUT"

sudo umount "/mnt/$IMGNAME"
echo "Unmounted $IMGPATH"