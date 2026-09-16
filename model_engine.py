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

TRAIN_RATIO = 0.80


def calculate_features(df):
    df = df.copy()

    df["Returns"] = df["Close"].pct_change()
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

    rs = gain / (loss + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    # Target = direzione del giorno successivo.
    # L'ultima riga NON ha un futuro disponibile,
    # quindi deve rimanere NaN e NON entrare nel training.
    future_close = df["Close"].shift(-1)
    df["Target"] = np.where(
        future_close.isna(),
        np.nan,
        (future_close > df["Close"]).astype(int)
    )

    return df


def build_models():
    models = {
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

    return models


def evaluate_oos(models, X_test, y_test):
    probabilities = []

    for model in models.values():
        probabilities.append(
            model.predict_proba(X_test)[:, 1]
        )

    ensemble_prob = np.mean(probabilities, axis=0)
    ensemble_pred = (ensemble_prob >= 0.50).astype(int)

    return {
        "samples": int(len(y_test)),
        "positive_rate": float(y_test.mean()),
        "accuracy": float(accuracy_score(y_test, ensemble_pred)),
        "brier_score": float(
            brier_score_loss(y_test, ensemble_prob)
        ),
        "log_loss": float(
            log_loss(y_test, ensemble_prob, labels=[0, 1])
        )
    }


def run_scout_and_train():
    scout_results = {}
    validation_results = {}

    for ticker in SCOUT_POOL:
        print(f"\nScansione Agente Scout per {ticker}...")

        try:
            data = yf.Ticker(ticker).history(period="2y")

            if data.empty or len(data) < 60:
                print(f"{ticker}: dati insufficienti.")
                continue

            df = calculate_features(data)

            last_price = float(df["Close"].iloc[-1])

            # Per il training usiamo SOLO righe che hanno
            # effettivamente un target futuro.
            df_train = df.dropna(
                subset=FEATURES + ["Target"]
            ).copy()

            if len(df_train) < 100:
                print(f"{ticker}: troppo pochi dati per il training.")
                continue

            X = df_train[FEATURES]
            y = df_train["Target"].astype(int)

            # -------------------------------------------------
            # 1. TEMPORAL TRAIN / TEST SPLIT
            # -------------------------------------------------
            split_index = int(len(df_train) * TRAIN_RATIO)

            if split_index < 50 or len(df_train) - split_index < 20:
                print(f"{ticker}: split temporale non valido.")
                continue

            X_train = X.iloc[:split_index]
            y_train = y.iloc[:split_index]

            X_test = X.iloc[split_index:]
            y_test = y.iloc[split_index:]

            # -------------------------------------------------
            # 2. OOS VALIDATION
            # -------------------------------------------------
            validation_models = build_models()

            for model in validation_models.values():
                model.fit(X_train, y_train)

            oos_metrics = evaluate_oos(
                validation_models,
                X_test,
                y_test
            )

            validation_results[ticker] = oos_metrics

            print(
                f"{ticker} OOS | "
                f"accuracy={oos_metrics['accuracy']:.3f} | "
                f"brier={oos_metrics['brier_score']:.4f} | "
                f"logloss={oos_metrics['log_loss']:.4f}"
            )

            # -------------------------------------------------
            # 3. TRAINING FINALE
            #
            # Dopo aver misurato l'OOS, addestriamo il modello
            # sull'intero storico disponibile per ottenere
            # la previsione corrente.
            # -------------------------------------------------
            final_models = build_models()

            for model in final_models.values():
                model.fit(X, y)

            # -------------------------------------------------
            # 4. CURRENT SIGNAL
            # -------------------------------------------------
            df_features = df.dropna(subset=FEATURES)

            if df_features.empty:
                continue

            last_features = df_features[FEATURES].iloc[[-1]]

            probabilities = []

            for model in final_models.values():
                probabilities.append(
                    model.predict_proba(last_features)[0][1]
                )

            prob_ensemble = float(
                np.mean(probabilities)
            )

            scout_results[ticker] = {
                "prob": prob_ensemble,
                "price": last_price
            }

            print(
                f"{ticker} CURRENT PROB = "
                f"{prob_ensemble:.3f}"
            )

        except Exception as e:
            print(f"Errore su {ticker}: {e}")

    # ---------------------------------------------------------
    # Segnali utilizzati da main.py
    # ---------------------------------------------------------
    with open("scout_signals.json", "w") as f:
        json.dump(
            scout_results,
            f,
            indent=4
        )

    # ---------------------------------------------------------
    # Report OOS separato
    # ---------------------------------------------------------
    with open("ml_validation_report.json", "w") as f:
        json.dump(
            validation_results,
            f,
            indent=4
        )

    print(
        f"\nScansione completata per "
        f"{len(scout_results)} asset."
    )

    print(
        f"Validazione OOS completata per "
        f"{len(validation_results)} asset."
    )


if __name__ == "__main__":
    run_scout_and_train()
