# makeimg.ps1: Makes a 360 KB floppy image containing the contents of a particular directory, suitable for being
# served by mTCP's netserve.
#
# Usage: makeimg.ps1 path [imgpath]
#     path    the directory containing the contents of the image
#     imgpath the path to image file (default: path + ".img")
#
# Details: After creating the image with netdrive, WSL does all the rest since it can mount these images natively. We
# create a directory in /mnt, mount the image to it, copy in all the files into our source directory, then umount.

param (
    [string]$path = $(Read-Host "From what path?"),
    [string]$imgpath = $path.trimend( '\' ) + ".img"
)


if ( Test-Path $imgpath ) {
    if ( (Read-Host -Prompt "Disk image $imgpath already exists. Delete it? [y/n]" ) -eq 'y') {
        remove-item $imgpath
    }
    else {
        write-host "Quitting because image file already exists."
        exit
    }
}

./netdrive_windows_amd64.exe create floppy 360 $imgpath

$wslpath = (($path -replace "\\", "/") -replace ":", "")
$wslimgpath = (($imgpath -replace "\\", "/") -replace ":", "")
$imgname = Split-Path -leaf $imgpath

wsl mkdir -p "/mnt/$imgname"
wsl mount "$wslimgpath" "/mnt/$imgname"
write-host "Mounted $wslimgpath at /mnt/$imgname"
write-host "Copying contents of $wslpath to image..."
wsl cp -vr "$wslpath/*" "/mnt/$imgname"
wsl umount "/mnt/$imgname"
write-host "Unmounted $wslimgpath"