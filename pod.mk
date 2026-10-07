# pod.mk: pod kit targets (use `make -f pod.mk <target>` or `include pod.mk` in the project Makefile)
# The test and test-strength commands are read from pod.yml (test_cmd, strength)
POD_PYTHON ?= python3

.PHONY: pod-setup pod-test pod-strength pod-check pod-metrics

pod-setup:
	@command -v $(POD_PYTHON) >/dev/null || { echo "python3 is required"; exit 1; }
	@command -v git >/dev/null || { echo "git is required"; exit 1; }
	@chmod +x scripts/*.sh
	@if [ -d plugins ]; then chmod +x plugins/*/hooks/*.sh; fi
	@mkdir -p .pod docs/changes
	@echo "Ready: set the emails in pod.yml to match each person's git config user.email"

pod-test:
	scripts/pod-test.sh

pod-strength:
	scripts/test-strength.sh

pod-check: pod-test pod-strength
	scripts/sync-codeowners.sh --check
	scripts/gate-check.sh --all

pod-metrics:
	@test -n "$(CHANGE)" || { echo "usage: make -f pod.mk pod-metrics CHANGE=docs/changes/001-slug"; exit 2; }
	scripts/metrics.sh $(CHANGE)
