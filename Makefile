NOSE = nosetests
NOSEFLAGS = --with-coverage --cover-package=smadata2

all: check

check:
	$(NOSE) $(NOSEFLAGS)

clean:
	rm -f *~ *.pyc
	rm -f smadata2/*~ smadata2/*.pyc
	rm -f tests/*~ tests/*.pyc
	rm -f .coverage
