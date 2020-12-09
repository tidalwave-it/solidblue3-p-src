#!/bin/bash

PYTHON_VERSION=3.9.0

echo "================================ git clone asdf"
if [ ! -f "$WORKSPACE/.asdf" ]; then
  git clone https://github.com/asdf-vm/asdf.git "$WORKSPACE/.asdf" -b v0.8.0
fi

. "$WORKSPACE/.asdf/asdf.sh"
. "$WORKSPACE/.asdf/completions/asdf.bash"

ASDF=asdf
echo "================================ asdf plugin-add python"
"$ASDF" plugin-add python
echo "================================ asdf install python $PYTHON_VERSION"
"$ASDF" install python $PYTHON_VERSION
echo "================================ asdf local python $PYTHON_VERSION"
"$ASDF" local python $PYTHON_VERSION

echo "================================ pip install --user pipenv"
"$PYTHON_PATH" -m pip install --user pipenv
PIPENV="$HOME/.local/bin/pipenv"

make clean test lint

exit 0
