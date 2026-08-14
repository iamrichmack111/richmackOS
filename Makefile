.PHONY: test smoke unit

test: smoke unit

smoke:
	./tests/smoke.sh

unit:
	python3 -m unittest discover -s tests -p 'test_*.py' -v
