# AUDIT RESULT 002

**Oggetto:** `docs/V2_RESEARCH_ROADMAP.md` versione 2
**Richiesta:** `docs/audits/AUDIT_REQUEST_002.md`
**Auditor:** GPT-5.6 Sol, audit indipendente e avversariale
**Data:** 2026-10-06
**File modificati dall'auditor:** nessuno

**Fedeltà:** testo verbatim come ricevuto. L'unico intervento è la
delimitazione markdown dei blocchi di codice citati dall'auditor, che
nella consegna originale erano riferimenti a file con intervallo di
righe. Nessuna parola è stata aggiunta, rimossa o riordinata.

---

Ho già individuato una discrepanza documentale: AUDIT_RESULT_001.md ricostruisce il requisito DSR in una forma diversa dal mio audit originale. La tratterò come trascrizione non fedele, come richiesto. Proseguo verificando direttamente artefatti e codice, senza eseguire il bot.

VERDETTO: REJECTED
VERIFIED — La v2 è migliorata come bozza di piano di ricerca, ma non è approvabile come protocollo statistico eseguibile.

VERIFIED — Diversi blocker dell'audit 001 sono stati solo spostati alla Fase 0C o alla sezione "decisioni aperte". Il blocker architetturale non è realmente risolto e sono emersi nuovi problemi nei risultati storici usati come contesto.

INFERRED — Un'attività separata e strettamente forense come R0.1 potrebbe essere autorizzata senza adottare la roadmap, ma la v2 attuale non deve ancora diventare authority operativa.

## Blocker

La gerarchia delle evidenze continua a confondere holdout, robustness test e inferenza su dati contaminati.
La contraddizione fra implementazione, validazione e shadow trading persiste.
DSR/PSR, primary gates e soglie economiche non sono definiti correttamente.
Il risultato +87.15% non è un vero static Buy & Hold e incorpora un confronto non equo.
La metodologia point-in-time è ancora una specifica incompleta, non una procedura implementabile.
Le 11 decisioni aperte impediscono l'esecuzione e non comprendono tutte le decisioni necessarie.
Dati e ambiente non sono riproducibili: download dinamici, dipendenze non bloccate e assenza di snapshot raw.
MASTER_CONTEXT contiene residui contraddittori e almeno una metrica errata.

## Risposte alle 18 domande

### 1. Standard error dello Sharpe

VERIFIED — Con le assunzioni dichiarate, il calcolo è aritmeticamente corretto:

SR=1.155;
q=252;
T=2;
SE=0.70804197;
intervallo normale 95% [-0.2328, 2.5428].

VERIFIED — La finestra reale del CSV è però 2024-10-15–2026-09-24, cioè circa 1.941 anni e 487 osservazioni. Usando la durata effettiva:

SE≈0.7187;
intervallo [-0.254, 2.564].

La differenza non cambia la conclusione qualitativa.

VERIFIED — L'intervallo resta solo un'approssimazione IID. La roadmap riconosce correttamente la necessità di HAC/block bootstrap.

### 2. Riformulazione dell'overclaim

VERIFIED — La sezione 1.3 non afferma che i confronti appaiati siano necessariamente decidibili: li classifica correttamente UNKNOWN.

PROBLEMA — L'affermazione plurale secondo cui gli Sharpe individuali del periodo non sono distinguibili da zero è stata dimostrata esplicitamente solo per l'esempio SR=1.155. Gli altri risultati non sono stati sistematicamente ricalcolati con durata, frequenza e dipendenza corrette.

INFERRED — È plausibile che anche gli altri risultati biennali citati non superino il test, ma non deve essere marcato VERIFIED senza calcolo individuale.

### 3. Mappa di contaminazione e CSV

VERIFIED — Esistono 52 CSV locali.

VERIFIED — Non sono però tutti "result CSV":

20 in backtest_results;
21 in portfolio_backtest_results;
10 artefatti dynamic-universe nella root;
1 trading_log.csv di produzione.

VERIFIED — Finestre reali:

OOS individuali equity: principalmente 2025-05-21–2026-09-16;
META: 2025-06-02–2026-09-16;
crypto OOS: 2025-03-05–2026-09-17;
portfolio predictions equity: 2025-06-02–2026-09-24;
crypto portfolio: 2025-03-15–2026-09-26;
portfolio equity: 2025-03-14–2026-09-26;
dynamic fair: 2024-10-15–2026-09-24/25;
dynamic equity: 2021-12-21–2026-09-24;
trading log: 2026-07-31–2026-08-24.

VERIFIED — La sintesi della roadmap è grossolanamente corretta, ma troppo aggregata per fungere da contamination map. R0.1 resta necessario.

### 4. Cinque fonti alternative di evidenza

Solo alcune sono sostituti parziali di un holdout:

VERIFIED — Nested walk-forward: valido per stimare il processo di selezione, ma non rende incontaminati dati già usati per progettare l'ipotesi.
UNKNOWN — Historical block mai usato: ammissibile solo se R0.1 dimostra che era davvero quarantinato.
INFERRED — Mercati esterni congelati: utile per generalizzazione, ma può introdurre selection bias e domain shift.
VERIFIED — Leave-one-cohort/asset-class-out: robustness test, non holdout temporale indipendente.
VERIFIED — Paired test preregistrato: inferenza comparativa; non "decontamina" dati già osservati.

BLOCKER — La roadmap deve classificare separatamente development evidence, robustness evidence e confirmatory evidence.

### 5. Coorti, pannello sbilanciato e MSTR

VERIFIED — Coorti e pannello sbilanciato sono la correzione concettuale giusta.

VERIFIED — Non sono però operazionalizzati: weighting, periodi comuni, seasoning e comparabilità rimangono aperti.

HYPOTHESIS — MSTR presenta una forte variazione di esposizione economica, ma non è dimostrato nel repository che esista un'unica data di break oggettiva.

RISCHIO — Special-case ex-post di MSTR può diventare data snooping. Serve una regola generale preregistrata per structural breaks, oppure esclusione mediante criteri di eligibility applicati a tutti gli asset.

### 6. Universo point-in-time e fallback

VERIFIED — La metodologia elenca requisiti corretti, ma non è ancora "implementable form":

manca il provider;
t-1 non definisce i lag informativi;
mancano venue e investability rules per crypto;
QQQ e suoi componenti creano sovrapposizione;
filtri e rebalance sono irrisolti;
delisting return richiede dati non presenti.

VERIFIED — Nel repository non è documentata alcuna regola point-in-time per i 18 ticker.

UNKNOWN — Non può essere provato che nessuna regola sia stata usata storicamente fuori dal repository. La roadmap deve distinguere "nessuna regola documentata" da "nessuna regola esistita".

BLOCKER — Il fallback case study deve essere un ramo formale e mutuamente esclusivo. Se viene scelto, H1 non può affermare generalizzabilità cross-sectional né soddisfare il requisito di un universo point-in-time ampio.

### 7. pct_change() e tassonomia delle barre

VERIFIED — Il difetto è presente:

`model_engine.py` Ln 46–49

```python
df["Returns"] = df["Close"].pct_change()
df["SMA_10"] = df["Close"].rolling(window=10).mean()
```

VERIFIED — Con pandas locale 2.3.3:

default implicito: [NaN, 0.0, 0.10] su [100, NaN, 110];
fill_method=None: [NaN, NaN, NaN].

VERIFIED — Sono presenti 31 chiamate a pct_change() in 15 file Python; nessuna specifica esplicitamente fill_method.

VERIFIED — Reindicizzazione sul calendario chiude il caso delle date assenti, ma la tassonomia non è completa né mutuamente esclusiva. Mancano almeno:

OHLC invalido;
duplicati e ordine temporale;
timezone/session label;
provider outage/revision;
ticker/currency/unit change;
calendario half-day;
qualità del volume.

"Corporate action" è inoltre un flag ortogonale, non uno stato alternativo della barra.

### 8. Separazione infrastruttura/plugin

BLOCKER — La contraddizione è stata spostata:

`V2_RESEARCH_ROADMAP.md` Ln 217–221

```
- Generic **infrastructure and engine are implemented first**.
- **Strategy plugins and rules** are promoted only after validation.
- One identical core for features, signals, portfolio and risk.
- Separate adapters for historical simulator, paper and live.
```

Una strategia non può essere validata o messa in shadow senza una sua implementazione.

Correzione necessaria:

plugin experimental implementabile prima della validazione;
plugin approved/deployable solo dopo;
promozione, non implementazione, subordinata al validation record.

### 9. Conformance replay

VERIFIED — È necessario, ma non sufficiente.

Un replay singolo con "ordini identici" non copre:

disponibilità temporale dei dati;
partial bar;
calendari e corporate actions;
ordine degli eventi;
state transition;
fill e slippage;
error handling;
divergenze fra signal intent e ordine eseguito.

Serve una conformance suite su snapshot ed edge case, confrontando gli intent pre-esecuzione quando gli adapter di fill devono necessariamente divergere.

### 10. Baseline

VERIFIED — La lista è migliorata e il comparatore primario elimina il comparatore mobile solo se viene congelato prima di osservare il candidato.

Problemi:

manca una trend rule canonica in Phase 1; il master context la considera baseline, mentre la roadmap sposta tutto il trend in H2;
volatility sizing non è una strategia autonoma: va abbinato allo stesso segnale con sizing statico;
factor attribution e placebo sono diagnostiche, non baseline;
per-sleeve benchmark non definisce aggregazione e capital allocation;
"single comparator" resta una decisione aperta.

### 11. H5 volatility sizing

VERIFIED — La ricollocazione fra sizing/risk baseline è corretta.

INFERRED — La prevedibilità della volatilità ha supporto nella letteratura, ma non è VERIFIED by the audit né verificata nel repository.

BLOCKER — "Equal risk or frontier" non è ancora testabile. Mancano:

target volatility;
forecast benchmark, per esempio rolling variance/EWMA;
leva massima;
rebalance frequency;
turnover/costi;
forecast loss, per esempio QLIKE;
regola di confronto sulla frontiera.

L'"or" permette di scegliere il confronto dopo aver visto i risultati.

### 12. Ordine H2/H1/H6/H3/H4

INFERRED — H2 prima di H1 è ragionevole con universo piccolo.

UNKNOWN — Non esiste evidenza sufficiente per presentare l'intero ordine come ottimale.

CONTRADDIZIONE — H6 è dichiarata "tested alongside H2", ma la decisione 9 lascia ancora aperto se H6 sia distinta da H2.

BLOCKER — Un template comune senza null, estimand, metrica e soglie non è preregistrabile. Inoltre applicare soglie uniformi ad alpha, regime gating e sizing può essere metodologicamente sbagliato: serve un framework comune con criteri specifici per estimand.

### 13. Primary gate e diagnostiche

BLOCKER — La classificazione non è sicura.

Una strategia potrebbe superare i primary gate pur:

violando il max drawdown imposto dall'investitore;
fallendo il placebo;
dipendendo da un unico asset;
fallendo tutti i regimi rilevanti.

Se drawdown o concentrazione sono mandati di rischio, devono essere hard gate. Il placebo dovrebbe essere un gate inferenziale quando la validità del timing dipende da esso.

### 14. Rinvio delle soglie alla Fase 0C

VERIFIED — Non inventare nuove soglie arbitrarie è corretto.

BLOCKER — Questo rende la roadmap un piano per costruire il protocollo, non il protocollo eseguibile richiesto dall'audit.

VERIFIED — La power analysis non può "derivare" tutte le soglie:

determina la dimensione dell'effetto rilevabile;
non determina risk tolerance, utility, drawdown massimo o costo economicamente accettabile;
tali valori devono provenire dal mandato economico della Fase 0A.

Le soglie devono essere congelate usando solo design data o simulazioni dichiarate, prima dei risultati candidati.

### 15. Kill criteria

VERIFIED — Non sono ancora verificabili perché trial, budget e gate non sono definiti.

Problemi:

"exceeding budget to reach threshold" deve essere semplicemente "exceeding budget";
tuning preregistrato entro nested validation è legittimo, non prova automatica di overfitting;
manca la categoria INCONCLUSIVE/UNDERPOWERED;
mancano kill per leakage, dati non riproducibili, parity failure e violazione dei risk mandate.

### 16. Abbandono ML

PARZIALMENTE CORRETTO — Fallire meta-labeling non falsifica volatility ML.

BLOCKER — Il fallimento di una singola formulazione non chiude tutto il directional ML, a meno che la famiglia, lo spazio dei modelli e il trial budget siano stati preregistrati come test esaustivo.

RISCHIO — "Other distinct targets remain open" può diventare un escape hatch infinito. Ogni nuovo target deve rientrare in un budget gerarchico di ipotesi.

### 17. Undici decisioni aperte

VERIFIED — Sono decisioni importanti, ma la lista è incompleta.

VERIFIED — La numero 11 è una domanda empirica, non una decisione.

Decisioni mancanti:

estimand e obiettivo economico primario;
long-only/short/leverage e base currency;
risk budget e utility;
provider/versione/licenza dei dati;
adjusted/total-return convention;
cut-off development e reveal authority;
fill, slippage, capacity e market-impact model;
family-wise correction e trial hierarchy;
metodo HAC/bootstrap e block length;
gestione della sovrapposizione QQQ/componenti e MSTR/crypto;
sincronizzazione calendari equity/crypto;
dependency lock;
uso consentito dei risultati legacy per progettare il protocollo;
criterio di "sufficient breadth" per H1.

PROBLEMA DI GOVERNANCE — Le decisioni non devono essere "lasciate all'auditor". Claude deve proporre una posizione motivata; Filippo decide i mandati; l'auditor tenta di falsificare la proposta.

### 18. Nuove affermazioni o contraddizioni

VERIFIED — Sono presenti:

"Tutti gli otto blocker risolti" è falso: il blocker architetturale persiste.
DSR e PSR sono conflati.
Robustness test e confirmatory evidence sono messi sullo stesso piano.
La metodologia point-in-time è chiamata implementabile prima della scelta del provider.
Plugin post-validazione e shadow precoce sono incompatibili.
H6 è contemporaneamente accanto a H2 e ancora da decidere.
Soglie economiche sarebbero "derivate" dalla power analysis.
Il fallback case study è incompatibile con il requisito H1 point-in-time.
"Baseline has won" in Phase 5 non ha un comparatore definito.
Il limite "più della metà non riproducibile ⇒ tutti i risultati void" è una soglia arbitraria. Ogni risultato deve essere ammesso o escluso individualmente.
R1.1 richiede riproduzione esatta senza snapshot raw né dipendenze bloccate.
Il master context definisce la roadmap contemporaneamente "authority" e "under audit".

## Problemi metodologici

### Il +87.15% non è Buy & Hold

VERIFIED — Il codice calcola ogni giorno la media dei rendimenti degli asset:

`dynamic_universe_final_comparison.py` Ln 93–103

```python
def static_equal_weight(p):
    x=p.dropna(subset=["NextRet"]).copy()
    g=x.groupby("Date")["NextRet"].agg(["count","mean"]).reset_index()
    g=g[g["count"]==len(ASSETS)].copy()
    g["GrossReturn"]=g["mean"]
    g["Return"]=g["GrossReturn"]
    if len(g):
        g.loc[g.index[0],"Return"]-=COST_PER_SIDE
    g["Turnover"]=0.0
```

Questo è un portafoglio equal-weight ribilanciato giornalmente, non static Buy & Hold.

VERIFIED — Il turnover viene impostato a zero nonostante il ribilanciamento implicito. Il confronto con Dynamic Top-K non è cost-matched.

### Look-ahead nel confronto dynamic universe

VERIFIED — Lo score usa Close e Volume completi del giorno d, seleziona al giorno d e accredita il rendimento close-to-close d → d+1.

INFERRED — Senza lag del segnale o execution al next open, il confronto incorpora una fill assumption non realizzabile dopo il completamento della barra.

Questo rende improprio chiamare il confronto "fair" prima di una nuova simulazione corretta.

## Problemi statistici

VERIFIED — La riga DSR è in realtà una formulazione PSR-like. DSR richiede uno Sharpe di riferimento legato al massimo atteso fra trial; il confronto appaiato richiede invece la distribuzione congiunta dei rendimenti.
VERIFIED — MDE statistico ed effetto economicamente utile sono concetti distinti.
VERIFIED — Non è definita la correzione gerarchica fra famiglie, parametri, universi e protocolli.
VERIFIED — q=252 non può essere applicato automaticamente a strategie crypto giornaliere o pannelli con calendari misti.
VERIFIED — Trial ledger senza definizione di trial non corregge il multiple testing.
UNKNOWN — Non è verificabile se esista un historical block davvero non osservato.
UNKNOWN — Non è verificabile se confronti appaiati esistenti siano significativi.

## Problemi di implementazione e repository

VERIFIED:

HEAD locale: 06006e3;
origin/main: 640ca0e;
i due commit remoti modificano soltanto:
ml_validation_report.json;
portfolio_state.json;
scout_signals.json;
28 file Python totali;
17 sono effettivamente script di ricerca/backtest, quindi il vecchio conteggio 17 era corretto sotto questa classificazione;
111 file tracciati;
nessun raw dataset parquet/feather/pickle/joblib;
1 chiamata esplicita auto_adjust=True;
7 chiamate esplicite auto_adjust=False;
4 download/history senza valore esplicito;
workflow e ambiente non bloccano le versioni delle dipendenze;
il workflow installa ogni volta le ultime versioni disponibili;
31 pct_change() senza fill_method.

VERIFIED — Il run #10 è internamente ricalcolabile dai CSV e coincide esattamente con summary:

equity 7980.019492;
return -20.1998%;
DD -45.5681%;
Sharpe -0.2496016;
302 trade;
win rate 49.3377%;
PF 0.878734.

UNKNOWN — Non è riproducibile dal raw market data perché il raw snapshot non è conservato.

VERIFIED — Il master context riporta per Static 18:

DD -38.11%.

Il CSV riporta invece:

CAGR +38.1103%;
max drawdown -27.1968%.

È stato scambiato il CAGR con il drawdown.

### Residui contraddittori nei documenti

VERIFIED — BOT_TRADING_V2_MASTER_CONTEXT.md contiene ancora:

"Keep V1 cron paused" nella sezione Immediate next task, nonostante la revoca;
roadmap definita "authority" mentre è ancora proposal under audit;
simple trend/momentum come baseline, mentre la roadmap colloca H2 solo fra i candidati;
"same engine where possible" contro "identical core" della roadmap;
drawdown statico errato -38.11%.

VERIFIED — AUDIT_RESULT_001.md non riproduce fedelmente il mio testo originale sul DSR: la ricostruzione usa P(DSR/PSR > 0) > 0.95; il testo originale richiedeva una probabilità DSR/PSR superiore a 0.95 rispetto a un riferimento esplicito e con conteggio dei trial. La roadmap introduce una terza formulazione, ancora ibrida.

## Valutazione delle tre scelte contestate

### Soglie rinviate a 0C

APPROVATO CON LIMITI — È meglio rinviarle che inventarle, ma ciò impedisce di chiamare la v2 "protocollo eseguibile". Phase 0C deve congelarle prima di qualunque risultato candidato.

### Errori storici mantenuti nel testo

NON APPROVATO — L'audit trail deve conservare gli errori; il documento normativo deve contenere solo la regola corrente. Valori ritirati e formule errate vanno spostati nel revision record o in appendice. L'attuale <=25% indicativo continua inoltre ad ancorare una soglia già giudicata arbitraria.

### Undici decisioni lasciate aperte

NON APPROVATO COME PROTOCOLLO — È corretto renderle visibili, ma servono:

proposta raccomandata;
alternative;
owner della decisione;
fase entro cui deve essere chiusa;
conseguenza se resta irrisolta;
nuovo audit prima dell'adozione.

## Correzioni richieste

### Bloccanti

Separare formalmente development, robustness e confirmation evidence.
Correggere il lifecycle dei plugin: experimental prima, deployable dopo validazione.
Riscrivere DSR/PSR e test appaiato come criteri distinti.
Trasformare risk mandate e placebo in gate quando appropriato.
Rimuovere il +87.15% dalla categoria Buy & Hold e dichiararlo risultato invalido/non comparabile fino a rerun.
Definire il ramo case study come scelta esplicita con restrizioni sulle conclusioni.
Proporre e auditare le decisioni aperte prima delle fasi che le richiedono.
Definire snapshot, dependency lock e data-version contract.
Correggere le contraddizioni nei documenti allineati.
Rimuovere la regola arbitraria "oltre metà non riproducibile ⇒ tutto void"; valutare ogni artefatto separatamente.

### Migliorative

Spostare tutte le ritrattazioni storiche in appendice/audit trail.
Inserire nel provenance ledger le finestre CSV esatte, non aggregate.
Distinguere baseline, diagnostiche e attribution.
Definire una canonical trend baseline distinta dalla ricerca H2.
Trasformare la tassonomia delle barre in quality flags ortogonali.

## Elementi approvati

VERIFIED — Stato "proposal under audit".
VERIFIED — Trial ledger e contamination map.
VERIFIED — Snapshot raw immutabili e versionati.
VERIFIED — Sleeve separati e dati survivorship-free.
VERIFIED — Pannello sbilanciato/coorti anziché falso pannello 2010–2024.
VERIFIED — Comparatore primario preregistrato.
VERIFIED — Test appaiati invece di confronto fra CI indipendenti.
VERIFIED — Ricollocazione del volatility sizing.
VERIFIED — ML subordinato a valore incrementale.
VERIFIED — Divieto di tuning dopo reveal.
VERIFIED — Forward shadow append-only con policy di peeking.
VERIFIED — Distinzione fra infrastructure core e adapter, purché venga corretto il lifecycle dei plugin.

## Punti non verificabili

UNKNOWN — Provenienza di ML ON/OFF e AUC: gli artefatti completi non sono presenti.
UNKNOWN — Estensione reale della contaminazione prima di R0.1.
UNKNOWN — Esistenza di un blocco storico realmente non osservato.
UNKNOWN — Disponibilità e qualità di un provider survivorship-free.
UNKNOWN — Significatività dei confronti appaiati.
UNKNOWN — Corretta riproduzione del +87.15%, perché manca il raw snapshot.
UNKNOWN — Data oggettiva del regime break MSTR.
UNKNOWN — Reale capacità/costi/slippage senza mandato e modello di mercato.

Nessun file è stato modificato, creato o messo in staging durante l'audit.
