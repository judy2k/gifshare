test:
	nosetests --with-coverage --cover-package=gifshare \
		--cover-html --cover-html-dir=coverage-report \
		--cover-erase --cover-tests

clean:
	rm -rf *.egg-info build \
	   	*.pyc gifshare/*.pyc gifshare/__pycache__ \
	   	README.html TODO.html 

distclean: clean
	rm -rf coverage-report dist

.PHONY: test clean distclean
