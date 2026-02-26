PYTHON ?= python
ARGS ?=

.PHONY: all run clean

all:
	$(PYTHON) -m build

run:
	$(PYTHON) -m gex $(ARGS)

clean:
	rm -rf dist/ build/ src/*.egg-info src/gex/__pycache__ __pycache__ output.png
