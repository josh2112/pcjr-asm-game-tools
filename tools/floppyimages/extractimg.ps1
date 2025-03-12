# extractimg.ps1: Extracts the contents of a floppy image file into a directory.
#
# Usage: extractimg.ps1 imgpath [path]
#     imgpath the image file to extract
#     path    the destination directory (default: imgpath with extension removed)
#
# Details: WSL does all the work since it can mount these images natively. We create a directory
# in /mnt, mount the image to it, copy out all the files into our destination directory, then umount.

param (
    [string]$imgpath = $(Read-Host "Image file path?"),
    [string]$path = $imgpath.Substring(0, $imgpath.LastIndexOf( '.' ))
)

if ( Test-Path $path ) {
    if ( (Read-Host -Prompt "Output directory $path already exists. Write into it? [y/n]" ) -ne 'y') {
        write-host "Not going to modify existing directory."
        exit
    }
}
else {
    new-item -ItemType Directory $path | Out-Null
}

$wslpath = (($path -replace "\\", "/") -replace ":", "")
$wslimgpath = (($imgpath -replace "\\", "/") -replace ":", "")
$imgname = (Split-Path -leaf $imgpath)

wsl mkdir -p "/mnt/$imgname"
wsl mount "$wslimgpath" "/mnt/$imgname"
write-host "Mounted $wslimgpath at /mnt/$imgname"
write-host "Copying contents of image to $wslpath..."
wsl cp -vr "/mnt/$imgname/*" "$wslpath"
wsl umount "/mnt/$imgname"
write-host "Unmounted $wslimgpath"