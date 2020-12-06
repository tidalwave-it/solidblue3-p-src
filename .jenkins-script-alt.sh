#!/bin/bash -x

PYTHON_VERSION=3.9.0

git clone https://github.com/asdf-vm/asdf.git "$WORKSPACE/.asdf" -b v0.8.0
export ASDF_DATA_DIR="$WORKSPACE/.asdf-data"
. "$WORKSPACE/.asdf/asdf.sh"
. "$WORKSPACE/.asdf/completions/asdf.bash"

ASDF="$WORKSPACE/.asdf/bin/asdf"
"$ASDF" plugin add python
"$ASDF" install python $PYTHON_VERSION
"$ASDF" local python $PYTHON_VERSION

PYTHON_PATH="$WORKSPACE/.asdf/installs/python/$PYTHON_VERSION/bin/python3"

"$PYTHON_PATH" -m pip install -t "$WORKSPACE/.local" pipenv
PIPENV="$WORKSPACE/.local/bin/pipenv"

if [ ! -f "$PIPENV" ]; then
    PIPENV="$HOME/Library/Python/3.9/bin/pipenv"
fi

# set -e
"$PIPENV" --python "$PYTHON_PATH" install
"$PIPENV" --python "$PYTHON_PATH" check
"$PIPENV" --python "$PYTHON_PATH" run coverage run -m unittest
"$PIPENV" --python "$PYTHON_PATH" run coverage html

set +e
"$PIPENV" --python "$PYTHON_PATH" run pylint *.py
echo