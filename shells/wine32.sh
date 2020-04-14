#!/bin/bash

# create wine 32 bit prefix

set -xe

WINEPREFIX="$HOME/.wine32" WINEARCH=win32 wine wineboot
