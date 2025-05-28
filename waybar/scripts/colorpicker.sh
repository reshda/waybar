#!/usr/bin/env bash

image=/tmp/color.png

# select the color
color=`hyprpicker`

# if the user cancels the selection, exit
if [ -z "$color" ]; then
		exit 1
fi

# copy it to the clipboard
wl-copy $color

# create a 500x500 image with the selected color as background
magick -size 500x500 xc:transparent -fill xc:$color -stroke $color -strokewidth 1 -draw "roundrectangle 100,100 399,399 30,30" $image


# show a notification with the color and the image as icon
notify-send -i $image "Color" "Color: $color"

# remove the image
rm $image
