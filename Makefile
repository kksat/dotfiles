
.PHONY: stow
stow: ## Stow all dotfiles
	stow --dotfiles --stow .

.PHONY: simulate
simulate: ## Simulate stow all dotfiles
	stow --simulate --dotfiles --stow --verbose=2 .

.PHONY: test
test:  # Test stow - put all in ./test instread of ~
	stow --dotfiles --target=./test/~/ --stow . 
