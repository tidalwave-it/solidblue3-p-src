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

PYTHON_PATH="$HOME/.asdf/installs/python/$PYTHON_VERSION/bin/python3"

echo "================================ pip install --user pipenv"
"$PYTHON_PATH" -m pip install --user pipenv
PIPENV="$HOME/.local/bin/pipenv"

if [ ! -f "$PIPENV" ]; then
    PIPENV="$HOME/Library/Python/3.9/bin/pipenv"
    fi

set +e
echo "================================ pipenv install"
"$PIPENV" install
echo "================================ pipenv check"
"$PIPENV" check
echo "================================ pipenv run coverage run -m unittest"
"$PIPENV" run coverage run -m unittest
echo "================================ pipenv run coverage html"
"$PIPENV" run coverage html
echo "================================ pipenv run pylint *.py"
set -e
"$PIPENV" run pylint *.py
echo