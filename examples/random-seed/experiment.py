import random


def run_experiment() -> float:
    random.seed(42)
    return random.random()


if __name__ == "__main__":
    print(run_experiment())
