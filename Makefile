PYTHON ?= python3

.PHONY: help test syntax metrics hotspots json quality status

help:
	@echo "RichmackOS Development"
	@echo
	@echo "  make test       Run unit/regression tests"
	@echo "  make syntax     Validate Python and shell syntax"
	@echo "  make metrics    Show engineering metrics"
	@echo "  make hotspots   Show complexity hotspots"
	@echo "  make json       Validate metrics JSON"
	@echo "  make quality    Run full quality gate"
	@echo "  make status     Show Git status"

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

syntax:
	$(PYTHON) -m py_compile richmack_metrics/*.py scripts/richmack-metrics tests/*.py
	bash -n bin/richmack

metrics:
	$(PYTHON) scripts/richmack-metrics

hotspots:
	$(PYTHON) scripts/richmack-metrics hotspots

json:
	$(PYTHON) scripts/richmack-metrics --json | $(PYTHON) -m json.tool >/dev/null
	@echo "PASS: metrics JSON"

quality: syntax test json metrics
	@echo
	@echo "PASS: RichmackOS quality gate"

status:
	git status --short --branch
