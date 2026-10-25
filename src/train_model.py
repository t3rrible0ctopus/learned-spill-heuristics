import os
import argparse
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def train_model(data_file="data/train/spill_cost_dataset.csv",
                model_file="models/spill_cost_model.pkl", seed=42):
    data = pd.read_csv(data_file)

    features = [
        "degree",
        "live_range_length",
        "use_frequency",
        "definition_frequency",
    ]

    X = data[features]
    y = data["spill_ops"]
    groups = data["program"]

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.2,
        random_state=seed
    )

    train_idx, test_idx = next(splitter.split(X, y, groups))

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=seed,
        max_depth=10
    )

    validation_model = RandomForestRegressor(
        n_estimators=100,
        random_state=seed,
        max_depth=10
    )
    validation_model.fit(X_train, y_train)
    predictions = validation_model.predict(X_test)

    metrics = {
        "Seed": seed,
        "Validation MAE": mean_absolute_error(y_test, predictions),
        "Validation MSE": mean_squared_error(y_test, predictions),
        "Validation R2": r2_score(y_test, predictions),
    }

    # Refit after reporting grouped validation so evaluation uses all training
    # programs while remaining completely separate from the held-out corpus.
    model.fit(X, y)
    os.makedirs(os.path.dirname(model_file) or ".", exist_ok=True)
    joblib.dump(model, model_file)

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train spill-cost estimator")
    parser.add_argument("--data", default="data/train/spill_cost_dataset.csv")
    parser.add_argument("--model", default="models/spill_cost_model.pkl")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    metrics = train_model(args.data, args.model, args.seed)
    print("Model Evaluation")
    for name, value in metrics.items():
        if name != "Seed":
            print(f"{name}: {value:.4f}")
    print(f"Model saved to {args.model}")
