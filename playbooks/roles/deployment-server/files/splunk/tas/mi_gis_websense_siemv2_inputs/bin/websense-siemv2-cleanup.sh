#!/bin/bash

SRC_PATH=/opt/websense-siemv2/logs/
DEST_PATH=/opt/websense-siemv2/logs-processed/
DOWNLOADING_FLAG=".downloading"
FILES=$SRC_PATH"*.csv.gz"
for f in $FILES
    do
    if [[ ! -d "$f"$DOWNLOADING_FLAG ]]; then
        STEM=$(basename "${f}" .gz)
        gunzip "$f";
        sed -i '1 s/ //g' "${f%.*}"
        sed -i 's/"None"//g' "${f%.*}"
        mv $SRC_PATH"${STEM}" $DEST_PATH"${STEM}"
    fi
done