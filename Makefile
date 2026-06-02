PYTHON ?= python

.PHONY: ingest merge-sources source-report clean prosody affect-train affect-infer stats viz thesis-report test

ingest:
	$(PYTHON) scripts/ingest/fetch_sources.py
	$(PYTHON) scripts/ingest/build_metadata.py

source-report:
	$(PYTHON) scripts/ingest/report_source_coverage.py

merge-sources:
	$(PYTHON) scripts/ingest/merge_source_registries.py

clean:
	$(PYTHON) scripts/clean/ocr_correct.py
	$(PYTHON) scripts/clean/segment_stanzas.py

prosody:
	$(PYTHON) scripts/prosody/run_scansion.py
	$(PYTHON) scripts/prosody/compute_latency.py
	$(PYTHON) scripts/prosody/compute_entropy.py

affect-train:
	$(PYTHON) scripts/affect/train_baseline.py
	$(PYTHON) scripts/affect/train_transformer.py

affect-infer:
	$(PYTHON) scripts/affect/infer_affect.py

stats:
	$(PYTHON) scripts/stats/run_cca.py
	$(PYTHON) scripts/stats/run_break_tests.py
	$(PYTHON) scripts/stats/run_robustness.py

viz:
	$(PYTHON) scripts/viz/build_figures.py

thesis-report:
	@echo "Thesis artifacts live in docs/thesis and docs/figures"

test:
	$(PYTHON) -m pytest -q
