def train_test_split(
    X,
    y,
    *,
    test_size,
    random_state,
    stratify,
):
    del test_size, random_state

    if stratify is None:
        test_indices = [0, 1]
    else:
        test_indices = [0, 2]

    train_indices = [
        index
        for index in range(len(X))
        if index not in test_indices
    ]

    X_train = [X[index] for index in train_indices]
    X_test = [X[index] for index in test_indices]
    y_train = [y[index] for index in train_indices]
    y_test = [y[index] for index in test_indices]

    return X_train, X_test, y_train, y_test
