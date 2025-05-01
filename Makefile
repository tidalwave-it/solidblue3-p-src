export PATH := $(PATH):/root/.local/bin
export LANG := C.UTF-8

.PHONY:	prepare clean check test lint lock

prepare:
	python -m pip install --user pipenv

prepare-travis:
	python -m pip install pipenv
	pipenv install

lock:
	pipenv lock

clean:
	rm -rf build __pycache__

check:
	echo "================================ Check"
	-pipenv check

test: check
	echo "================================ Coverage"
	pipenv run coverage run -m unittest
	pipenv run coverage html -i

lint: check
	echo "================================ Pylint"
	mkdir -p build/pylint
	pipenv run pylint *.py | tee build/pylint/report.txt
