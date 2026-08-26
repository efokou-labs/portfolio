.PHONY: check help

help:
	@echo "check   Verify meta-repo docs and repo layout"

check:
	@test -f README.md
	@test -f ARCHITECTURE.md
	@test -f TRACKER.md
	@test -f CONTRIBUTING.md
	@test -f SECURITY.md
	@test -f LICENSE
	@test -f org-profile/profile/README.md
	@test -f repos/README.md
	@test -f repos/.gitkeep
	@echo "meta-repo check passed"
