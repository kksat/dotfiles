export TESTFOLDER=./test/
export STOWCOMMAND=stow --dotfiles --stow .
export BREW=brew

.PHONY: help
help: ## Prints help for targets with comments
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: stow
stow: ## Stow all dotfiles
	${STOWCOMMAND} --target=$$HOME

.PHONY: adopt
adopt: ## Adopt all dotfiles
	${STOWCOMMAND} --adopt

.PHONY: simulate
simulate: ## Simulate stow all dotfiles
	${STOWCOMMAND} --simulate --verbose=2

.PHONY: test
test:  # Test stow - put all in ./test instread of ~
	${STOWCOMMAND} --target="${TESTFOLDER}"

.PHONY: bundle-bump
bundle-bump:  ## Update Brewfile
	${BREW} bundle dump --force --file=dot-Brewfile

.PHONY: Brewfile
Brewfile: stow  ## Install Brew dependencies
	${BREW} bundle --global
