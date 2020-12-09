PIPENV="$(HOME)/.local/bin/pipenv"

prepare:
	python -m pip install --user pipenv

clean:
	rm -rf build __pycache__

check:
	echo "================================ Check"
	$(PIPENV) check

test: check
	echo "================================ Coverage"
	$(PIPENV) run coverage run -m unittest
	$(PIPENV) run coverage html -i

lint: check
	echo "================================ Pylint"
	mkdir -p build/pylint
	$(PIPENV) run pylint *.py | tee build/pylint/report.txt



