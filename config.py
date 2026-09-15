# config.py - Configurazione Multi-Asset Portafoglio (v5.0)

# Portafoglio Multi-Asset
PORTFOLIO = ["BTC-USD", "NVDA", "QQQ", "GLD"]
TIMEFRAME = "1d"
TRAIN_TEST_SPLIT = 0.8

# Simulazione Capitale Iniziale ($)
INITIAL_CAPITAL = 10000.0

# Soglie di Confidenza XGBoost
LONG_THRESHOLD = 0.60
SHORT_THRESHOLD = 0.35

# Gestione Rischio
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
FEE_RATE = 0.001

# Credenziali Exchange (Testnet / Paper Trading)
API_KEY = "LA_TUA_API_KEY_TESTNET"
API_SECRET = "IL_TUO_API_SECRET_TESTNET"
USE_TESTNET = True
# Credenziali Telegram (Per notifiche su Smartphone)
# Lascia vuoto per ora: il bot simulerà l'invio della notifica a schermo
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
