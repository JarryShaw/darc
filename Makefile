include .env

export CODECOV_TOKEN
export PIPENV_VERBOSITY=-1
export PIPENV_VENV_IN_PROJECT=1

commit: github-commit gitlab-commit

github-commit:
	git add .
	git commit -S -a
	git push

gitlab-prep:
	find gitlab -depth 1 | grep -v '.git' | xargs rm -rf
	cp -rf \
	    browser \
	    docker \
	    driver \
	    extra \
	    tbb \
	    text \
	    .coveragerc \
	    .env \
	    .dockerignore \
	    .gitattributes \
	    .gitignore \
	    .travis.yml \
	    CODE_OF_CONDUCT.md \
	    CONTRIBUTING.md \
	    LICENSE \
	    MANIFEST.in \
	    Makefile \
	    Pipfile \
	    Pipfile.lock \
	    README.md \
	    darc.py \
		requirements.debug.txt \
	    requirements.txt \
	    setup.cfg \
	    setup.py gitlab
	echo 'driver/*' >> gitlab/.gitignore
	echo '!driver/*.tar.gz' >> gitlab/.gitignore
	echo 'tbb/*' >> gitlab/.gitignore
	echo '!tbb/*.tar.gz' >> gitlab/.gitignore
	sed '/browser/d' gitlab/.gitignore.tmp > gitlab/.gitignore
	sed '/driver/d' gitlab/.gitignore > gitlab/.gitignore.tmp
	sed '/tbb/d' gitlab/.gitignore.tmp > gitlab/.gitignore
	rm gitlab/.gitignore.tmp

gitlab-commit-wrapper:
	git add .
	git commit -S -am"$$(cd .. && git log -1 --pretty=%B)"
	git push

gitlab-commit: gitlab-prep
	$(MAKE) -C gitlab gitlab-commit-wrapper

init:
	pipenv install --dev

test:
	pipenv run python src/test_darc.py

clean: clean-misc clean-docker

coverage:
	pipenv run coverage run src/test_darc.py
	pipenv run coverage html
	open htmlcov/index.html
	read
	rm -rf htmlcov
	rm .coverage

docker-setup:
	sudo echo 'DOCKER_OPTS="$DOCKER_OPTS --registry-mirror=https://docker.mirrors.ustc.edu.cn"' >> /etc/default/docker
	sudo service docker restart

docker-test: clean-misc
	docker build --file debug.dockerfile --tag darc --rm .
	clear
	docker run -it -v ${PATH_ROOT}/data:/darc/db darc 'https://www.sjtu.edu.cn'

compose-test: clean-misc clean-docker
	docker-compose --file docker-compose.debug.yml build
	clear
	docker-compose --file docker-compose.debug.yml up

update:
	pipenv run pip install -U pip setuptools wheel
	pipenv update
	pipenv install --dev
	pipenv clean
	$(MAKE) requirements requirements-debug

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

clean-docker:
	docker system prune --volumes -f

clean-pipenv:
	pipenv --rm

clean-pypi:
	mkdir -p dist sdist eggs wheels
	find dist -iname '*.egg' -exec mv {} eggs \;
	find dist -iname '*.whl' -exec mv {} wheels \;
	find dist -iname '*.tar.gz' -exec mv {} sdist \;
	rm -rf build dist *.egg-info

requirements:
	echo "# Python packages"                                                                           >  requirements.txt
	pipenv run python -m pip show pip        | grep Version | sed "s/Version: \(.*\)*/pip==\1/"        >> requirements.txt
	pipenv run python -m pip show setuptools | grep Version | sed "s/Version: \(.*\)*/setuptools==\1/" >> requirements.txt
	pipenv run python -m pip show wheel      | grep Version | sed "s/Version: \(.*\)*/wheel==\1/"      >> requirements.txt
	echo                                                                                               >> requirements.txt
	echo "# Python dependencies"                                                                       >> requirements.txt
	pipenv lock -r                           | tail +4                                                 >> requirements.txt

requirements-debug:
	echo "# Python sources"                                                                            >  requirements.debug.txt
	pipenv lock -r                           | head -3                                                 >> requirements.debug.txt
	echo                                                                                               >> requirements.debug.txt
	echo "# Python packages"                                                                           >> requirements.debug.txt
	pipenv run python -m pip show pip        | grep Version | sed "s/Version: \(.*\)*/pip==\1/"        >> requirements.debug.txt
	pipenv run python -m pip show setuptools | grep Version | sed "s/Version: \(.*\)*/setuptools==\1/" >> requirements.debug.txt
	pipenv run python -m pip show wheel      | grep Version | sed "s/Version: \(.*\)*/wheel==\1/"      >> requirements.debug.txt
	echo                                                                                               >> requirements.debug.txt
	echo "# Python dependencies"                                                                       >> requirements.debug.txt
	pipenv lock -r                           | tail +4                                                 >> requirements.debug.txt

push-github:
	git config remote.origin.url https://github.com/JarryShaw/darc.git
	git push

push-gitlab:
	git config remote.origin.url git@gitlab.sjtu.edu.cn:xiaojiawei/darc.git
	git push
