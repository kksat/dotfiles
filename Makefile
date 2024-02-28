
.PHONY: stow
stow: ## Stow all dotfiles
	stow --dotfiles --stow .

.PHONY: simulate
simulate: ## Simulate stow all dotfiles
	stow --simulate --dotfiles --stow --verbose=2 .

