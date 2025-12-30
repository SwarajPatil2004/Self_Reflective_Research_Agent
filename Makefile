.PHONY: run run-i test-smoke

run:
	python -m src.cli "Explain LangGraph Reflexion loops and include citations."

run-i:
	python -m src.cli

smoke-test:
	python -m src.cli "Give a short, cautious brief on Pune weather trends. If research is unavailable, explain uncertainty."