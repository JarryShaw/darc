include .env

export CODECOV_TOKEN
export PIPENV_VENV_IN_PROJECT=1

init:
	pipenv install --dev

test:
	pipenv run python src/test_darc.py

coverage:
	pipenv run coverage run src/test_darc.py
	pipenv run coverage html
	open htmlcov/index.html
	read
	rm -rf htmlcov
	rm .coverage

update:
	pipenv run pip install -U pip setuptools wheel
	pipenv update
	pipenv install --dev
	pipenv clean

dist: clean-pypi pypi-setup pypi-upload

pypi-setup:
	pipenv run python setup.py test sdist bdist_wheel

pypi-upload:
	twine check dist/* || true
	twine upload dist/* -r pypi --skip-existing
	twine upload dist/* -r pypitest --skip-existing

clean-pyc:
	find . -iname __pycache__ | xargs rm -rf
	find . -iname '*.pyc' | xargs rm -f

clean-misc: clean-pyc
	find . -iname .DS_Store | xargs rm -f

clean-pipenv:
	pipenv --rm

clean-pypi:
	mkdir -p dist sdist eggs wheels
	find dist -iname '*.egg' -exec mv {} eggs \;
	find dist -iname '*.whl' -exec mv {} wheels \;
	find dist -iname '*.tar.gz' -exec mv {} sdist \;
	rm -rf build dist *.egg-info
