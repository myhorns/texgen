#!/bin/bash

# This script replaces the "." with "_" in filename.
# To run this script: 
#  Place this file in the same folder with target files, then execute the script.

for fname in *; do
  name="${fname%\.*}"
  extension="${fname#$name}"
  newname="${name//./_}"
  newfname="$newname""$extension"
  if [ "$fname" != "$newfname" ]; then
    echo mv "$fname" "$newfname"
    mv "$fname" "$newfname"
  fi
done
