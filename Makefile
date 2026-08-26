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
	@test -d repos/cloud-platform-blueprint
	@test -d repos/terraform-modules
	@test -d repos/kubernetes-gitops
	@test -d repos/kubernetes-operations-toolkit
	@test -d repos/distributed-job-processor
	@test -d repos/career-workspace
	@test -d repos/agentic-ai-platform
	@test -d repos/system-design-notes
	@test -d repos/observability-lab
	@test -d repos/aws-cdk-examples
	@echo "meta-repo check passed"
