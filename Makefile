.PHONY: test

test:
	@command -v python3 >/dev/null 2>&1 && python3 -m unittest discover -s tests -v || python -m unittest discover -s tests -v
