NOSE = nosetests
NOSEFLAGS =

all: check

check:
	$(NOSE) $(NOSEFLAGS)

clean:
	rm -f *~ *.pyc
	rm -f smadata2/*~ smadata2/*.pyc
