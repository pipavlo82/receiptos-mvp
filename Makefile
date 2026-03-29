demo:
	python3 examples/demo_all.py

smoke:
	bash scripts/smoke.sh

test:
	PYTHONPATH=.. python3 -m pytest tests/test_smoke.py tests/test_reason_codes.py

replay-demo:
	python3 examples/api_replay_demo.py
