export TESTFOLDER=./test/~/
export STOWCOMMAND=stow --dotfiles --stow --target=$$HOME .
export BREW=brew

.PHONY: stow
stow: ## Stow all dotfiles
	${STOWCOMMAND}

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
