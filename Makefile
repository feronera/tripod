PYTHON ?= python3

.PHONY: setup test check metrics

setup:
	@command -v $(PYTHON) >/dev/null || { echo "ต้องติดตั้ง python3"; exit 1; }
	@command -v git >/dev/null || { echo "ต้องติดตั้ง git"; exit 1; }
	@chmod +x scripts/*.sh plugins/*/hooks/*.sh
	@mkdir -p .pod docs/changes
	@echo "พร้อมใช้งาน: แก้อีเมลใน pod.yml ให้ตรงกับ git config user.email ของแต่ละคน"

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

check: test
	scripts/gate-check.sh --all

metrics:
	@test -n "$(CHANGE)" || { echo "usage: make metrics CHANGE=docs/changes/001-slug"; exit 2; }
	scripts/metrics.sh $(CHANGE)
