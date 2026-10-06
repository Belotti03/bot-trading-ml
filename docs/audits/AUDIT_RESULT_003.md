# AUDIT RESULT 003

**Oggetto:** `docs/V2_RESEARCH_ROADMAP.md` versione 3
**Richiesta:** `docs/audits/AUDIT_REQUEST_003.md`
**Auditor:** GPT-5.6 Sol, audit indipendente e avversariale
**Data:** 2026-10-06
**File modificati dall'auditor:** nessuno

**Fedeltà:** testo verbatim come ricevuto. L'unico intervento è la
delimitazione markdown della tabella delle dieci correzioni e della
tabella delle 24 posizioni, che nella consegna originale erano allineate
con tab. Nessuna parola è stata aggiunta, rimossa o riordinata.

---

VERDETTO: APPROVED WITH CHANGES
La riformulazione della natura del documento è una risposta accettabile al motivo del rigetto della v2. La v3 non va respinta per lo stesso motivo.

La v2 è stata respinta perché si presentava come protocollo eseguibile mentre non lo era. La v3 dichiara di essere un piano più posizioni proposte, e colloca il protocollo all'uscita di 0A–0C. VERIFIED — questo è coerente con quanto chiesto nell'audit 002: non inventare soglie arbitrarie, congelarle prima dei candidati, e non chiamare "protocollo" un documento che ancora non lo è.

Quella riformulazione non rende adottabile il piano così com'è. Restano blocker nuovi o residui. La Fase 0A metodologica non può partire su questo testo. R0.1 può essere autorizzato indipendentemente.

Nessun file è stato modificato.

## Domanda preliminare

VERIFIED — Rifiutare di nuovo la v3 perché "non è un protocollo eseguibile" sarebbe un errore di categoria. Un piano può essere approvato se: (i) non si finge protocollo; (ii) i decision gate sono veri vincoli; (iii) le posizioni non contraddicono i gate; (iv) i documenti allineati non riammettono le tesi ritirate.

La v3 soddisfa (i). Fallisce parzialmente (ii)–(iv).

## Le dieci correzioni bloccanti dell'audit 002

| # | Correzione | Esito |
| --- | --- | --- |
| 1 | Gerarchia development / robustness / confirmatory | RISOLTA nel documento. NON RISOLTA nei documenti allineati, che riammettono le fonti robustness come se fossero evidenza primaria. |
| 2 | Lifecycle plugin experimental → validated → deployable | RISOLTA per implementazione vs promozione. SPOSTATA sul punto shadow: lo shadow resta classificato confirmatory e viene aperto agli experimental dalla Fase 1. |
| 3 | DSR, PSR e test appaiato distinti | RISOLTA in §2.2. |
| 4 | Risk mandate e placebo come gate | RISOLTA per drawdown, concentrazione, leva e placebo. Il fallimento su tutti i regimi resta diagnostica, non gate. |
| 5 | +87,15% rimosso da Buy & Hold | RISOLTA. |
| 6 | Case study come ramo esclusivo e H1 bloccato | RISOLTA come specifica. La proposta D1 di "iniziare da B" mentre D15 resta aperta sposta il rischio di inerzia. |
| 7 | Proporre e auditare le decisioni prima delle fasi | RISOLTA come processo (questa è quella revisione). D4 e D22 sono posizioni incomplete. |
| 8 | Snapshot, lock, data-version contract | RISOLTA come requisito di piano. VERIFIED — nel repository è ancora assente. |
| 9 | Contraddizioni nei documenti allineati | RISOLTA rispetto all'elenco 002 (cron, authority, CAGR/DD, trend/motore marcati UNRESOLVED). NON RISOLTA rispetto alla v3: i testi allineati contraddicono §1 e §2.1. |
| 10 | Adjudication individuale, niente soglia 50% | RISOLTA. |

"Where addressed in v3" è più onesto della v2. Lo spostamento mascherato da risoluzione ricompare su shadow, Branch B e allineamento documentale.

## Blocker residui

Shadow confirmatory vs playground experimental. §1 classifica il forward shadow come unica fonte confirmatory incondizionata. §5.2 permette a un plugin experimental di "run in shadow" con sola scheda di preregistrazione. §9 fa partire lo shadow dalla Fase 1. VERIFIED — più candidati sullo stesso periodo live distruggono lo status confirmatory. Infrastruttura shadow ≠ coorte confirmatory congelata.

Gate placebo mal definito. "The candidate lies outside the pre-registered quantile" è vero anche per un risultato significativamente peggiore del null. Serve la coda superiore (o una regione di rifiuto preregistrata a una coda) sulla metrica primaria.

D1 contraddice il gate 0B e D15. D15 deve chiudersi in 0B. D1 propone di far procedere 0C/1/2 sul ramo B mentre la valutazione vendor di D15 corre in parallelo. I due testi non possono valere insieme.

Documenti allineati contraddicono la v3. BOT_TRADING_V2_MASTER_CONTEXT.md e RESEARCH_LOG.md ripetono che gli Sharpe individuali "non sono distinguibili da zero" e che nested walk-forward, blocchi storici, mercati esterni, leave-one-cohort e test appaiati sono "admissible", senza la gerarchia §1.

D4 e D22 non sono posizioni complete. D4 non elenca i criteri di eligibility. D22 non propone lo split di capitale fra sleeve.

## Risposte alle 21 domande

### 1. Natura del documento

Accettabile come risposta al rigetto della v2. Non sufficiente da sola per APPROVED.

### 2. Gerarchia delle evidenze

VERIFIED — La tripartizione è quella richiesta. La regola "robustness può solo bloccare, mai promuovere" è difendibile.

Correzioni: (a) un blocco storico quarantinato è confirmatory, non robustness; (b) un paired test preregistrato su dati non usati per progettare l'ipotesi può essere confirmatory; sui dati già visti resta comparative inference. INFERRED — "Robustness non può mai concedere promozione" è corretta per la promozione a validated/deployable, non per uccidere un candidato in development.

### 3. DSR / PSR / paired

VERIFIED — Ora sono tre criteri distinti, con riferimenti giusti: benchmark Sharpe; expected maximum fra trial; distribuzione congiunta delle due serie. PSR da solo non basta. La formula esplicita di Bailey/López de Prado resta da scrivere in 0C: per un piano è accettabile.

### 4. Vincolo §2.1 sullo Sharpe plurale

Sufficiente nella roadmap. Insufficiente nei documenti allineati, che riaffermano il plurale come fatto.

VERIFIED — Con SR=1.155, q=252, T=1.941: SE=0.7187, intervallo 95% [-0.254, 2.564]. La v3 adotta questi numeri, non più T=2.

### 5. Calendari misti e q

VERIFIED — Un q per sleeve e metriche di portafoglio sull'intersezione è la direzione corretta. "Crypto held unchanged on equity-closed days, no synthetic returns" è coerente con il difetto pct_change. D22 non fissa lo split: la regola di calendario è approvabile, l'allocazione no.

### 6. Contratto dati e R1.1

VERIFIED — Nessun dataset raw .parquet/.feather/.pkl/.joblib/.h5/.sqlite. Il workflow installa ancora pacchetti non pinnati. Un risultato senza snapshot+lock+version contract non è ammissibile: corretto.

Restituire R1.1 come coerenza interna, non riproduzione da sorgente, è l'unico criterio onesto per il run #10. Non va chiamato "reproduction".

### 7. Quality flag

INFERRED — L'elenco copre i buchi della tassonomia v2. Non è dimostrabilmente completo.

stale_value: valuation sì, execution no — corretto.

Troppo stretto: qualsiasi altro flag blocca il segnale, incluso corporate_action e half_day_session. Un split correttamente aggiustato non deve azzerare il segnale. Controproposta: flag che bloccano vs flag che annotano, preregistrati.

### 8. Rami A/B e H1

VERIFIED — §4.2, Fase 3 e tabella ipotesi bloccano H1 sotto B. D8 può nominare il comparatore di H1 come specifica dormiente.

NON coerente: D1 vuole 0C/1/2 su B mentre D15 è ancora aperta.

### 9. Lifecycle a tre stati

Risolve la contraddizione implementazione/validazione. Non risolve occupancy dello shadow confirmatory.

### 10. Conformance suite

VERIFIED — I otto punti dell'audit 002 sono elencati. Elencarli non è implementarli; per un piano basta. "One identical core" resta UNKNOWN fino al pass della suite: corretto.

### 11. Baseline / diagnostiche / attribuzione

VERIFIED — La separazione è quella richiesta. La trend baseline canonica è distinta da H2. Volatility sizing è overlay sullo stesso segnale. Placebo è sia diagnostica (§6.2) sia gate (§7.2): accettabile se il gate resta vincolante.

### 12. Tre livelli §7

Chiude il buco drawdown/concentrazione/placebo. Non chiude "fallisce ogni regime rilevante". Se i regimi sono preregistrati nel mandato, almeno uno deve essere inferential gate o hard gate. Altrimenti resta una via di fuga.

### 13. Placebo e D10

Lo schema (block bootstrap stazionario, allineamento cross-section, frequenza trade) è adeguato come direzione. Il test "outside quantile" no. Vedi blocker 2.

### 14. Stop criteria e INCONCLUSIVE

Molto migliorati. Ancora ambiguo: INCONCLUSIVE "consumes its trial budget" poi torna in coda. Controproposta: un esito INCONCLUSIVE consuma un trial; una ri-coda con più dati è un nuovo trial; i budget di famiglia non si riallocano a nuovi target senza audit.

Manca un kill esplicito per violazione della freeze rule di §2.5.

### 15. Trial e DSR

D5 è calcolabile in linea di principio. Una walk-forward a più fold deve contare come un trial se la metrica è una sola valutazione del tuple, o come N se si sceglie il fold. Va detto. La griglia di sensitivity va nel ledger anche se "never selected on", altrimenti il DSR è sottostimato.

### 16. Le 24 posizioni

Vedi sezione dedicata sotto.

### 17. Decisioni implicite non dichiarate

Almeno: timeframe (daily ereditato); orizzonte del segnale V2 diverso dal target 1-day di V1; ammissione di ETF (QQQ, GLD) nel case study; niente futures/opzioni; unità di osservazione del trial walk-forward; policy di peeking sullo shadow (rimandata a 0A senza bozza); freeze dei budget di famiglia contro riallocazione.

D11 assente è dichiarato. Il conteggio "24, numerate D1–D25" è aritmeticamente corretto.

### 18. Adjudication §12

La regola individuale è corretta. Le classificazioni §12.3 sono corrette come status, con una correzione empirica sulla doppia riga: ora è determinabile, non più UNRESOLVED. Vedi domanda 19.

### 19. Doppia riga TopK 18

VERIFIED — Non è un mistero metodologico irrisolto. Sono due funzioni diverse in dynamic_universe_fair_comparison.py, più un bug sui costi.

Riga 487 obs, +87,15%, turnover 0,205%: è simulate(panel, k=18), non static_18(). Tiene solo i giorni in cui tutti e 18 hanno Score e NextRet. Selezionare top-18 su 18 asset è equal-weight su calendario da pannello completo. I costi sono turnover * 0.0015, quindi quasi zero dopo il primo giorno. Coincide con dynamic_universe_final_comparison.csv "Static 18 equal-weight".

Riga 711 obs, −16,26%, DD −57,13%, turnover 0: è static_18(with_costs=True). Media NextRet su ogni data con almeno un asset, quindi include weekend crypto. Il commento dice "one initial allocation cost only"; il codice fa g["Return"] -= COST_PER_SIDE su tutte le 711 righe.

VERIFIED — (1-0.0015)**711 ≈ 0.344. Equity senza costi 24321,13 × 0,344 ≈ 8373, coincidente con 8373,71. Il segno negativo è quasi interamente il bug dei costi, non un altro universo economico.

Senza costi, le due static differiscono comunque: +87,43% (487) vs +143,21% (711). INFERRED — la differenza residua è il mix weekend crypto / giorni incompleti, non solo i costi.

Benchmark statico inteso nei documenti: la riga 487 / +87,15%, perché è quella citata e quella riprodotta da static_equal_weight() in dynamic_universe_final_comparison.py con count==len(ASSETS). Resta INVALID come Buy & Hold: è equal-weight ribilanciato giornalmente, con look-ahead close-to-close sulla gamba dinamica.

### 20. Nuove affermazioni / contraddizioni

VERIFIED:

D1 vs gate 0B/D15;
D8 Close by: 1 vs tabella Fase 0C che elenca D8;
D10 Close by: 0C vs gate Fase 1 = D9, D10;
"any other flag blocks signal generation";
shadow experimental = confirmatory;
master context/research log vs §1 e §2.1;
v3 dice "Twenty-four decisions" e il pacchetto 003 parla una volta di 25.

### 21. R0.1 indipendente

Sì. È forense, non adotta metodologia, e ora deve anche registrare la spiegazione della doppia riga. Non può "scegliere" quale riga sia il benchmark vero: può solo attribuire ciascuna riga alla funzione che l'ha prodotta.

## Problemi metodologici

Usare i risultati legacy per disegnare il protocollo (D24) è un canale di snooping. La v3 lo ammette. INFERRED — un conteggio a posteriori dei trial mentali non sarà completo; il DSR andrà deliberatamente conservativo.
Ramo B sul paniere dei 18 vince ex-post: H2/H3/H4 restano case study. VERIFIED — questo è dichiarato. Il rischio è promuovere comunque un edge specifico di quel paniere.
Look-ahead dynamic universe: confermato di nuovo nel codice (Score al close di d, NextRet = close d+1).
features.py crea il target e poi fa dropna() sull'intera riga: l'ultima barra perde il target, ma le barre con NaN di volume vengono eliminate in modo diverso dal live. INFERRED — un altro asse di non-comparabilità V1.

## Problemi statistici

Placebo a due code simmetriche.
"Paired CI excludes zero" e "economic effect size" sono gate diversi: con T≈2 anni il primo produrrà molti INCONCLUSIVE. Va detto esplicitamente, altrimenti si uccideranno ipotesi sotto-potenza.
DSR richiede N effettivo; D5 non dice come si ottiene N da fold walk-forward, griglie e famiglie.
q=252 sullo Sharpe 1.155 è ancora un'approssimazione da calendario equity per un paniere con crypto.

## Problemi di implementazione

VERIFIED, ricalcolato/ispezionato:

52 CSV: 20 backtest_results, 21 portfolio_backtest_results, 10 dynamic-universe in root, 1 trading_log.csv;
31 pct_change() in 15 file, zero fill_method;
auto_adjust: 1 True, 7 False, 4 impliciti (model_engine.py .history(), main.py ATR, main.py SPY, data_loader.py);
run #10: summary invariato, 7980.019492, −20.20%, DD −45.57%, Sharpe −0.2496, 302 trade, WR 49,34%, PF 0,8787;
run_bot.yml senza lock;
nessun snapshot raw.

## Correzioni richieste

### Bloccanti

Separare shadow infrastructure (Fase 1) da confirmatory shadow cohort: una sola strategia congelata, append-only, peeking sealed fino al reveal di Filippo. Gli experimental paper run sono development.
Riscrivere il gate placebo: il candidato deve superare il quantile superiore preregistrato della metrica primaria.
Allineare D1/D15/gate 0B: 0C non parte finché il ramo è scelto; se si sceglie B, registrarlo come ramo corrente con data di revisione, non "mentre D15 è aperta".
Allineare master context e research log a §1 e §2.1.
Completare D4 (lista di eligibility) e D22 (split numerico proposto, anche se Filippo può cambiarlo).
Allineare i Close by di D8/D9/D10 con la tabella delle fasi.

### Migliorative

Distinguere flag bloccanti vs annotativi.
Kill esplicito per violazione della freeze §2.5.
Chiarire conteggio trial walk-forward e divieto di riallocare budget di famiglia.
Regime preregistrato come gate se il mandato lo richiede.
Aggiornare §12.3: doppia riga spiegata, non UNRESOLVED.
Q7 del research log: la domanda sul selection bias resta, ma non può più poggiare sul +87,15% come B&H.

## Le 24 posizioni

| ID | Giudizio | Nota / controproposta |
| --- | --- | --- |
| D12 estimand | Approvo la struttura | Owner Filippo sui numeri. Excess net Sharpe vs comparatore è un estimand lecito. |
| D13 long-only / EUR | Approvo come default proposto | Owner Filippo. |
| D14 25% / 15% / 20% | Approvo la forma, non i numeri | Sono mandati, non statistica. L'auditor non li "deriva". |
| D15 provider | Approvo con modifica | Deve chiudere in 0B prima di 0C. Yahoo+snapshot è lecito per B. |
| D17 reveal | Approvo | Solo Filippo; Claude non rivela. |
| D1 ramo | Respingo | Controproposta: in 0B scegliere B oppure A. Se B, è il ramo corrente, H1 off, data di revisione preregistrata. Vietato avviare 0C "mentre si valuta il vendor". |
| D2 sleeve / quarterly | Approvo | Soglia liquidità in 0C va dichiarata prima dei candidati. |
| D3 pannello sbilanciato | Approvo | |
| D4 eligibility | Respingo come incompleta | Controproposta: criteri concreti, es. seasoning 252g, liquidità, nessun cambiamento di oggetto economico definito ex ante (es. equity il cui asset sottostante supera X% del NAV per Y mesi). Niente break detection ex-post. |
| D5 trial | Approvo con modifica | Definire fold walk-forward; ledger automatico include sensitivity. |
| D6 origini soglie | Approvo | Scelta metodologica corretta: non sostituire arbitrarietà con altra arbitrarietà. |
| D7 durata shadow | Approvo la forma | I numeri restano 0C. |
| D8 comparatori | Approvo | Congelare in 0C, non in Fase 1. H1 dormiente sotto B. |
| D9 merge H6→H2 | Approvo | Un'ipotesi economica, un budget. |
| D10 permutazioni | Approvo lo schema, respingo il test associato in §7.2 | Coda superiore, non "outside". |
| D16 total return | Approvo | Unadjusted accanto per execution; mai auto_adjust implicito. |
| D18 next-open + impact | Approvo | Necessario per H4. |
| D19 gerarchia | Approvo | |
| D20 HAC + bootstrap | Approvo | |
| D21 no overlap QQQ | Approvo | |
| D22 calendari | Approvo i calendari, respingo come posizione completa | Manca lo split. Controproposta esplicita, es. 70/20/10 equity/crypto/commodity, owner Filippo. |
| D23 lock | Approvo | |
| D24 legacy solo ipotesi | Approvo | Contare quel canale nel DSR in modo conservativo. |
| D25 breadth H1 | Approvo | Sotto B non si esegue, senza caveat. |

Proporre anche i mandati di Filippo è corretto. L'errore è presentare come chiuse posizioni senza contenuto numerico o operativo.

## Elementi approvati

Status "proposal under audit, not authority".
Protocollo eseguibile solo dopo freeze 0A–0C.
Gerarchia evidenze nel corpo della roadmap.
DSR ≠ PSR ≠ paired test.
Contratto dati e kill su irriproducibilità.
Rami A/B e H1 incompatibile con B.
Lifecycle experimental / validated / deployable per il codice.
Trend baseline canonica distinta da H2.
Volatility sizing come overlay a pari target vol, con QLIKE.
Adjudication individuale.
Appendice A invece di errori nel testo normativo.
R0.1 indipendente.
Governance: Claude propone, Filippo decide i mandati, auditor falsifica.

## Non verificabile

UNKNOWN — provenance ML ON/OFF e AUC (artefatti assenti).
UNKNOWN — estensione reale della contaminazione prima di R0.1.
UNKNOWN — esistenza di un blocco storico davvero quarantinato.
UNKNOWN — qualità/prezzo di un vendor survivorship-free.
UNKNOWN — se un eligibility rule generale escluderebbe MSTR.
UNKNOWN — capacità e impact reali.
UNKNOWN — completezza del conteggio trial a posteriori per D24.

## R0.1

Sì, autorizzabile ora, indipendentemente da questa roadmap. Scope minimo:

provenance per-file;
attribuzione delle due righe TopK 18 alle due funzioni e al bug -= COST_PER_SIDE;
inventario auto_adjust / feature set / costi;
nessuna conclusione strategica.

Non è Fase 0A. Non adotta soglie, universo o engine.

## Cosa deve cambiare perché diventi APPROVED

Non servono le soglie numeriche nel documento. Servono, nel piano:

shadow confirmatory = una coorte congelata, non un runtime experimental;
placebo a una coda;
D1/D15/0B non contraddittori;
master context e research log allineati a §1 e §2.1;
D4 e D22 con contenuto operativo;
tabella fasi allineata ai Close by.

Dopo queste correzioni, una v4 può essere approvata come piano. Il protocollo eseguibile resterà l'output di 0A–0C, con freeze prima di qualsiasi candidato.
