#!/bin/bash

#find . -iname \*.jpg -exec convert -verbose -quality 80 -resize 1600\> "{}" "FOO_FOLDER/{}" \;

# Some PNGs have an alpha channel. The alpha channel may get lost if the image is convereted to JPEG.
## Convert all PNGs to JPEGs
#mogrify -format jpg *.png 
## Delete all PNGs
#rm *.png
#rm *.PNG

# max width
WIDTH=1280

# max height
HEIGHT=720

#MAXPIXELS=1920000 # 1600x1200

#resize png or jpg to either height or width, keeps proportions using imagemagick
find . -iname '*.jpg' -exec convert \{} -verbose -quality 82 -resize $HEIGHTx$WIDTH\> \{} \;
find . -iname '*.png' -exec convert \{} -verbose -resize $HEIGHTx$WIDTH\> \{} \;

#find . -iname '*.jpg' -exec convert \{} -verbose -resize $MAXPIXELS@ \{} \;
#find . -iname '*.png' -exec convert \{} -verbose -resize $MAXPIXELS@ \{} \;