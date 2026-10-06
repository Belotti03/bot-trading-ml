# AUDIT REQUEST 004

**Preparato da:** Claude/Cursor
**Data:** 2026-10-06
**Audit precedente:** `AUDIT_RESULT_003.md` (APPROVED WITH CHANGES, 6
blocker residui, verbatim)
**Stato richiesto:** quarto audit indipendente e avversariale

## 1. Titolo della decisione da auditare

Approvazione di `docs/V2_RESEARCH_ROADMAP.md` versione 4 come piano di
ricerca, non come protocollo eseguibile. In subordine: conferma che R0.1
resta autorizzabile indipendentemente.

## 2. Domanda precisa

La v4 risolve i sei blocker residui dell'audit 003, senza reintrodurre
contraddizioni fra gate e posizioni, e senza riammettere tesi ritirate
nei documenti allineati?

L'audit 003 ha scritto: "Dopo queste correzioni, una v4 può essere
approvata come piano." Questa richiesta chiede se quelle correzioni
sono effettivamente nel testo, non se il protocollo eseguibile è già
pronto. Il protocollo resta l'output di 0A–0C.

## 3. Contesto necessario

Working tree locale, file **non committati**. `main` locale `06006e3`,
`origin/main` `640ca0e`.

La v3 è stata APPROVED WITH CHANGES, non REJECTED. La Fase 0A
metodologica non parte su questo testo finché la v4 non è approvata.
R0.1 è indipendente.

## 4. Ipotesi testata

> La v4 chiude i sei blocker dell'audit 003. I decision gate sono veri
> vincoli. Le posizioni non contraddicono i gate. I documenti allineati
> non riammettono le tesi ritirate.

Falsificarla.

## 5. Dati utilizzati

Revisione documentale. Verifica indipendente della doppia riga, read-only:

In `dynamic_universe_fair_comparison.py`:
- `simulate(panel, k, with_costs)` alle righe 71–107, con
  `dropna(subset=["Score","NextRet"])` e `if len(day) < k: continue`;
- `static_18(panel, with_costs)` alle righe 121–144, con
  `g["Return"] -= COST_PER_SIDE` su tutte le righe quando
  `with_costs=True`, contro il commento "One initial allocation cost
  only".

Confermato. Non ho ricalcolato `(1-0.0015)**711` né le equity senza
costi: recepisco i numeri dell'audit 003 su quel punto.

## 6. Periodo temporale

Nessun test eseguito.

## 7. Metodologia

Riscrittura della roadmap a versione 4 contro i sei blocker e le
migliorative elencate. Tre scelte da valutare:

1. Occupancy dello shadow: infrastruttura in Fase 1, paper run
   experimental = development, coorte confirmatory = al massimo una
   strategia congelata in Fase 6.
2. D1: in 0B si sceglie A o B come ramo *corrente*; 0C non parte prima;
   valutazione vendor dopo la registrazione, switch successivo = nuovo
   audit.
3. Decisioni implicite dichiarate come D26 (daily), D27 (orizzonte),
   D28 (strumenti). Conteggio walk-forward e freeze dei budget di
   famiglia piegati in D5. Peeking piegato in D17. Totale 27 decisioni,
   numerate D1–D28 con buco a D11.

## 8. Split temporali

Non applicabile.

## 9. Codice e commit rilevanti

Nessun codice modificato. File citati:
`dynamic_universe_fair_comparison.py` righe 71–147.

## 10. Metriche

Nessuna metrica nuova. SE 0.7187 e intervallo [-0.254, 2.564] restano
l'unico caso calcolato, marcato come singolo caso.

## 11. Assunzioni

1. I sei blocker dell'audit 003 vanno recepiti, non discussi.
2. Le posizioni che l'audit 003 ha approvato non vanno riaperte, salvo
   incoerenza nuova.
3. I numeri della doppia riga (0.344, 24321.13, +87.43% vs +143.21%)
   sono dell'auditor; io ho confermato il meccanismo nel codice, non
   ricalcolato le equity.

## 12. Limitazioni

1. Non ho riverificato `features.py` / `dropna()` segnalato come
   INFERRED dall'audit 003. È registrato in §12.3 come asse per R0.1.
2. D4 propone 50% NAV per 6 mesi come soglia di "oggetto economico".
   È un numero proposto, non derivato. UNKNOWN se escluda MSTR.
3. D22 propone 70/20/10. Owner Filippo.
4. Lo shadow confirmatory a una sola strategia è una regola di
   occupancy, non ancora un meccanismo nel codice.

## 13. Conclusione proposta da Claude

Proposta: i sei blocker sono chiusi nel testo; la v4 è approvabile come
piano. R0.1 resta autorizzabile ora.

Chi scrive è la stessa parte che in 001 ha presentato derivazioni errate
come verificate, in 002 ha dichiarato risolti blocker non risolti, e in
003 ha lasciato lo shadow confirmatory occupabile dagli experimental.

## 14. Rischi

- Occupancy dello shadow spostata in §5.4 ma contraddetta da qualche
  altra riga.
- D1 "review date" come nuova forma di inerzia del ramo B.
- D4 con soglie 50%/6 mesi ancora arbitrarie, solo più esplicite.
- Allineamento documentale incompleto: residui di "Sharpe non
  distinguibili" o di fonti "admissible" senza gerarchia.
- D26–D28 insufficienti rispetto alle decisioni implicite residue.

## 15. Domande

1. I sei blocker dell'audit 003 sono RISOLTI, SPOSTATI o NON RISOLTI?
2. Infrastruttura shadow / paper run development / coorte confirmatory
   sono distinti in tutto il documento, inclusa la tabella delle fasi?
3. Il gate placebo è una coda superiore sulla metrica primaria, e D10
   non lo contraddice?
4. D1 e D15 chiudono insieme in 0B, e 0C non può partire prima? Il
   review date di B è una nuova inerzia?
5. D4 è ora una posizione operativa? Le soglie 50%/6 mesi sono
   accettabili come proposta di mandato?
6. D22 ha uno split numerico proposto, e i calendari restano quelli
   approvati?
7. I Close by di D8, D9, D10 coincidono con la tabella della Fase 0C?
8. Master context e research log contraddicono ancora §1 o §2.1?
9. Q7 del research log poggia ancora sul +87.15% come buy & hold?
10. La doppia riga in §12.3 è spiegata correttamente, senza eleggere un
    benchmark vero?
11. Flag bloccanti vs annotativi: la classificazione è difendibile?
12. Kill per violazione della freeze, conteggio INCONCLUSIVE, e divieto
    di riallocare i budget di famiglia sono verificabili?
13. Il regime preregistrato come hard gate se il mandato lo richiede
    chiude la via di fuga dell'audit 003?
14. D26–D28 coprono le decisioni implicite segnalate, o ne restano?
15. La v4 introduce affermazioni nuove non supportate o contraddizioni
    interne?
16. R0.1 resta autorizzabile ora, con lo scope dell'audit 003 più
    l'attribuzione delle due righe, senza conclusioni strategiche?

## PROMPT DA INVIARE A GPT-5.6 SOL

Agisci come auditor indipendente e avversariale. Non confermare la mia
proposta: cerca di falsificarla.

Oggetto: `docs/V2_RESEARCH_ROADMAP.md` versione 4. Hai giudicato la v3
APPROVED WITH CHANGES con sei blocker residui, e hai scritto che dopo
quelle correzioni una v4 può essere approvata come piano.

DOVE GUARDARE. File locali **non committati**. Non esiste su
`origin/main`. `main` locale `06006e3`, `origin/main` `640ca0e`.

Leggi, nell'ordine:

1. `docs/audits/AUDIT_REQUEST_004.md`
2. `docs/audits/AUDIT_RESULT_003.md` (il tuo testo verbatim)
3. `docs/V2_RESEARCH_ROADMAP.md` versione 4
4. `docs/RESEARCH_LOG.md` e `docs/BOT_TRADING_V2_MASTER_CONTEXT.md`

Non riaprire i punti che in 003 hai già accettato, salvo incoerenza
nuova con i sei blocker.

Domanda principale: i sei blocker sono chiusi nel testo?

Verifica in particolare:

- più candidati live non possono occupare la coorte confirmatory;
- placebo = coda superiore, non "outside quantile";
- 0C non parte prima della scelta di ramo registrata;
- D4 ha una lista; D22 ha 70/20/10;
- Close by D8/D9/D10 = Fase 0C;
- i due documenti allineati non dicono più che gli Sharpe individuali
  "non sono distinguibili da zero" come fatto, né che nested
  walk-forward e affini siano evidenza primaria.

Rispondi alle 16 domande della sezione 15.

Verifica autonomamente il codice della doppia riga se vuoi contraddirmi.
Io ho confermato le due funzioni e il `-= COST_PER_SIDE` su tutte le
righe; non ho ricalcolato le equity.

Cerca: contraddizioni gate/posizioni; tesi ritirate riammesse;
decisioni implicite ancora non dichiarate; occupancy dello shadow
contraddetta da qualche riga; inerzia del ramo B sotto altra forma.

Vincoli: non modificare file; non fare commit; non fare push; non
eseguire workflow; non eseguire il bot; non riattivare il retraining.

Output:

- VERDETTO: `APPROVED`, `APPROVED WITH CHANGES` o `REJECTED`;
- per ciascuno dei sei blocker: RISOLTO / SPOSTATO / NON RISOLTO;
- blocker residui numerati;
- correzioni bloccanti vs migliorative;
- quali posizioni nuove (D1, D4, D22, D5, D8, D10, D26–D28) approvi o
  respingi;
- se R0.1 è autorizzabile ora;
- etichette VERIFIED / INFERRED / HYPOTHESIS / UNKNOWN.
