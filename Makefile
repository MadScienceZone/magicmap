DIRLIST=docs man Test lib/RagnarokMUD
# translate %MAGICMAP_RELEASE% to version number

all: builddocs test

builddocs:
	(cd man && ../scripts/build_man_makefile pdf man? <Makefile.in >Makefile && $(MAKE))
	(cd docs && $(MAKE))

test:
	(cd Test && $(MAKE))

clean:
	for dir in $(DIRLIST); do (cd $${dir} && $(MAKE) clean); done

distclean: clean
	for dir in $(DIRLIST); do (cd $${dir} && $(MAKE) distclean); done
	rm -rf dist_bin

dist: distclean builddocs
	(mkdir -p dist_bin && cd bin && for file in *; do sed 's/^#@@REL@@//' < $$file > ../dist_bin/$$file; done)
	./setup.py sdist --formats=gztar,zip

