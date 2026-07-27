#!/bin/sh
# makeimg.sh: Makes a 360 KB floppy image containing the contents of a particular directory, suitable for being
# served by mTCP's netserve.
#
# Usage: ./makeimg.sh [-f] [-o|--output imgpath] filespath
#   filespath the directory containing the contents of the image
#   imgpath the image file to create (default: filespath.img)

set -e  # errexit
set -C  # noclobber
set -u  # nounset

FORCE=n
OUTPUT=-

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

if [ "$#" -ne 1 ]; then
  echo "$0: No image directory given!"
  exit 1
fi

FILESPATH=$(echo "$1" | tr '\\' '/')

# Use [filespath].img if no output file given
if [ "$OUTPUT" = "-" ]; then
  CLEAN_PATH="${FILESPATH%/}"
  OUTPUT="${CLEAN_PATH}.img"
fi

IMGNAME="${OUTPUT##*/}"

if [ -e "$OUTPUT" ]; then
  if [ "$FORCE" = 'y' ]; then
    # Bypass -C (noclobber) restrictions when forcefully replacing an existing file
    set +C
    rm "$OUTPUT"
    set -C
  else
    echo "Image file already exists. If you want to overwrite it, use -f."
    exit 1
  fi
fi

cleanup() {
  EXIT_STATUS=$?
  
  echo "Cleaning up..."
  
  if mount | grep -q "on /mnt/$IMGNAME "; then
    sudo umount "/mnt/$IMGNAME"
  fi
  
  if [ -d "/mnt/$IMGNAME" ]; then
    sudo rm -rf "/mnt/$IMGNAME"
  fi

  exit $EXIT_STATUS
}

trap cleanup EXIT INT TERM

dd if=/dev/zero of="$OUTPUT" bs=1k count=360
mkfs.fat -F12 "$OUTPUT"

sudo mkdir -p "/mnt/$IMGNAME"
sudo mount "$OUTPUT" "/mnt/$IMGNAME"
sudo cp -r "$FILESPATH"/* "/mnt/$IMGNAME"

echo "Created $OUTPUT"
