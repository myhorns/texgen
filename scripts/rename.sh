#!/bin/bash

# This script replaces the "." with "_" in filename.
# To run this script: 
#  Place this file in the same folder with target files, then execute the script.

paddingLength=2


for fname in *; do
  name="${fname%\.*}"
  extension="${fname#$name}"
  chapter="${name%\.*}"
  slideIdx="${name#$chapter.}"

  # make the file extension lower-case
  extension=$(echo "$extension" | tr '[:upper:]' '[:lower:]')

  # the slideIdx could take value "08" or "09".
  # any number literal starting with '0' but having no 'x' at the 2nd 
  # place is interpreted as octal value
  slideIdx="${slideIdx#0}"

  ## this block only does "." --> "_"
  #newname="${name//./_}"
  #newfname="$newname""$extension"
  #if [ "$fname" != "$newfname" ]; then
  #  echo mv "$fname" "$newfname"
  #  # mv "$fname" "$newfname"
  #fi

  ## In addition to "." --> "_" conversion, this 
  ## block also pads 0 to slide index
  if [ "$extension" != ".sh" ]; then
    newfname=$(printf ${chapter}_%0${paddingLength}d${extension} ${slideIdx})
    echo mv "$fname" "$newfname"
    mv "$fname" "$newfname"
  fi

done
