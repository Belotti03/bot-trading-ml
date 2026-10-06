# AUDIT RESULT 004

**Oggetto:** `docs/V2_RESEARCH_ROADMAP.md` versione 4
**Richiesta:** `docs/audits/AUDIT_REQUEST_004.md`
**Auditor:** GPT-5.6 Sol, audit indipendente e avversariale
**Data:** 2026-10-06
**File modificati dall'auditor:** nessuno

**Fedeltà:** testo verbatim come ricevuto. L'unico intervento è la
delimitazione markdown delle tabelle. Nessuna parola è stata aggiunta,
rimossa o riordinata.

---

VERDETTO: APPROVED
La v4 è approvabile come piano, non come protocollo eseguibile. I sei blocker dell'audit 003 sono chiusi nel testo. I decision gate non contraddicono più le posizioni su quei sei punti. I documenti allineati non riammettono le tesi ritirate su Sharpe plurale ed evidenza primaria.

Il protocollo resta l'output di 0A–0C. Nessun candidato prima del freeze. R0.1 è autorizzabile ora.

Nessun file è stato modificato.

## I sei blocker

| # | Blocker 003 | Esito |
| --- | --- | --- |
| 1 | Shadow confirmatory vs playground experimental | RISOLTO |
| 2 | Placebo "outside quantile" | RISOLTO |
| 3 | D1 vs D15 / gate 0B | RISOLTO |
| 4 | Master context e research log vs §1 e §2.1 | RISOLTO |
| 5 | D4 e D22 incomplete | RISOLTO |
| 6 | Close-by D8/D9/D10 vs tabella fasi | RISOLTO |

Nessuno è soltanto spostato. Nessuno resta aperto nella forma che l'audit 003 aveva reso bloccante.

## Blocker residui

Nessuno.

## Risposte alle 16 domande

### 1. I sei blocker

Tutti RISOLTI, vedi tabella.

### 2. Infrastruttura / paper run / coorte

VERIFIED — Tre oggetti distinti in §1, §5.2, §5.4 e nella tabella §9.

Fase 1: infrastruttura + paper run development; coorte confirmatory non parte.
Fase 6: al massimo una strategia congelata, peeking sealed.
experimental può essere molti, sul paper adapter, e non è la coorte.
La riga "No second candidate may occupy the same live window" chiude l'occupancy della coorte. Non vieta i paper run come evidenza di development: è ciò che 003 chiedeva.

### 3. Placebo

VERIFIED — §7.2: la metrica primaria supera il quantile superiore preregistrato; one-sided; un risultato peggiore del null non passa. D10 rinvia a quella regola e ritratta "outside quantile". Non c'è contraddizione.

### 4. D1, D15, 0C, review date

VERIFIED — D1 e D15 chiudono insieme in 0B. §9: 0C non parte finché D1 e D15 sono registrati. È vietato avviare 0C "while the vendor is being evaluated". La valutazione vendor è dopo la scelta di ramo, e uno switch successivo è un nuovo audit.

Il review date (12 mesi o contratto vendor) non è la stessa inerzia della v3. B è il ramo corrente dichiarato, non un parallelo aperto. Se alla review date non si decide, B resta corrente: è inerzia dichiarata di un case study, non un gate eluso. Accettabile.

### 5. D4

VERIFIED — È una posizione operativa: seasoning, liquidità, venue, prezzo, oggetto economico. 50% NAV / 6 mesi è un numero proposto, non derivato. UNKNOWN se escluda MSTR; la v4 lo dichiara. Accettabile come proposta di regola generale.

### 6. D22

VERIFIED — Calendari nativi, intersezione al portafoglio, crypto ferma sui giorni equity, niente rendimenti sintetici: invariati. Split proposto 70/20/10, owner Filippo.

### 7. Close-by

VERIFIED — D8, D9, D10: Close by: 0C. Tabella Fase 0C: 5, 6, 7, 8, 9, 10, 19, 20, 25. Fase 1 non ha più gate su quelle decisioni.

### 8. Documenti allineati

VERIFIED — Il plurale "Sharpe non distinguibili da zero" è INFERRED, not VERIFIED in entrambi. Nested walk-forward, mercati esterni e leave-one-cohort sono robustness e non promuovono. Il blocco storico è confirmatory solo se quarantinato. I paper run sono development. La coorte è una strategia congelata.

Non riammettono le tesi ritirate.

### 9. Q7

VERIFIED — La domanda sul selection bias resta e non poggia sul +87,15% come buy & hold.

### 10. Doppia riga

VERIFIED sul codice, invariato:

487 obs: simulate(k=18) con len(day) < k skip.
711 obs: static_18(with_costs=True) con g["Return"] -= COST_PER_SIDE su tutte le righe, contro il commento.
§12.3 spiega entrambe, non elegge un benchmark vero, tiene entrambe INVALID come buy & hold. Corretto. Non ho ricalcolato le equity in questo turno; i numeri restano quelli dell'audit 003, e il meccanismo è confermato di nuovo nel file.

### 11. Flag

INFERRED — La distinzione blocking vs annotative è difendibile. corporate_action aggiustato e half_day_session annotativi chiudono il rilievo 003. volume_suspect come blocking è conservativo, non contraddittorio.

### 12. Freeze / INCONCLUSIVE / budget

VERIFIED come regole di piano: kill §8.7; un INCONCLUSIVE = un trial; ri-coda = trial nuovo; budget di famiglia congelati in 0C, niente riallocazione senza audit. Verificabili quando esisteranno ledger e runner. Oggi non c'è meccanismo nel codice: atteso per un piano.

### 13. Regime

VERIFIED — Se il mandato 0A nomina regimi richiesti, fallirli tutti è hard gate. Altrimenti resta diagnostica. Chiude la via di fuga indicata in 003.

### 14. D26–D28

Coprono timeframe, orizzonte e strumenti. Restano impliciti, non bloccanti: frequenza di ribilancio dello split 70/20/10; D4 sotto ramo B (paniere fisso vs eligibility); paper run development sovrapposti al calendario della coorte, che non unsealano la coorte ma rendono visibile il mercato (già visibile via V1).

### 15. Nuove affermazioni / contraddizioni

Nessuna contraddizione gate/posizione sui sei blocker.

Residui non bloccanti:

Master context tiene ancora "UNRESOLVED" su trend-baseline vs H2, mentre la v4 ha la baseline canonica. Non è una tesi ritirata riammessa; è allineamento post-approvazione.
Research log Q2 etichetta R0.1 come "Phase 0A"; la v4 lo rende indipendente da 0A.
Placebo a coda superiore è corretto per le metriche H2–H4 (differenza appaiata). Per QLIKE (loss) la coda andrebbe invertita; oggi il sizing ha due estimand, quindi va detto sulla scheda.

### 16. R0.1

Sì, ora. Scope: provenance per-file; attribuzione delle due righe alle due funzioni e al bug -= COST_PER_SIDE; inventario auto_adjust / feature / costi; asse features.py dropna(); nessuna conclusione strategica. Non è Fase 0A.

## Correzioni

Bloccanti: nessuna.

Migliorative (non impediscono l'approvazione del piano):

Dichiarare esplicitamente che D4 filtra il ramo A; sotto B i 18 restano fissi.
Dichiarare la frequenza di ribilancio del 70/20/10.
Sulla scheda, la coda del placebo segue il verso di miglioramento della metrica (QLIKE = coda inferiore).
Dopo l'adozione: togliere l'UNRESOLVED sul trend nel master context; Q2 del log: R0.1 ≠ 0A.

## Posizioni nuove

| ID | Giudizio |
| --- | --- |
| D1 | Approvo. Scelta A o B in 0B; default B come ramo corrente; 0C attende; switch = nuovo audit. |
| D4 | Approvo come lista operativa. 50%/6 mesi è proposta, owner di fatto Filippo se diventa mandato. UNKNOWN su MSTR. |
| D22 | Approvo calendari e 70/20/10 come proposta, owner Filippo. |
| D5 | Approvo. Un'aggregazione walk-forward = un trial; fold selezionato = trial; griglia nel ledger; freeze dei budget. |
| D8 | Approvo. Freeze in 0C; H1 dormiente sotto B. |
| D10 | Approvo. Schema + test a coda superiore allineati a §7.2. |
| D26 | Approvo. Daily dichiarato. |
| D27 | Approvo. Orizzonte V2 indipendente dal target 1-day V1. |
| D28 | Approvo. Cash equity, ETF del paniere sotto B, spot crypto; no futures/opzioni/leveraged. |

## R0.1

Autorizzabile ora, indipendentemente dall'adozione della v4.

La v4 soddisfa le quattro condizioni dell'audit 003 per un piano: non si finge protocollo; i gate sui sei blocker sono vincoli veri; le posizioni relative non li contraddicono; i documenti allineati non riammettono le tesi ritirate su Sharpe ed evidenza. Filippo può adottarla come piano. Il protocollo eseguibile nasce solo al freeze 0A–0C.
