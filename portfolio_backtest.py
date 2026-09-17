import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# CONFIG
# ============================================================

INITIAL_CAPITAL = 10_000.0

LONG_THRESHOLD = 0.55
HIGH_CONVICTION_THRESHOLD = 0.60
EXIT_THRESHOLD = 0.45

MAX_POSITION_55 = 0.30
MAX_POSITION_60 = 0.40

MAX_NEW_POSITIONS_PER_DAY = 5

STOP_ATR_MULTIPLIER = 2.0
TRAILING_ATR_MULTIPLIER = 2.5

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005

ATR_PERIOD = 14

MIN_TRAIN_SIZE = 120
STEP_SIZE = 20

LOOKBACK_PERIOD = "2y"

ASSETS = [
    "BTC-USD",
    "ETH-USD",
    "NVDA",
    "AMD",
    "MSTR",
    "COIN",
    "TSM",
    "PLTR",
    "ARM",
    "SMCI",
    "TSLA",
    "META",
    "AMZN",
    "GOOGL",
    "AAPL",
    "MSFT",
    "QQQ",
    "GLD",
]


MODEL_FEATURES = [
    "Return_1d",
    "Return_5d",
    "SMA_10",
    "SMA_50",
    "SMA_ratio",
    "RSI",
]


# ============================================================
# DATA
# ============================================================

def download_data(ticker):

    print(f"Downloading {ticker}...")

    df = yf.download(
        ticker,
        period=LOOKBACK_PERIOD,
        interval="1d",
        progress=False,
        auto_adjust=False,
    )

    if df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = [
        "Open",
        "High",
        "Low",
        "Close",
    ]

    if not all(
        column in df.columns
        for column in required
    ):
        return pd.DataFrame()

    df = df[required].copy()

    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    df.dropna(inplace=True)

    # Normalize dates.
    df.index = pd.to_datetime(
        df.index
    ).tz_localize(None)

    # Remove duplicate dates.
    df = df[
        ~df.index.duplicated(
            keep="last"
        )
    ]

    return df


# ============================================================
# FEATURES
# ============================================================

def calculate_features(df):

    data = df.copy()

    data["Return_1d"] = (
        data["Close"].pct_change(1)
    )

    data["Return_5d"] = (
        data["Close"].pct_change(5)
    )

    data["SMA_10"] = (
        data["Close"].rolling(10).mean()
    )

    data["SMA_50"] = (
        data["Close"].rolling(50).mean()
    )

    data["SMA_ratio"] = (
        data["SMA_10"]
        / data["SMA_50"]
    )

    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = (
        avg_gain
        / avg_loss.replace(
            0,
            np.nan
        )
    )

    data["RSI"] = (
        100
        - (
            100
            / (1 + rs)
        )
    )

    # ATR
    prev_close = data["Close"].shift(1)

    tr1 = (
        data["High"]
        - data["Low"]
    )

    tr2 = (
        data["High"]
        - prev_close
    ).abs()

    tr3 = (
        data["Low"]
        - prev_close
    ).abs()

    data["TR"] = pd.concat(
        [
            tr1,
            tr2,
            tr3,
        ],
        axis=1
    ).max(axis=1)

    data["ATR"] = (
        data["TR"]
        .rolling(ATR_PERIOD)
        .mean()
    )

    # Next-day direction.
    data["Target"] = (
        data["Close"].shift(-1)
        > data["Close"]
    ).astype(float)

    return data


# ============================================================
# MODEL
# ============================================================

def train_models(train):

    from sklearn.ensemble import RandomForestClassifier
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier

    X = train[MODEL_FEATURES]
    y = train["Target"].astype(int)

    models = [

        XGBClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        ),

        LGBMClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            verbosity=-1,
            random_state=42,
        ),

        RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        ),
    ]

    for model in models:
        model.fit(X, y)

    return models


def predict_probability(
    models,
    row
):

    X = row[
        MODEL_FEATURES
    ].to_frame().T

    probabilities = []

    for model in models:

        probabilities.append(
            model.predict_proba(X)[0, 1]
        )

    return float(
        np.mean(probabilities)
    )


# ============================================================
# OOS PREDICTIONS
# ============================================================

def generate_oos_predictions(df):

    data = calculate_features(df)

    data = data.replace(
        [np.inf, -np.inf],
        np.nan
    )

    data = data.dropna(
        subset=MODEL_FEATURES
        + [
            "ATR",
            "Target",
            "Open",
            "High",
            "Low",
            "Close",
        ]
    ).copy()

    predictions = []

    test_start = MIN_TRAIN_SIZE

    while test_start < len(data):

        test_end = min(
            test_start + STEP_SIZE,
            len(data)
        )

        train = data.iloc[
            :test_start
        ]

        test = data.iloc[
            test_start:test_end
        ]

        models = train_models(
            train
        )

        for idx, row in test.iterrows():

            probability = (
                predict_probability(
                    models,
                    row
                )
            )

            predictions.append({

                "Date": idx,

                "Open": float(
                    row["Open"]
                ),

                "High": float(
                    row["High"]
                ),

                "Low": float(
                    row["Low"]
                ),

                "Close": float(
                    row["Close"]
                ),

                "ATR": float(
                    row["ATR"]
                ),

                "Probability": probability,
            })

        test_start = test_end

    return pd.DataFrame(
        predictions
    )


# ============================================================
# PORTFOLIO BACKTEST
# ============================================================

def run_portfolio_backtest(
    all_predictions
):

    # --------------------------------------------------------
    # Build individual date sets.
    # We DO NOT mix crypto weekends into the equity calendar.
    # --------------------------------------------------------

    asset_dates = {}

    for ticker, df in all_predictions.items():

        asset_dates[ticker] = set(
            pd.to_datetime(
                df["Date"]
            )
        )

    # Use dates where at least one asset has data.
    all_dates = sorted(
        set().union(
            *asset_dates.values()
        )
    )

    # --------------------------------------------------------
    # Fast lookup
    # --------------------------------------------------------

    prediction_map = {}

    for ticker, df in all_predictions.items():

        for _, row in df.iterrows():

            date = pd.Timestamp(
                row["Date"]
            )

            prediction_map[
                (ticker, date)
            ] = row

    cash = INITIAL_CAPITAL

    positions = {}

    trades = []

    equity_curve = []

    # --------------------------------------------------------
    # Process each global date.
    # --------------------------------------------------------

    for i in range(
        len(all_dates) - 1
    ):

        signal_date = all_dates[i]
        next_date = all_dates[i + 1]

        # ----------------------------------------------------
        # 1. EXIT EXISTING POSITIONS
        # ----------------------------------------------------

        for ticker in list(
            positions.keys()
        ):

            position = positions[
                ticker
            ]

            signal = prediction_map.get(
                (
                    ticker,
                    signal_date
                )
            )

            next_bar = prediction_map.get(
                (
                    ticker,
                    next_date
                )
            )

            # Asset did not trade on this date.
            if signal is None:
                continue

            # Asset has no next bar yet.
            if next_bar is None:
                continue

            entry_price = (
                position[
                    "entry_price"
                ]
            )

            shares = position[
                "shares"
            ]

            peak_price = position[
                "peak_price"
            ]

            atr = float(
                signal["ATR"]
            )

            probability = float(
                signal[
                    "Probability"
                ]
            )

            next_open = float(
                next_bar["Open"]
            )

            next_high = float(
                next_bar["High"]
            )

            next_low = float(
                next_bar["Low"]
            )

            # Update peak with actual intraday high.
            peak_price = max(
                peak_price,
                next_high
            )

            position[
                "peak_price"
            ] = peak_price

            stop_price = (
                entry_price
                - STOP_ATR_MULTIPLIER
                * atr
            )

            trailing_price = (
                peak_price
                - TRAILING_ATR_MULTIPLIER
                * atr
            )

            exit_price = None
            exit_reason = None

            # ------------------------------------------------
            # STOP
            # ------------------------------------------------

            if next_low <= stop_price:

                exit_price = min(
                    next_open,
                    stop_price
                )

                exit_reason = (
                    "STOP"
                )

            # ------------------------------------------------
            # TRAILING STOP
            # ------------------------------------------------

            elif (
                next_low
                <= trailing_price
            ):

                exit_price = min(
                    next_open,
                    trailing_price
                )

                exit_reason = (
                    "TRAILING_STOP"
                )

            # ------------------------------------------------
            # ML EXIT
            # ------------------------------------------------

            elif (
                probability
                < EXIT_THRESHOLD
            ):

                exit_price = next_open

                exit_reason = (
                    "ML_EXIT"
                )

            # ------------------------------------------------
            # Execute exit
            # ------------------------------------------------

            if exit_price is not None:

                execution_price = (
                    exit_price
                    * (
                        1
                        - SLIPPAGE_RATE
                    )
                )

                gross_value = (
                    shares
                    * execution_price
                )

                fee = (
                    gross_value
                    * FEE_RATE
                )

                cash += (
                    gross_value
                    - fee
                )

                pnl = (
                    execution_price
                    - entry_price
                ) * shares

                trades.append({

                    "Ticker": ticker,

                    "EntryDate":
                        position[
                            "entry_date"
                        ],

                    "ExitDate":
                        next_date,

                    "EntryPrice":
                        entry_price,

                    "ExitPrice":
                        execution_price,

                    "Shares":
                        shares,

                    "PnL":
                        pnl,

                    "Return":
                        (
                            execution_price
                            / entry_price
                        ) - 1,

                    "Reason":
                        exit_reason,
                })

                del positions[
                    ticker
                ]

        # ----------------------------------------------------
        # 2. ENTER NEW POSITIONS
        # ----------------------------------------------------

        candidates = []

        for ticker in ASSETS:

            if ticker in positions:
                continue

            signal = prediction_map.get(
                (
                    ticker,
                    signal_date
                )
            )

            next_bar = prediction_map.get(
                (
                    ticker,
                    next_date
                )
            )

            if (
                signal is None
                or next_bar is None
            ):
                continue

            probability = float(
                signal[
                    "Probability"
                ]
            )

            if (
                probability
                >= LONG_THRESHOLD
            ):

                candidates.append({

                    "Ticker":
                        ticker,

                    "Probability":
                        probability,

                    "NextBar":
                        next_bar,
                })

        candidates.sort(
            key=lambda x:
                x["Probability"],
            reverse=True
        )

        candidates = candidates[
            :MAX_NEW_POSITIONS_PER_DAY
        ]

        # ----------------------------------------------------
        # Current portfolio equity
        # ----------------------------------------------------

        portfolio_equity = cash

        for ticker, position in (
            positions.items()
        ):

            current_bar = prediction_map.get(
                (
                    ticker,
                    signal_date
                )
            )

            if current_bar is not None:

                portfolio_equity += (
                    position["shares"]
                    * float(
                        current_bar["Close"]
                    )
                )

        # ----------------------------------------------------
        # Enter candidates
        # ----------------------------------------------------

        for candidate in candidates:

            ticker = candidate[
                "Ticker"
            ]

            probability = candidate[
                "Probability"
            ]

            next_bar = candidate[
                "NextBar"
            ]

            # Recalculate equity before
            # every new position.
            portfolio_equity = cash

            for (
                existing_ticker,
                position
            ) in positions.items():

                current_bar = (
                    prediction_map.get(
                        (
                            existing_ticker,
                            signal_date
                        )
                    )
                )

                if current_bar is not None:

                    portfolio_equity += (
                        position["shares"]
                        * float(
                            current_bar[
                                "Close"
                            ]
                        )
                    )

            if (
                probability
                >= HIGH_CONVICTION_THRESHOLD
            ):

                allocation_pct = (
                    MAX_POSITION_60
                )

            else:

                allocation_pct = (
                    MAX_POSITION_55
                )

            target_value = (
                portfolio_equity
                * allocation_pct
            )

            allocation = min(
                target_value,
                cash
            )

            if allocation <= 0:
                continue

            open_price = float(
                next_bar["Open"]
            )

            execution_price = (
                open_price
                * (
                    1
                    + SLIPPAGE_RATE
                )
            )

            fee = (
                allocation
                * FEE_RATE
            )

            position_value = (
                allocation
                - fee
            )

            shares = (
                position_value
                / execution_price
            )

            cash -= allocation

            positions[ticker] = {

                "entry_date":
                    next_date,

                "entry_price":
                    execution_price,

                "shares":
                    shares,

                "peak_price":
                    float(
                        next_bar["High"]
                    ),
            }

        # ----------------------------------------------------
        # 3. END-OF-DAY EQUITY
        # ----------------------------------------------------

        end_equity = cash

        for ticker, position in (
            positions.items()
        ):

            current_bar = prediction_map.get(
                (
                    ticker,
                    signal_date
                )
            )

            if current_bar is not None:

                end_equity += (
                    position["shares"]
                    * float(
                        current_bar["Close"]
                    )
                )

        equity_curve.append({

            "Date":
                signal_date,

            "Equity":
                end_equity,

            "Cash":
                cash,

            "Positions":
                len(positions),
        })

    # ========================================================
    # FINAL LIQUIDATION
    # ========================================================

    if positions:

        final_dates = {}

        for ticker in positions:

            ticker_dates = sorted(
                asset_dates[
                    ticker
                ]
            )

            if ticker_dates:
                final_dates[ticker] = (
                    ticker_dates[-1]
                )

        for ticker in list(
            positions.keys()
        ):

            position = positions[
                ticker
            ]

            last_date = final_dates.get(
                ticker
            )

            if last_date is None:
                continue

            last_bar = prediction_map.get(
                (
                    ticker,
                    last_date
                )
            )

            if last_bar is None:
                continue

            exit_price = (
                float(
                    last_bar["Close"]
                )
                * (
                    1
                    - SLIPPAGE_RATE
                )
            )

            gross_value = (
                position["shares"]
                * exit_price
            )

            fee = (
                gross_value
                * FEE_RATE
            )

            cash += (
                gross_value
                - fee
            )

            pnl = (
                exit_price
                - position[
                    "entry_price"
                ]
            ) * position["shares"]

            trades.append({

                "Ticker":
                    ticker,

                "EntryDate":
                    position[
                        "entry_date"
                    ],

                "ExitDate":
                    last_date,

                "EntryPrice":
                    position[
                        "entry_price"
                    ],

                "ExitPrice":
                    exit_price,

                "Shares":
                    position[
                        "shares"
                    ],

                "PnL":
                    pnl,

                "Return":
                    (
                        exit_price
                        / position[
                            "entry_price"
                        ]
                    ) - 1,

                "Reason":
                    "END_OF_TEST",
            })

            del positions[
                ticker
            ]

    # ========================================================
    # RESULTS
    # ========================================================

    equity_df = pd.DataFrame(
        equity_curve
    )

    trades_df = pd.DataFrame(
        trades
    )

    # Final equity MUST be cash after
    # all positions have been liquidated.
    final_equity = float(
        cash
    )

    total_return = (
        final_equity
        / INITIAL_CAPITAL
    ) - 1

    if not equity_df.empty:

        running_max = (
            equity_df["Equity"]
            .cummax()
        )

        drawdown = (
            equity_df["Equity"]
            / running_max
        ) - 1

        max_drawdown = float(
            drawdown.min()
        )

        daily_returns = (
            equity_df["Equity"]
            .pct_change()
            .dropna()
        )

        if (
            len(daily_returns) > 1
            and daily_returns.std() > 0
        ):

            sharpe = (
                daily_returns.mean()
                / daily_returns.std()
                * math.sqrt(252)
            )

        else:

            sharpe = 0.0

    else:

        max_drawdown = 0.0
        sharpe = 0.0

    trades_count = len(
        trades_df
    )

    if trades_count > 0:

        wins = (
            trades_df["PnL"] > 0
        ).sum()

        win_rate = (
            wins
            / trades_count
        )

        gross_profit = (
            trades_df.loc[
                trades_df["PnL"] > 0,
                "PnL"
            ].sum()
        )

        gross_loss = abs(
            trades_df.loc[
                trades_df["PnL"] < 0,
                "PnL"
            ].sum()
        )

        if gross_loss > 0:

            profit_factor = (
                gross_profit
                / gross_loss
            )

        else:

            profit_factor = float(
                "inf"
            )

    else:

        win_rate = 0.0
        profit_factor = 0.0

    result = {

        "InitialCapital":
            INITIAL_CAPITAL,

        "FinalEquity":
            final_equity,

        "TotalReturn":
            total_return,

        "MaxDrawdown":
            max_drawdown,

        "Sharpe":
            sharpe,

        "Trades":
            trades_count,

        "WinRate":
            win_rate,

        "ProfitFactor":
            profit_factor,
    }

    return (
        result,
        equity_df,
        trades_df
    )


# ============================================================
# MAIN
# ============================================================

def main():

    output_dir = Path(
        "portfolio_backtest_results"
    )

    output_dir.mkdir(
        exist_ok=True
    )

    all_predictions = {}

    print(
        "\n========================================"
    )

    print(
        "GENERATING WALK-FORWARD PREDICTIONS"
    )

    print(
        "========================================\n"
    )

    for ticker in ASSETS:

        try:

            df = download_data(
                ticker
            )

            if df.empty:

                print(
                    f"{ticker}: no data"
                )

                continue

            predictions = (
                generate_oos_predictions(
                    df
                )
            )

            if predictions.empty:

                print(
                    f"{ticker}: no OOS predictions"
                )

                continue

            all_predictions[
                ticker
            ] = predictions

            predictions.to_csv(
                output_dir
                / f"{ticker}_predictions.csv",
                index=False,
            )

            print(
                f"{ticker}: "
                f"{len(predictions)} OOS signals"
            )

        except Exception as e:

            print(
                f"ERROR {ticker}: {e}"
            )

    if not all_predictions:

        raise RuntimeError(
            "No predictions generated."
        )

    print(
        "\n========================================"
    )

    print(
        "RUNNING SINGLE PORTFOLIO BACKTEST"
    )

    print(
        "========================================\n"
    )

    (
        result,
        equity_df,
        trades_df
    ) = run_portfolio_backtest(
        all_predictions
    )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if not np.isfinite(
        result["FinalEquity"]
    ):

        raise RuntimeError(
            "Final equity is not finite."
        )

    if (
        result["FinalEquity"] < 0
    ):

        raise RuntimeError(
            "Final equity is negative."
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    equity_df.to_csv(
        output_dir
        / "portfolio_equity.csv",
        index=False,
    )

    trades_df.to_csv(
        output_dir
        / "portfolio_trades.csv",
        index=False,
    )

    pd.DataFrame(
        [result]
    ).to_csv(
        output_dir
        / "portfolio_summary.csv",
        index=False,
    )

    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print(
        "\n========================================"
    )

    print(
        "PORTFOLIO BACKTEST COMPLETED"
    )

    print(
        "========================================"
    )

    print(
        f"Initial capital : "
        f"€{result['InitialCapital']:,.2f}"
    )

    print(
        f"Final equity    : "
        f"€{result['FinalEquity']:,.2f}"
    )

    print(
        f"Total return    : "
        f"{result['TotalReturn']:.2%}"
    )

    print(
        f"Max drawdown    : "
        f"{result['MaxDrawdown']:.2%}"
    )

    print(
        f"Sharpe          : "
        f"{result['Sharpe']:.2f}"
    )

    print(
        f"Trades          : "
        f"{result['Trades']}"
    )

    print(
        f"Win rate        : "
        f"{result['WinRate']:.2%}"
    )

    print(
        f"Profit factor   : "
        f"{result['ProfitFactor']:.2f}"
    )


if __name__ == "__main__":
    main()
