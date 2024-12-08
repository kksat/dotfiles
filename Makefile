export TESTFOLDER=./test/~/
export STOWCOMMAND=stow --dotfiles --stow --target=$$HOME .

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
