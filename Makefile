test:
	nosetests --with-coverage --cover-package=gifshare \
		--cover-html --cover-html-dir=coverage-report \
		--cover-erase --cover-tests

clean:
	rm -rf *.egg-info build dist *.pyc README.html TODO.html

.PHONY: test clean
