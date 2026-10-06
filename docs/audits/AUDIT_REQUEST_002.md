# AUDIT REQUEST 002

**Preparato da:** Claude/Cursor
**Data:** 2026-10-06
**Audit precedente:** `docs/audits/AUDIT_RESULT_001.md` (APPROVED WITH
CHANGES, otto blocker)
**Stato richiesto:** secondo audit indipendente e avversariale

## 1. Titolo della decisione da auditare

Approvazione di `docs/V2_RESEARCH_ROADMAP.md` versione 2 come protocollo
di ricerca eseguibile per V2, e autorizzazione a iniziare la Fase 0A.

## 2. Domanda precisa a cui l'auditor deve rispondere

La versione 2 della roadmap ha recepito correttamente e integralmente
gli otto blocker dell'audit 001, ed è ora approvabile come protocollo
statistico eseguibile?

In particolare: le correzioni introdotte sono sufficienti, oppure
introducono nuovi errori, nuove affermazioni non supportate o nuove
contraddizioni interne?

## 3. Contesto necessario

### 3.1 Dove sono i file (importante)

Gli artefatti da auditare sono **file locali non committati** nel
working tree. Non esistono su `origin/main` e non sono visibili da
GitHub.

- `docs/V2_RESEARCH_ROADMAP.md` — **untracked**, assente da `origin/main`
- `docs/RESEARCH_LOG.md` — modificato, non committato
- `docs/BOT_TRADING_V2_MASTER_CONTEXT.md` — modificato, non committato
- `docs/CURSOR_CLAUDE_WORKFLOW.md` — modificato, non committato
- `docs/audits/AUDIT_RESULT_001.md` — untracked
- `docs/audits/AUDIT_REQUEST_002.md` — questo file, untracked

L'audit va condotto sul **working tree locale**, non su GitHub.
`main` locale è `06006e3`, `origin/main` è `640ca0e`, con `main` indietro
di 2 commit (i due commit remoti sono auto-update di stato del bot e non
toccano `docs/`).

### 3.2 Situazione del progetto

V1 è in produzione e viene usata solo come benchmark. L'incidente NaN è
chiuso: catena causale provata, guard uniti, stato ricostruito da storia
verificata, fix validato in produzione. `run_bot.yml` è attivo,
`retrain.yml` è `disabled_manually`. V2 non è implementata e non deve
esserlo finché la roadmap non è approvata.

### 3.3 Perché questo audit è obbligatorio

`docs/CURSOR_CLAUDE_WORKFLOW.md` impone un audit indipendente prima di
adottare decisioni metodologiche, architetturali o strategiche. La
roadmap ricade interamente in quella categoria: definisce universo,
target, metodologia di validazione, regole di confronto e criteri di
accettazione. La roadmap v2 si dichiara infatti "proposal under audit,
not adopted".

## 4. Ipotesi testata

Non è un esperimento empirico. L'ipotesi sotto esame è documentale e
metodologica:

> Roadmap v2 recepisce gli otto blocker dell'audit 001 senza introdurre
> nuovi difetti, ed è internamente coerente e preregistrabile.

L'auditor è invitato a tentare di **falsificarla**.

## 5. Dati utilizzati

Nessun dato di mercato è stato elaborato per produrre la v2. La
revisione è documentale. I dati rilevanti citati nel documento e
verificabili nel repository sono:

- 52 file CSV di risultati (conteggio verificato oggi);
- 28 file `.py` tracciati o presenti nel working tree, esclusi i
  `__pycache__` (la v1 parlava di "17 research scripts": **questo
  conteggio non è stato riverificato** e va considerato non affidabile);
- 111 file tracciati in totale;
- `ml_validation_report.json`, `scout_signals.json`,
  `portfolio_state.json` come artefatti di produzione correnti.

L'unico calcolo numerico rifatto è lo standard error dello Sharpe
(sezione 10).

## 6. Periodo temporale

Non è stato definito alcun periodo di test, perché nessun test è stato
eseguito. I periodi citati nel documento, da verificare, sono:

- file OOS principali: circa 2025-03/05 a 2026-09;
- confronto equo a universo dinamico: 2024-10 a 2026-09;
- alcuni file equity a universo dinamico: 2021-12 a 2026-09;
- V1 in produzione: run documentati fino a 2026-10-06.

## 7. Metodologia

Confronto riga per riga fra i rilievi dell'audit 001 e il testo della
roadmap v1, con riscrittura integrale del documento. Tre scelte
metodologiche adottate che l'auditor deve valutare criticamente:

1. **Le soglie numeriche non sono state reinventate.** Dove l'audit 001
   ha giudicato una soglia arbitraria, la v2 non l'ha sostituita con
   un'altra soglia: ha marcato il valore come `*0C*`, rinviandolo alla
   power analysis della Fase 0C. La motivazione è che sostituire soglie
   arbitrarie con altre soglie arbitrarie non avrebbe risolto il
   rilievo. Il rischio è che il documento resti incompleto come
   protocollo eseguibile.
2. **Le correzioni sono tracciate anziché cancellate.** Il documento
   affianca il valore errato e quello corretto, e ritratta
   esplicitamente le affermazioni cadute, per non perdere la traccia di
   cosa fosse stato contestato.
3. **Le decisioni ancora aperte sono state elencate anziché decise.**
   La sezione 9 della roadmap contiene 11 decisioni non prese di
   proposito, perché metodologiche o strategiche.

## 8. Split temporali

Non applicabile: nessun addestramento, nessuna validazione e nessun
backtest sono stati eseguiti. La roadmap *propone* tre regimi
(development, pseudo-OOS storico, forward shadow) la cui definizione
operativa è rinviata alla Fase 0C. La correttezza di quella proposta è
parte di ciò che l'auditor deve giudicare.

## 9. Codice e commit rilevanti

Nessun codice è stato modificato per produrre la v2. Nessun file sorgente
è stato toccato dall'audit 001 a oggi.

| Commit | Oggetto |
| --- | --- |
| `640ca0e` | auto-update stato portafoglio, `origin/main` |
| `259eba1` | auto-update stato portafoglio |
| `06006e3` | `Ignore Python runtime artifacts`, HEAD locale |
| `40bba21` | ricostruzione stato e rigenerazione scout validati |
| `5177e86` | merge PR #1 `fix/nan-guards` |
| `98994d3` | hardening della validazione di recency lato consumer |
| `9ccaa9d` | fix corruzione NaN e recency dei segnali |
| `4f54be3` | aggiunta del contesto V2 e del workflow Claude |

File di codice citati dalla roadmap e rilevanti per la verifica:
`model_engine.py`, `main.py`, `safe_state.py`,
`.github/workflows/run_bot.yml`, `tests/test_nan_guards.py`.

## 10. Metriche e risultati completi

Unico calcolo rifatto, con `SR = 1.155`, `q = 252`, `T = 2`:

| formula | SE | intervallo 95% |
| --- | --- | --- |
| v1: `sqrt((1 + SR^2/2)/T)` | 0.9130 | [-0.63, 2.94] |
| v2: `sqrt((1 + SR^2/(2q))/T)` | 0.7080 | [-0.23, 2.54] |

Entrambi gli intervalli contengono lo zero. Il valore v2 coincide con
quello indicato dall'audit 001.

Nessun'altra metrica è stata ricalcolata. Tutte le cifre storiche citate
nella roadmap (run #10 a -20,20%, Sharpe -0,2496, ML OFF +117,56%, ML ON
+16,54%, Buy & Hold +87,15%, AUC 0,5046) sono **ereditate e non
verificate**, e la loro verifica è l'oggetto di R0.1.

## 11. Assunzioni

1. I rilievi dell'audit 001 sono corretti e vanno recepiti, non
   discussi. La v2 non contesta alcun blocker.
2. `SR = 1.155`, `q = 252` e `T = 2` sono i valori di riferimento per
   l'esempio di potenza statistica.
3. Una roadmap può essere approvata con soglie numeriche rinviate a una
   fase successiva, purché i rinvii siano espliciti.
4. L'auditor legge il working tree locale.

## 12. Limitazioni

1. `AUDIT_RESULT_001.md` è una **ricostruzione** e non il verbatim
   dell'audit 001, per i motivi spiegati in quel file. Se l'auditor
   rileva una discrepanza fra ciò che aveva scritto e ciò che è
   riportato lì, prevale il suo testo originale.
2. Nessun blocker dell'audit 001 è stato verificato empiricamente contro
   il repository: sono stati recepiti sulla fiducia. In particolare non
   ho riverificato l'incoerenza di `auto_adjust`, le finestre temporali
   dei CSV né il conteggio degli script.
3. La roadmap resta un documento, non un protocollo eseguibile: finché
   le soglie `*0C*` non sono definite, non è possibile preregistrare un
   esperimento.
4. Le 11 decisioni aperte della sezione 9 non sono risolte, e alcune
   (in particolare l'acquisizione di dati survivorship-free)
   condizionano la generalizzabilità di tutto ciò che segue.
5. Il conteggio "17 research scripts" della v1 non è stato corretto nel
   documento perché non riverificato; oggi risultano 28 file `.py`.

## 13. Conclusione proposta da Claude

Proposta: roadmap v2 recepisce gli otto blocker ed è approvabile come
**piano di ricerca**, con l'avvertenza che non è ancora un protocollo
preregistrabile finché la Fase 0C non produce le soglie rinviate.

Questa è una proposta, non una conclusione stabilita. Chi l'ha scritta
ha anche scritto il documento sotto esame, ed è la stessa parte che
nell'audit 001 ha prodotto due derivazioni errate presentate come
verificate. La proposta va trattata di conseguenza.

## 14. Possibili rischi di leakage, bias, overfitting o data snooping

Rischi che questa revisione può non aver eliminato:

- **Data snooping già avvenuto.** La contaminazione della finestra
  recente è dichiarata ma non misurata. Se R0.1 mostrasse che la
  contaminazione è più estesa di quanto inferito, parte della Fase 4
  diventerebbe inutilizzabile.
- **Selection bias sull'universo.** La v2 declassa il +87,15% a ipotesi,
  ma mantiene i 18 ticker come riferimento operativo nel frattempo. Il
  fallback "case study" potrebbe essere adottato per inerzia anziché per
  scelta.
- **Survivorship bias.** La metodologia point-in-time è specificata ma
  non implementata, e dipende da dati non ancora disponibili.
- **Overfitting del protocollo.** Rinviare le soglie alla Fase 0C
  trasferisce il rischio invece di eliminarlo: se le soglie fossero
  scelte dopo aver visto risultati preliminari, l'intera impalcatura
  statistica cadrebbe.
- **Multiple testing.** Il trial ledger è richiesto ma non esiste.
  Nessun conteggio di trial è attualmente disponibile per la correzione.
- **Look-ahead nei dati.** Il difetto `pct_change` è ancora presente nel
  codice, e il requisito di reindicizzazione sul calendario non è
  implementato.
- **Bias di conferma nella preparazione di questo pacchetto.** La
  descrizione dei rilievi è passata attraverso la parte auditata.

## 15. Domande che l'auditor deve verificare

1. La formula dello standard error nella sezione 1.1 della roadmap è ora
   corretta, e i valori 0.7080 e [-0.23, 2.54] sono riproducibili?
2. La riformulazione della sezione 1.3 elimina l'overclaim senza
   introdurne uno opposto, cioè senza suggerire che i confronti appaiati
   siano decidibili quando non è dimostrato?
3. La mappa di contaminazione della sezione 2 è coerente con le finestre
   reali dei CSV, verificandole direttamente nel repository?
4. Le cinque fonti di evidenza alternative della sezione 2.3 sono
   effettivamente ammissibili, o alcune reintroducono contaminazione?
5. La trattazione di coorti e pannello sbilanciato nella sezione 3 è
   sufficiente, e la rottura di regime MSTR è gestita correttamente?
6. La metodologia point-in-time della sezione 4 è implementabile, e il
   fallback "case study" è formulato in modo da non poter essere
   adottato implicitamente?
7. I requisiti sui dati della sezione 3.3 chiudono effettivamente il
   difetto `pct_change`, e la tassonomia a sei stati della barra è
   completa?
8. La separazione fra infrastruttura e plugin nella sezione 5 risolve la
   contraddizione del blocker 6, o la sposta?
9. Il requisito di conformance replay è sufficiente a trasformare
   "esattamente un motore" da requisito documentale a proprietà
   verificata?
10. L'elenco delle baseline nella Fase 1 è completo, e il comparatore
    primario preregistrato elimina il problema del comparatore mobile?
11. La ricollocazione di H5 fra le baseline di sizing è corretta, e il
    confronto a pari rischio è specificato in modo testabile?
12. Il nuovo ordine H2, H1, H6, H3, H4 è giustificato, e il template
    comune è sufficiente in assenza di soglie numeriche?
13. La separazione fra gate primari e diagnostiche secondarie nella
    sezione 7 è difendibile, o alcune diagnostiche dovrebbero essere
    gate?
14. Rinviare tutte le soglie numeriche alla Fase 0C è una scelta
    metodologicamente accettabile o un difetto che blocca
    l'approvazione?
15. I criteri di kill della sezione 8 sono ora verificabili?
16. La restrizione dell'abbandono del ML al solo ramo direzionale e di
    meta-labeling è corretta?
17. Le 11 decisioni aperte della sezione 9 sono le decisioni giuste da
    sottoporre, o ne mancano altre che la v2 ha deciso implicitamente
    senza dichiararlo?
18. La v2 introduce affermazioni nuove non supportate, o contraddizioni
    interne, che l'audit 001 non poteva rilevare?

## PROMPT DA INVIARE A GPT-5.6 SOL

Agisci come auditor indipendente e avversariale. Il tuo compito non è
confermare la mia proposta: è cercare di falsificarla.

Oggetto dell'audit: `docs/V2_RESEARCH_ROADMAP.md` versione 2, nel
repository `bot-trading-ml`.

IMPORTANTE SU DOVE GUARDARE. I file da auditare sono file locali **non
committati**. `docs/V2_RESEARCH_ROADMAP.md` è untracked e non esiste su
`origin/main`, quindi non lo trovi su GitHub. Lavora sul working tree
locale. `main` locale è `06006e3`, `origin/main` è `640ca0e`, e i due
commit di differenza sono auto-update di stato del bot che non toccano
`docs/`.

Leggi, nell'ordine:

1. `docs/audits/AUDIT_REQUEST_002.md` — questo pacchetto, con assunzioni
   e limitazioni dichiarate;
2. `docs/audits/AUDIT_RESULT_001.md` — il tuo audit precedente, ma
   attenzione: è una **ricostruzione** e non il tuo testo verbatim,
   perché l'originale è stato incollato in chat e non salvato nel
   repository. Se trovi discrepanze rispetto a ciò che avevi scritto,
   prevale il tuo testo originale e segnalalo;
3. `docs/V2_RESEARCH_ROADMAP.md` — il documento da auditare;
4. `docs/RESEARCH_LOG.md` e `docs/BOT_TRADING_V2_MASTER_CONTEXT.md` —
   allineati oggi alla v2; verifica che non contengano residui
   contraddittori;
5. `docs/CURSOR_CLAUDE_WORKFLOW.md` — regole e procedura di audit.

Verifica autonomamente codice, dati e risultati nel repository. Non
fidarti delle cifre riportate nel pacchetto: ricalcolale. In
particolare, verifica direttamente nel repository le finestre temporali
dei file CSV di risultati, l'incoerenza dichiarata di `auto_adjust` fra
gli script, la presenza del difetto `pct_change` nel codice attuale e il
conteggio degli script di ricerca, perché io ho recepito questi punti
senza riverificarli.

Rispondi alle 18 domande della sezione 15 di questo pacchetto.

Cerca attivamente, senza assumere che la mia conclusione sia corretta:
leakage; look-ahead bias; survivorship bias; selection bias; data
snooping; overfitting; multiple testing; confronti non equi; errori
statistici; errori di implementazione; interpretazioni eccessive dei
risultati; contraddizioni interne al documento; decisioni importanti
prese implicitamente e non dichiarate fra le decisioni aperte.

Valuta criticamente, in particolare, tre scelte che ho fatto e che
potrebbero essere sbagliate:

- aver rinviato tutte le soglie numeriche alla Fase 0C invece di
  definirle, con la motivazione che sostituire soglie arbitrarie con
  altre soglie arbitrarie non avrebbe risolto il rilievo;
- aver mantenuto nel documento le affermazioni errate affiancate alle
  correzioni, per tracciabilità, invece di rimuoverle;
- aver elencato 11 decisioni come aperte invece di proporre una
  posizione su ciascuna.

Vincoli operativi: non modificare alcun file; non fare commit; non fare
push; non eseguire workflow; non eseguire il bot; non riattivare il
retraining.

Produci in output:

- un **VERDETTO** esplicito, scelto fra `APPROVED`,
  `APPROVED WITH CHANGES`, `REJECTED`;
- l'elenco dei **blocker**, numerati;
- i problemi **metodologici**;
- i problemi **statistici**;
- i problemi di **implementazione**;
- le **correzioni richieste**, ciascuna indicando se è bloccante o
  migliorativa;
- gli elementi che **approvi**;
- i punti **non verificabili** e perché;
- per ogni affermazione rilevante, l'etichetta VERIFIED, INFERRED,
  HYPOTHESIS o UNKNOWN.

Se ritieni che la roadmap non sia approvabile, dillo chiaramente e
indica cosa deve cambiare perché lo diventi.
