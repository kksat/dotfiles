export TESTFOLDER=./test/
export STOWCOMMAND=stow --dotfiles --stow --adopt .
export RESTOWCOMMAND=stow --dotfiles --restow --adopt .
export BREW=brew
HOMEBREW_BUNDLE_FILE_GLOBAL=~/.Brewfiles/dev.Brewfile

.PHONY: help
help: ## Prints help for targets with comments
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

dot-config/nvim: ## Stow nvim
	(mkdir -p dot-config && cd dot-config && git clone https://github.com/kksat/nvim.git)

.PHONY: stow
stow: dot-config/nvim ## Stow all dotfiles
	${STOWCOMMAND} --target=$$HOME

.PHONY: restow
restow: dot-config/nvim ## Restow all dotfiles
	${RESTOWCOMMAND} --target=$$HOME

.PHONY: adopt
adopt: ## Adopt all dotfiles
	${STOWCOMMAND} --adopt

.PHONY: simulate
simulate: ## Simulate stow all dotfiles
	${STOWCOMMAND} --simulate --verbose=2

.PHONY: test
test: dot-config/nvim ## Test stow - put all in ./test instread of ~
	${STOWCOMMAND} --target="${TESTFOLDER}"

.PHONY: bundle-bump
bundle-bump:  ## Update Brewfile
	${BREW} bundle dump --force --file=dot-Brewfile

.PHONY: Brewfile
Brewfile: stow  ## Install Brew dependencies
	HOMEBREW_BUNDLE_FILE_GLOBAL=${HOMEBREW_BUNDLE_FILE_GLOBAL} \
	${BREW} bundle --global

.PHONY: install
install: Brewfile ## Install everything
