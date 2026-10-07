include pod.mk

.PHONY: setup test strength check metrics

setup: pod-setup
test: pod-test
strength: pod-strength
check: pod-check
metrics: pod-metrics
