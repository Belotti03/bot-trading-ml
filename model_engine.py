import json

import numpy as np
import pandas as pd
import yfinance as yf

from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from xgboost import XGBClassifier


SCOUT_POOL = [
    "BTC-USD", "ETH-USD", "NVDA", "AMD", "MSTR", "COIN",
    "TSM", "PLTR", "ARM", "SMCI", "TSLA", "META",
    "AMZN", "GOOGL", "AAPL", "MSFT", "QQQ", "GLD"
]

FEATURES = [
    "Returns",
    "SMA_10",
    "SMA_50",
    "RSI"
]

# Numero minimo di osservazioni necessarie prima
# di iniziare a generare previsioni OOS.
MIN_TRAIN_SIZE = 120

# Numero di giorni tra una previsione OOS e la successiva.
STEP_SIZE = 20


def calculate_features(df):
    df = df.copy()

    df["Returns"] = df["Close"].pct_change()
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()

    delta = df["Close"].diff()

    gain = delta.where(
        delta > 0, 0
    ).rolling(window=14).mean()

    loss = (-delta.where(
        delta < 0, 0
    )).rolling(window=14).mean()

    rs = gain / (loss + 1e-9)

    df["RSI"] = 100 - (100 / (1 + rs))

    # Direzione del giorno successivo.
    #
    # L'ultima riga non ha un futuro disponibile:
    # il target rimane NaN e quindi non entra nel training.
    future_close = df["Close"].shift(-1)

    df["Target"] = np.where(
        future_close.isna(),
        np.nan,
        (future_close > df["Close"]).astype(int)
    )

    return df


def build_models():
    return {
        "xgb": XGBClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42,
            eval_metric="logloss"
        ),
        "lgb": LGBMClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42,
            verbose=-1
        ),
        "rf": RandomForestClassifier(
            n_estimators=100,
            max_depth=3,
            random_state=42
        )
    }


def predict_ensemble(models, X):
    probabilities = []

    for model in models.values():
        probabilities.append(
            model.predict_proba(X)[:, 1]
        )

    return np.mean(probabilities, axis=0)


def walk_forward_predictions(X, y):
    """
    Genera previsioni esclusivamente OOS.

    Per ogni blocco:
        passato -> TRAIN
        futuro  -> TEST

    Il modello non vede mai le osservazioni che deve prevedere.
    """

    all_predictions = []
    all_actuals = []

    n = len(X)

    if n <= MIN_TRAIN_SIZE:
        return np.array([]), np.array([])

    for test_start in range(
        MIN_TRAIN_SIZE,
        n,
        STEP_SIZE
    ):
        test_end = min(
            test_start + STEP_SIZE,
            n
        )

        X_train = X.iloc[:test_start]
        y_train = y.iloc[:test_start]

        X_test = X.iloc[test_start:test_end]
        y_test = y.iloc[test_start:test_end]

        if len(X_test) == 0:
            continue

        models = build_models()

        for model in models.values():
            model.fit(
                X_train,
                y_train
            )

        predictions = predict_ensemble(
            models,
            X_test
        )

        all_predictions.extend(
            predictions.tolist()
        )

        all_actuals.extend(
            y_test.tolist()
        )

    return (
        np.array(all_predictions),
        np.array(all_actuals)
    )


def evaluate_predictions(probabilities, actuals):
    if len(actuals) == 0:
        return None

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    return {
        "samples": int(len(actuals)),
        "positive_rate": float(
            actuals.mean()
        ),
        "predicted_positive_rate": float(
            predictions.mean()
        ),
        "accuracy": float(
            accuracy_score(
                actuals,
                predictions
            )
        ),
        "brier_score": float(
            brier_score_loss(
                actuals,
                probabilities
            )
        ),
        "log_loss": float(
            log_loss(
                actuals,
                probabilities,
                labels=[0, 1]
            )
        )
    }


def train_final_models(X, y):
    models = build_models()

    for model in models.values():
        model.fit(X, y)

    return models


def run_scout_and_train():

    scout_results = {}
    validation_results = {}

    for ticker in SCOUT_POOL:

        print(
            f"\nScansione Agente Scout per {ticker}..."
        )

        try:

            data = yf.Ticker(
                ticker
            ).history(
                period="2y"
            )

            if data.empty or len(data) < 150:
                print(
                    f"{ticker}: dati insufficienti."
                )
                continue

            df = calculate_features(
                data
            )

            # -------------------------------------------------
            # DATASET PER IL MODELLO
            # -------------------------------------------------

            df_train = df.dropna(
                subset=FEATURES + ["Target"]
            ).copy()

            if len(df_train) <= MIN_TRAIN_SIZE:
                print(
                    f"{ticker}: "
                    f"troppo pochi dati."
                )
                continue

            X = df_train[FEATURES]
            y = df_train["Target"].astype(int)

            # -------------------------------------------------
            # WALK-FORWARD OOS
            # -------------------------------------------------

            probabilities, actuals = (
                walk_forward_predictions(
                    X,
                    y
                )
            )

            metrics = evaluate_predictions(
                probabilities,
                actuals
            )

            if metrics is not None:

                validation_results[
                    ticker
                ] = metrics

                print(
                    f"{ticker} WALK-FORWARD | "
                    f"samples={metrics['samples']} | "
                    f"accuracy={metrics['accuracy']:.3f} | "
                    f"brier={metrics['brier_score']:.4f} | "
                    f"logloss={metrics['log_loss']:.4f}"
                )

            # -------------------------------------------------
            # MODELLO FINALE
            #
            # Dopo la validazione OOS,
            # addestriamo sui dati disponibili
            # per ottenere il segnale corrente.
            # -------------------------------------------------

            final_models = train_final_models(
                X,
                y
            )

            df_features = df.dropna(
                subset=FEATURES
            )

            if df_features.empty:
                continue

            last_features = (
                df_features[FEATURES]
                .iloc[[-1]]
            )

            current_probabilities = []

            for model in final_models.values():

                current_probabilities.append(
                    model.predict_proba(
                        last_features
                    )[0][1]
                )

            current_probability = float(
                np.mean(
                    current_probabilities
                )
            )

            last_price = float(
                df["Close"].iloc[-1]
            )

            scout_results[ticker] = {
                "prob": current_probability,
                "price": last_price
            }

            print(
                f"{ticker} CURRENT PROB = "
                f"{current_probability:.3f}"
            )

        except Exception as e:

            print(
                f"Errore su {ticker}: {e}"
            )

    # ---------------------------------------------------------
    # SEGNALI CORRENTI
    # ---------------------------------------------------------

    with open(
        "scout_signals.json",
        "w"
    ) as f:

        json.dump(
            scout_results,
            f,
            indent=4
        )

    # ---------------------------------------------------------
    # REPORT WALK-FORWARD
    # ---------------------------------------------------------

    with open(
        "ml_validation_report.json",
        "w"
    ) as f:

        json.dump(
            validation_results,
            f,
            indent=4
        )

    print(
        "\n========================================"
    )

    print(
        f"Scansione completata: "
        f"{len(scout_results)} asset."
    )

    print(
        f"Walk-forward completato: "
        f"{len(validation_results)} asset."
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    run_scout_and_train()
