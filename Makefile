NOSE = nosetests
PEP8 = pep8

NOSEFLAGS = --with-coverage --cover-package=smadata2

SCRIPTS = sma2-explore sma2mon \
	sma2-upload-to-pvoutputorg sma2-push-daily-to-pvoutput
PYFILES = $(SCRIPTS) $(wildcard smadata2/*.py)

all: check

check:
	$(NOSE) $(NOSEFLAGS) -a '!pvoutput.org'

checkall:
	$(NOSE) $(NOSEFLAGS)

pep8:
	$(PEP8) $(PYFILES)

clean:
	rm -f *~ *.pyc
	rm -f smadata2/*~ smadata2/*.pyc
	rm -f tests/*~ tests/*.pyc
	rm -f __testdb__*
	rm -f .coverage
