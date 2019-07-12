NOSE = nosetests3
PEP8 = python3-pep8
FLAKE8 = python3-flake8

NOSEFLAGS = --with-coverage --cover-package=smadata2

SCRIPTS = sma2-explore sma2mon \
	sma2-upload-to-pvoutputorg sma2-push-daily-to-pvoutput

SMADATA2_PYFILES = check.py config.py datetimeutil.py download.py \
	__init__.py pvoutputorg.py pvoutputuploader.py sma2mon.py \
	upload.py \
	test_config.py test_datetimeutil.py test_upload.py

DB_PYFILES = base.py __init__.py mock.py sqlite.py tests.py
INVERTER_PYFILES = base.py __init__.py mock.py smabluetooth.py

PYFILES = $(SCRIPTS) $(SMADATA2_PYFILES:%=smadata2/%) \
	$(DB_PYFILES:%=smadata2/db/%) \
	$(INVERTER_PYFILES:%=smadata2/inverter/%)

all: check

check:
	$(NOSE) $(NOSEFLAGS) -a '!pvoutput.org'

checkall:
	$(NOSE) $(NOSEFLAGS)

pep8:
	$(PEP8) $(PYFILES)

flake8:
	$(FLAKE8) $(PYFILES)

clean:
	rm -f *~ *.pyc
	rm -f smadata2/*~ smadata2/*.pyc
	rm -f tests/*~ tests/*.pyc
	rm -f __testdb__*
	rm -f .coverage
