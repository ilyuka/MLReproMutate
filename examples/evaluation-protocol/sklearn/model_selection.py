class StratifiedKFold:
    def __init__(
        self,
        *,
        n_splits,
        shuffle=False,
        random_state=None,
    ):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def get_n_splits(self):
        return self.n_splits
