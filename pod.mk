# pod.mk: คำสั่งของ pod kit (ใช้ได้ทั้ง `make -f pod.mk <target>` และ `include pod.mk` ใน Makefile ของ project)
# คำสั่ง test และ test-strength อ่านจาก pod.yml (test_cmd, strength)
POD_PYTHON ?= python3

.PHONY: pod-setup pod-test pod-strength pod-check pod-metrics

pod-setup:
	@command -v $(POD_PYTHON) >/dev/null || { echo "ต้องติดตั้ง python3"; exit 1; }
	@command -v git >/dev/null || { echo "ต้องติดตั้ง git"; exit 1; }
	@chmod +x scripts/*.sh
	@if [ -d plugins ]; then chmod +x plugins/*/hooks/*.sh; fi
	@mkdir -p .pod docs/changes
	@echo "พร้อมใช้งาน: แก้อีเมลใน pod.yml ให้ตรงกับ git config user.email ของแต่ละคน"

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
