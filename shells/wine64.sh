#!/bin/bash

# create wine 64 bit prefix

set -xe

WINEPREFIX="$HOME/.wine64" WINEARCH=win64 wine wineboot
