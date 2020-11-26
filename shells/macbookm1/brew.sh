#!/bin/bash

# install brew on apple silicon

if ! which brew >/dev/null; then
  arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  set -xe
  exec arch -x86_64 brew "$@"
fi

