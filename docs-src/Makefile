# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = .

ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean doc

default: doc

doc:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/../docs
	@echo
	@echo "Build finished. The HTML pages are in /docs."

clean:
	-rm -rf $(BUILDDIR)/html

