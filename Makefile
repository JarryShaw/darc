include .env

export CODECOV_TOKEN
export PIPENV_VERBOSITY=-1
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

docker-test: clean-misc
	docker build --tag darc --rm .
	docker run -it -v ${PATH_ROOT}/data:/darc/db darc 'https://www.sjtu.edu.cn'

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
	rm -rf ${PATH_DATA}

clean-pipenv:
	pipenv --rm

clean-pypi:
	mkdir -p dist sdist eggs wheels
	find dist -iname '*.egg' -exec mv {} eggs \;
	find dist -iname '*.whl' -exec mv {} wheels \;
	find dist -iname '*.tar.gz' -exec mv {} sdist \;
	rm -rf build dist *.egg-info

requirements:
	echo "# Python sources"                                                                            >  requirements.txt
	pipenv lock -r                           | head -3                                                 >> requirements.txt
	echo                                                                                               >> requirements.txt
	echo "# Python packages"                                                                           >> requirements.txt
	pipenv run python -m pip show pip        | grep Version | sed "s/Version: \(.*\)*/pip==\1/"        >> requirements.txt
	pipenv run python -m pip show setuptools | grep Version | sed "s/Version: \(.*\)*/setuptools==\1/" >> requirements.txt
	pipenv run python -m pip show wheel      | grep Version | sed "s/Version: \(.*\)*/wheel==\1/"      >> requirements.txt
	echo                                                                                               >> requirements.txt
	echo "# Python dependencies"                                                                       >> requirements.txt
	pipenv lock -r                           | tail +4                                                 >> requirements.txt
