release:
	ACCELERATE_HIKARI=1 nox -s build-ext

debug:
	DEBUG_HIKARI=1 ACCELERATE_HIKARI=1 nox -s build-ext

clean:
	nox -s clean-ext

rebuild: clean release
debug-rebuild: clean debug

.PHONY: release debug clean rebuild debug-rebuild
