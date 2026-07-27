#!/bin/sh
# extractimg.sh: Extracts a floppy image containing the contents of a particular directory, suitable for being
# served by mTCP's netserve.
#
# Usage: ./extractimg.sh [-f|--force] [-o|--output destdir] imgpath
#   imgpath the image file to extract
#   destdir the destination directory (default: imgpath with extension removed)

set -e  # errexit
set -C  # noclobber
set -u  # nounset

FORCE=n
OUTPUT=-

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

if [ "$#" -ne 1 ]; then
  echo "$0: No disk image name given!"
  exit 1
fi

IMGPATH=$(echo "$1" | tr '\\' '/')
IMGNAME="${IMGPATH##*/}"

# Use the image name without extension if no output file given
if [ "$OUTPUT" = "-" ]; then
  # Strip the .img extension using POSIX suffix removal
  OUTPUT="${IMGPATH%.img}"
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

# Handle existing destination directory
if [ -e "$OUTPUT" ]; then
  if [ "$FORCE" = 'y' ]; then
    # Temporarily bypass -C (noclobber) to allow removal
    set +C
    rm -r "$OUTPUT"
    set -C
  else
    echo "Output directory already exists. If you want to overwrite it, use -f."
    exit 1
  fi
fi

mkdir -p "$OUTPUT"
sudo mkdir -p "/mnt/$IMGNAME"

# Mount the target floppy image
sudo mount "$IMGPATH" "/mnt/$IMGNAME"
echo "Mounted $IMGPATH at /mnt/$IMGNAME"

echo "Copying contents of image to $OUTPUT..."
sudo cp -r "/mnt/$IMGNAME"/* "$OUTPUT"
