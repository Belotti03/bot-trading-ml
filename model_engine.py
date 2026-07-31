# model_engine.py - Addestramento Modelli Multi-Asset (v4.0)

import joblib
from xgboost import XGBClassifier

import config
from data_loader import download_data
from features import create_features

def train_and_save_all_models():
    print("=== ADDESTRAMENTO MODELLI IA PER IL PORTAFOGLIO ===")
    
    for ticker in config.PORTFOLIO:
        print(f"\n---> Addestramento IA per: {ticker}")
        raw_data = download_data(ticker)
        df = create_features(raw_data)
        
        feature_cols = ['return_1d', 'return_5d', 'volatility_7d', 'sma_ratio', 'rsi_14', 'volume_change']
        X = df[feature_cols]
        y = df['target']
        
        split_idx = int(len(df) * config.TRAIN_TEST_SPLIT)
        X_train, y_train = X.iloc[:split_idx], y.iloc[:split_idx]
        
        model = XGBClassifier(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.03,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        clean_name = ticker.replace('-', '_').replace('=', '_')
        model_filename = f"model_{clean_name}.joblib"
        joblib.dump(model, model_filename)
        print(f"✅ Modello per {ticker} salvato come '{model_filename}'")

    print("\n🎉 Tutti i modelli del portafoglio sono stati addestrati con successo!")

if __name__ == "__main__":
    train_and_save_all_models()