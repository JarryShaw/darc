.PHONY: logs docs

-include .env

export CODECOV_TOKEN
export PIPENV_VERBOSITY=-1
export PIPENV_VENV_IN_PROJECT=1

commit: github-commit gitlab-commit

reload:
	git pull
	$(MAKE) stop-healthcheck
	sudo docker-compose stop
	$(MAKE) uniq
	sudo docker-compose logs -t > logs/$(shell date +%Y-%m-%d-%H-%M-%S).log
	sudo docker-compose build
	sudo docker system prune --volumes -f
	sudo docker-compose up -d
	$(MAKE) healthcheck

uniq: uniq-requests uniq-selenium

uniq-requests:
	cat data/_queue_requests.txt | sort | uniq > data/_queue_requests.txt.uniq || true
	mv data/_queue_requests.txt.uniq data/_queue_requests.txt || true
	rm -f data/_queue_requests.txt.tmp

uniq-selenium:
	cat data/_queue_selenium.txt | sort | uniq > data/_queue_selenium.txt.uniq || true
	mv data/_queue_selenium.txt.uniq data/_queue_selenium.txt || true
	rm -f data/_queue_selenium.txt.tmp

logs:
	sudo docker-compose logs -tf

stop-healthcheck:
	sudo kill -2 $(shell ps axo pid=,command= | grep healthcheck.py | python3 -c "print(input().split()[0])") || true
	sudo kill -9 $(shell ps axo pid=,command= | grep healthcheck.py | python3 -c "print(input().split()[0])") || true

healthcheck:
	echo ------------- >> logs/healthcheck.log
	echo $(shell date) >> logs/healthcheck.log
	echo ------------- >> logs/healthcheck.log
	sudo nohup python3 extra/healthcheck.py >> logs/healthcheck.log &

github-commit:
	git add .
	git commit -S -a
	git push

gitlab-prep:
	find gitlab -depth 1 | grep -v '.git' | xargs rm -rf
	cp -rf \
	    darc \
		docker \
	    docs \
	    extra \
	    text \
		vendor \
	    .coveragerc \
	    .env \
	    .dockerignore \
	    .gitignore \
	    .travis.yml \
	    CODE_OF_CONDUCT.md \
	    CONTRIBUTING.md \
	    Dockerfile \
	    LICENSE \
	    MANIFEST.in \
	    Makefile \
	    Pipfile \
	    Pipfile.lock \
	    README.rst \
	    debug.dockerfile \
	    docker-compose.debug.yml \
	    docker-compose.yml \
	    requirements.debug.txt \
	    requirements.txt \
	    setup.cfg \
	    setup.py \
	    test_darc.py gitlab
	sed '/lfs/d' .gitattributes > gitlab/.gitattributes
	sed '/browser/d' gitlab/.gitignore > gitlab/.gitignore.tmp
	sed '/driver/d' gitlab/.gitignore.tmp > gitlab/.gitignore.tmp1
	sed '/tbb/d' gitlab/.gitignore.tmp1 > gitlab/.gitignore
	echo 'driver/*' >> gitlab/.gitignore
	echo '!driver/*.tar.gz' >> gitlab/.gitignore
	echo '!driver/*.zip' >> gitlab/.gitignore
	echo 'tbb/*' >> gitlab/.gitignore
	echo '!tbb/*.tar.gz' >> gitlab/.gitignore
	echo '!tbb/*.zip' >> gitlab/.gitignore
	rm gitlab/.gitignore.tmp*

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

docker-stop:
	if [ -f ${PATH_DATA}/darc.pid ]; then docker-compose exec darc kill -2 $(shell cat ${PATH_DATA}/darc.pid); fi
	docker-compose stop --timeout=60

docker-restart: docker-stop
	git pull
	docker-compose build
	docker system prune --volumes -f
	docker-compose up -d

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
	pipenv run python setup.py sdist bdist_wheel --python-tag='cp38'

pypi-upload:
	twine check dist/* || true
	twine upload dist/* -r pypi --skip-existing
	twine upload dist/* -r pypitest --skip-existing

clean-pyc:
	find . -iname __pycache__ | xargs rm -rf
	find . -iname '*.pyc' | xargs rm -f

clean-misc: clean-pyc
	if [ -d ${PATH_DATA} ]; then tar -cvzf archive/$(shell date '+%Y-%m-%d-%H-%M-%S').tar.gz ${PATH_DATA} && rm -rf ${PATH_DATA}; fi

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

docs:
	pipenv run $(MAKE) -C docs html
