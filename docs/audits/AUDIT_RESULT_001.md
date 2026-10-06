# AUDIT RESULT 001

**Oggetto:** `docs/V2_RESEARCH_ROADMAP.md` versione 1
**Auditor:** GPT-5.6 Sol, audit indipendente e avversariale
**Data:** 2026-10-06
**Richiesto da:** Filippo
**File modificati dall'auditor:** nessuno

## VERDETTO

**APPROVED WITH CHANGES**

Direzione generale valida. Non approvabile come protocollo statistico
eseguibile nella forma della versione 1. Otto blocker.

## AVVERTENZA SULLA FEDELTÀ DI QUESTO DOCUMENTO

Questo file è una **ricostruzione**, non il testo verbatim dell'audit.

La procedura operativa di `docs/CURSOR_CLAUDE_WORKFLOW.md` è stata
introdotta *dopo* questo audit, quindi il risultato non fu salvato nel
repository al momento della ricezione: fu incollato direttamente in
chat. Ho verificato la trascrizione della sessione
(`0cb37190-7724-4fea-b218-b0ac33b5f6e0.jsonl`) e il messaggio utente
corrispondente conserva soltanto il blocco di contesto di sistema, senza
il testo incollato. Il verbatim non è quindi recuperabile da lì.

Il contenuto che segue è la sintesi dei rilievi come recepiti da Claude,
ed è lo stesso insieme di correzioni applicate in roadmap v2. Non deve
essere citato come testo letterale dell'auditor. **Se il testo originale
è ancora disponibile, va incollato qui a sostituzione integrale di
questo documento**, mantenendo l'avvertenza solo se la sostituzione è
parziale.

Audit 002 e successivi saranno salvati verbatim al momento della
ricezione, come previsto dalla procedura.
`docs/audits/AUDIT_RESULT_002.md` è verbatim.

**Discrepanza accertata e corretta.** L'auditor, aprendo l'audit 002, ha
rilevato che questa ricostruzione riportava il requisito DSR in una
forma diversa dalla sua: diceva `P(DSR/PSR > 0) > 0.95` anziché una
probabilità superiore a 0.95 rispetto a un riferimento esplicito e con
conteggio dei trial. Il punto è stato corretto nel blocker 5 qui sotto,
citando l'audit 002 come fonte. Questo conferma che il documento va
trattato come trascrizione non fedele: possono esistere altre
discrepanze non ancora rilevate.

## BLOCKER

### 1. Formula dello standard error dello Sharpe applicata male

La roadmap v1 usava `SE(SR) ~= sqrt((1 + SR^2 / 2) / T)` con uno Sharpe
annualizzato e `T` in anni. La forma è valida solo quando Sharpe e
conteggio delle osservazioni hanno la stessa frequenza. Con `q`
osservazioni per anno l'espressione corretta è

    SE(SR_annuo) ~= sqrt((1 + SR_annuo^2 / (2q)) / T_anni)

Per SR 1.155, `q` 252, `T` 2 anni il risultato è SE ~= 0.71 e intervallo
95% ~= [-0.23, 2.54], non SE 0.91 e [-0.6, 2.9].

La conclusione qualitativa sopravvive, perché l'intervallo corretto
contiene ancora lo zero. La derivazione che l'aveva prodotta no.

### 2. Due affermazioni eccessive

**"Ogni risultato è indecidibile"** non segue dall'ampiezza degli
intervalli sui singoli Sharpe. Due strategie valutate sugli stessi
giorni producono serie appaiate e correlate, e l'incertezza della loro
*differenza* può essere molto minore di quella dei due Sharpe presi
separatamente. Formulazione corretta: i risultati attuali non
forniscono evidenza confermativa finché non sono stati calcolati
intervalli robusti e test appaiati con correzione per selezione.

**"Il futuro è l'unico holdout"** promuove lo shadow trading a unica
fonte di validazione primaria. Con dati giornalieri servirebbero anni
per distinguere Sharpe moderati, quindi non può essere l'unica fonte di
evidenza. Sono utilizzabili anche: walk-forward nidificato; blocchi
storici mai usati; asset o mercati esterni congelati prima dell'uso;
leave-one-cohort-out e leave-one-asset-class-out; test appaiati su
configurazioni preregistrate.

Inoltre l'assunzione IID normale non è sufficiente nemmeno per la
formula corretta: servono asimmetria, curtosi in eccesso,
autocorrelazione e dipendenza cross-asset, stimate con standard error
HAC o block bootstrap.

### 3. Il periodo 2010-2024 non è realizzabile

Nel repository non esiste alcun dataset grezzo 2010-2024; i dati
persistiti iniziano prevalentemente nel 2021 o nel 2025. Un pannello
uniforme sui 18 asset attuali è impossibile: ARM quotata 2023, COIN
2021, PLTR 2020, ETH con storia molto più breve, BTC non coperto
integralmente dal 2010 dalle fonti comuni, e MSTR con un cambiamento
radicale di esposizione economica a metà storia.

Va sostituito con storia massima disponibile, coorti per data di
quotazione e pannello esplicitamente sbilanciato. MSTR richiede una
rottura di regime documentata.

### 4. L'universo point-in-time non è implementabile con Yahoo Finance

Yahoo da solo non consente di ricostruire correttamente membership e
storia dei delisting. Serve una metodologia esplicita: universi
investibili **separati per sleeve** (azioni USA, ETF/commodity, crypto),
perché un unico ranking di capitalizzazione fra questi gruppi non è
economicamente coerente; membership, capitalizzazione e liquidità
disponibili a `t-1`; frequenza di ribilanciamento preregistrata; filtri
di età di quotazione e liquidità; mantenimento degli asset delistati con
i relativi delisting return e corporate action; nessuna rimozione
retroattiva; dati survivorship-free per le azioni e listing storici per
le crypto.

Se tali dati non sono disponibili, va dichiarato esplicitamente che
l'universo attuale è un **case study** e le conclusioni vanno limitate a
quel paniere.

La roadmap v1 trattava inoltre come quasi accertato che il +87,15% di
Buy & Hold statico sia spiegato dalla selezione retrospettiva. È una
**ipotesi**, non una conclusione.

### 5. Criteri di accettazione in parte mal definiti o arbitrari

- *Deflated Sharpe*: va richiesta una probabilità DSR/PSR superiore a
  0.95 **rispetto a un riferimento esplicito** e **con conteggio dei
  trial**. Il DSR richiede uno Sharpe di riferimento legato al massimo
  atteso fra i trial; il confronto appaiato richiede invece la
  distribuzione congiunta dei rendimenti, quindi sono due criteri
  distinti e non vanno conflati. Servono inoltre asimmetria, curtosi,
  autocorrelazione e numero **effettivo** di trial correlati.
  *Formulazione corretta il 2026-10-06 su indicazione dell'auditor in
  `AUDIT_RESULT_002.md`: la ricostruzione precedente diceva
  `P(DSR/PSR > 0) > 0.95`, che non è ciò che l'audit 001 richiedeva.*
- *OOS >= 0.5 x IS*: **da eliminare**. È arbitrario e instabile quando
  IS è vicino a zero o negativo. Sostituire con una soglia OOS assoluta
  più un intervallo di confidenza sul degrado.
- *Vantaggio >= 0.3 Sharpe*: da modificare. Deve derivare da analisi di
  potenza e da un intervallo sulla differenza appaiata.
- *Max drawdown <= 25%*: da modificare. È un mandato di rischio
  economico, non prova di edge. Confrontare a pari rischio.
- *Costi raddoppiati*: da modificare. Usare costi empirici, scenari
  multipli e un **break-even cost** riportato; definire cosa significa
  "sopravvive".
- *Rolling 12 mesi positivo nel 60% delle finestre*: da modificare. Le
  finestre sovrapposte non sono indipendenti e il 60% è arbitrario.
  Usare blocchi e regimi preregistrati con intervalli di confidenza.
- *Nessun asset oltre il 40% del PnL*: da modificare. È instabile con
  PnL totale piccolo o negativo. Aggiungere HHI, contributo al rischio e
  leave-one-asset-out.
- *Placebo*: da modificare. Serve una **distribuzione** di permutazioni
  che preservi autocorrelazione, struttura cross-sectional e frequenza
  dei trade, non una singola esecuzione randomizzata.

Inoltre "il fallimento di un solo test equivale al kill" è troppo rigido
mentre molte soglie sono arbitrarie: separare gate primari da
diagnostiche secondarie. E "più di un ri-tuning" non è verificabile
senza una definizione formale di trial e un ledger automatico.

### 6. Contraddizione fra separazione dei livelli, motore condiviso e shadow precoce

La v1 affermava insieme che l'implementazione è autorizzata solo dopo
l'holdout, che lo shadow trading in avanti parte presto (e quindi
richiede un'implementazione) e che backtest e live condividono il
motore. Le tre cose non possono valere contemporaneamente.

Distinzione corretta: infrastruttura e motore generico si implementano
**per primi**, perché non sono decisioni strategiche; i plugin di
strategia si promuovono solo dopo validazione; core identico per
feature, segnali, portafoglio e rischio; adapter separati per
simulatore storico, paper e live.

"Esattamente un motore" è attualmente un requisito documentale, non una
proprietà verificata: diventa verificato solo con replay deterministico
e test di conformance che producano ordini identici da snapshot
identici.

### 7. H5 non è una famiglia di alpha

La previsione di volatilità è costruzione di portafoglio e di rischio,
non alpha direzionale. Il prior sulla prevedibilità della volatilità è
solido, ma H5 va spostata fra le **baseline di sizing e rischio**, prima
che si testino le famiglie di alpha. Il criterio della v1 ("drawdown
ridotto di 10 punti percentuali a pari rendimento") era arbitrario e
difficile da testare: il confronto corretto è a pari rischio, o sulla
frontiera rischio/rendimento.

### 8. Da H2 a H6 mancano criteri completi e omogenei

La v1 dava criteri espliciti solo a H5 e H1, e nella forma data non
erano preregistrabili. Serve un template di preregistrazione identico
per tutte le famiglie.

Ordine rivisto: **H2** trend time-series per primo, prior forte e
implementabile anche con universo piccolo; **H1** momentum
cross-sectional solo dopo che R0.3 ha prodotto un universo
point-in-time di ampiezza sufficiente, perché 18 asset misti sono
pochi; **H6** breakout trattato come variante del trend e non come
famiglia inferiore; **H3** regime gating con alto rischio di data
mining, da confrontare prima con il semplice volatility scaling; **H4**
mean reversion a breve orizzonte per ultima, correttamente subordinata
perché costi ed esecuzione al prossimo open sono decisivi.

## ALTRI PROBLEMI METODOLOGICI

- **Affermazione falsa sulla contaminazione.** Non è vero che i 52 CSV
  siano stati prodotti tutti sulla stessa finestra 2024-2026. Finestre
  reali: file OOS principali circa 2025-03/05 a 2026-09; confronto equo
  a universo dinamico 2024-10 a 2026-09; alcuni file equity a universo
  dinamico 2021-12 a 2026-09. La contaminazione integrale va marcata
  INFERRED/UNKNOWN in attesa di R0.1, ed è un *output* della Fase 0A,
  non un input.
- **"Migliore baseline" come comparatore.** Crea un comparatore mobile e
  aggiunge un livello di selezione. Ogni ipotesi deve dichiarare un
  **comparatore primario preregistrato** unico; le altre baseline si
  riportano come contesto.
- **Baseline insufficienti.** Vanno aggiunte: cash al tasso T-bill e non
  a rendimento zero; equal-weight buy-and-hold *e* equal-weight
  ribilanciato periodicamente come casi distinti; cap-weighted o
  liquidity-weighted point-in-time; inverse-vol / risk parity; benchmark
  separati per sleeve (equity, crypto, GLD); SPY e QQQ
  volatility-matched e non grezzi; V1 con *e* senza gate ML; placebo a
  ingressi casuali con frequenza di trade appaiata; attribuzione a
  fattori e beta. Tutti i confronti devono condividere dati, date,
  universo, modello di fill, costi, volatilità target ed esposizione.
- **Preregistrazione di "un singolo set di parametri".** Incompatibile
  con l'analisi di sensibilità richiesta altrove nello stesso
  documento. La scheda deve dichiarare ipotesi, comparatore primario,
  dati, split, **griglia completa**, trial budget, metrica primaria,
  modello di costi, seed e criterio di kill.
- **Ambito dell'abbandono del ML troppo ampio.** Se il meta-labeling
  fallisce, si chiude il ramo **direzionale e di meta-labeling**, non il
  ML in generale: il ML su volatilità o su altri target resta una
  questione separata e non preclusa.
- **Prerequisiti del meta-labeling.** Segnali primari generati OOS;
  cross-fitting nidificato; nessuna feature datata dopo l'evento;
  gestione esplicita delle label sovrapposte; correzione per dipendenza
  temporale e cross-asset; confronto con una regola semplice. Un
  pannello aumenta il numero di righe, non necessariamente quello delle
  osservazioni indipendenti, perché gli asset sono correlati.

## PROBLEMI DI QUALITÀ DEI DATI

- `fill_method=None` **non è sufficiente** a chiudere il difetto di
  `pct_change`, perché non rileva le date interamente assenti
  dall'indice. Il layer dati deve reindicizzare sul calendario di
  mercato atteso e distinguere sei stati: barra assente; barra presente
  ma incompleta; mercato chiuso; sospensione di contrattazione; dato
  stale; corporate action.
- Il repository usa impostazioni **incoerenti**: alcuni script
  `auto_adjust=True`, altri `False`, mentre il live usa il default di
  `Ticker.history()`. Feature, rendimenti, split e dividendi sono quindi
  potenzialmente non comparabili fra i risultati esistenti.
- Requisiti: snapshot grezzi immutabili e versionati; un calendario per
  mercato; prezzo grezzo, prezzo aggiustato e total return definiti
  separatamente; split e dividendi con timestamp e regole esplicite;
  nessun forward-fill nella generazione dei segnali; marcatura stale
  ammessa solo per la valutazione e mai per l'esecuzione; purge almeno
  pari all'orizzonte target; embargo giustificato dalle label
  sovrapposte e dal processo di selezione, non applicato
  meccanicamente; hash e versione del dataset registrati in ogni
  risultato.

## RISTRUTTURAZIONE RICHIESTA

Fase 0A mandato e governance; Fase 0B dati e universo; Fase 0C
protocollo statistico; poi Fasi 1 a 6.

## ELEMENTI APPROVATI

- Direzione generale e impostazione del progetto.
- Priorità a dati, universo e statistica prima della ricerca di alpha.
- Separazione concettuale fra ricerca, backtest e implementazione.
- Shadow trading avviato presto e mai usato per il tuning.
- Divieto assoluto di tuning dopo la rivelazione dell'holdout.
- Trial ledger e mappa di contaminazione come artefatti necessari.
- Principio del kill: se una strategia va aggiustata per funzionare, il
  risultato misura l'aggiustamento e non la strategia.
- Necessità e carattere bloccante di R0.1 e R0.3.
- Prior forte su H2 trend.
- Prior solido sulla prevedibilità della volatilità.
- Subordinazione corretta di H4.

## PUNTI NON VERIFICABILI

- Se ogni osservazione 2024-2026 sia contaminata per ogni **nuova**
  ipotesi: indecidibile fino a R0.1.
- Se nel sistema esista effettivamente un solo motore: richiede replay
  deterministico e test di conformance.
- Se siano ottenibili dati survivorship-free adeguati: dipende da una
  decisione di acquisizione non ancora presa.
- Se esista già qualche confronto appaiato decidibile nei risultati
  2024-2026: richiede le serie appaiate e un test robusto.
