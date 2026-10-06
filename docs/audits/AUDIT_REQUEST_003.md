# AUDIT REQUEST 003

**Preparato da:** Claude/Cursor
**Data:** 2026-10-06
**Audit precedenti:** `AUDIT_RESULT_001.md` (APPROVED WITH CHANGES, 8
blocker, ricostruzione non verbatim), `AUDIT_RESULT_002.md` (REJECTED,
10 correzioni bloccanti, verbatim)
**Stato richiesto:** terzo audit indipendente e avversariale

## 1. Titolo della decisione da auditare

Approvazione di `docs/V2_RESEARCH_ROADMAP.md` versione 3, e
autorizzazione ad avviare la Fase 0A. In subordine: autorizzazione di
R0.1 come attività forense separata, come l'audit 002 ha indicato
possibile anche senza adottare la roadmap.

## 2. Domanda precisa a cui l'auditor deve rispondere

La v3 risolve le dieci correzioni bloccanti dell'audit 002, e le 25
posizioni proposte nella sezione 11 sono difendibili?

Domanda subordinata, che riguarda la natura stessa del documento e che
va risolta prima delle altre. L'audit 002 ha respinto la v2 perché "un
piano per costruire il protocollo, non il protocollo eseguibile
richiesto". La v3 **non rivendica più** di essere un protocollo
eseguibile: dichiara di essere un piano più un insieme di posizioni
proposte, e colloca il protocollo eseguibile all'uscita delle Fasi 0A,
0B e 0C. La domanda è se questa riformulazione sia una risposta
accettabile al motivo del rigetto, oppure se l'approvazione richieda che
le soglie siano già presenti nel documento. Se vale la seconda, la v3 va
respinta per lo stesso motivo della v2 e va detto chiaramente.

## 3. Contesto necessario

### 3.1 Dove sono i file

Working tree locale, file **non committati**. `main` locale è `06006e3`,
`origin/main` è `640ca0e`, due commit di differenza che toccano solo i
tre JSON di stato del bot.

- `docs/V2_RESEARCH_ROADMAP.md` — untracked, v3
- `docs/RESEARCH_LOG.md`, `docs/BOT_TRADING_V2_MASTER_CONTEXT.md` —
  modificati, allineati alla v3
- `docs/CURSOR_CLAUDE_WORKFLOW.md` — modificato
- `docs/audits/*.md` — untracked

### 3.2 Correzioni documentali già eseguite

La correzione bloccante 9 dell'audit 002 è stata eseguita fuori dalla
roadmap. Verificate e corrette: il CAGR scambiato con il drawdown per lo
Static 18, "Keep V1 cron paused", la roadmap definita "authority", le
divergenze su trend/momentum e sul motore registrate come UNRESOLVED
anziché risolte in una direzione. La decisione 6 del research log è
**sospesa, non ribaltata**.

### 3.3 Cosa è cambiato strutturalmente nella v3

Nuove sezioni: gerarchia delle evidenze a tre livelli (§1); DSR, PSR e
test appaiato come criteri distinti (§2.2); contratto dati con snapshot,
dependency lock e data-version contract (§3.1); quality flag ortogonali
al posto della tassonomia a stati (§3.3); rami A e B dell'universo
mutuamente esclusivi con le conseguenze su H1 (§4.2); lifecycle dei
plugin a tre stati (§5.2); baseline, diagnostiche e attribuzione
separate (§6); criteri su tre livelli con hard gate (§7); esito
INCONCLUSIVE aggiunto (§8); 24 decisioni con posizione proposta (§11);
risultati legacy con adjudication individuale (§12); appendice delle
affermazioni ritirate (Appendice A).

## 4. Ipotesi testata

Documentale e metodologica, non empirica:

> La v3 risolve le dieci correzioni bloccanti dell'audit 002 senza
> introdurre nuovi difetti, e le 24 posizioni proposte sono coerenti fra
> loro e con i vincoli statistici dichiarati.

L'auditor è invitato a falsificarla.

## 5. Dati utilizzati

La revisione è documentale. Verifiche empiriche eseguite da me in
preparazione, tutte read-only:

| Verifica | Esito |
| --- | --- |
| `dynamic_universe_fair_summary.csv`, intestazione e righe | due righe distinte per TopK 18: 487 osservazioni con +87,15% e 711 osservazioni con -16,26% |
| CAGR contro drawdown per Static 18 | CAGR +38,1103%, max DD -27,1968%; il master context riportava 38,11 come drawdown |
| `static_equal_weight()` | confermato; il commento dichiara "True static 18 ... turnover = 0" mentre l'aritmetica è una media cross-sectional giornaliera |
| score e `NextRet` | `NextRet` è `Close.shift(-1)/Close - 1`; lo score usa il giorno `d`, la selezione è al giorno `d`, il rendimento accreditato è `d`→`d+1` |
| `pct_change(` | 31 occorrenze in 15 file, nessuna con `fill_method` |
| `auto_adjust` | 1 esplicito `True`, 7 espliciti `False` |

## 6. Periodo temporale

Nessun test eseguito, nessun periodo definito. La finestra usata per
l'esempio di potenza statistica è 2024-10-15 / 2026-09-24, 487
osservazioni, `T = 1.941`, presa dalla riga del CSV e non assunta.

## 7. Metodologia

Riscrittura integrale contro le dieci correzioni bloccanti e le cinque
migliorative, più verifica diretta di sei affermazioni dell'audit 002
anziché recepirle sulla fiducia come avevo fatto nella richiesta 002.

Tre scelte di metodo da valutare criticamente:

1. **Riformulazione della natura del documento.** Vedi sezione 2. È il
   punto su cui la v3 può cadere interamente.
2. **Soglie ancora non numeriche, ma con origine dichiarata.** La v3
   separa le soglie statistiche, derivate dalla power analysis in 0C,
   dalle soglie economiche, che provengono dal mandato 0A, e vieta di
   fissarle dopo aver visto un risultato candidato. Non le inventa.
3. **Posizioni proposte su tutte le 24 decisioni.** Alcune sono mandati
   economici che non mi competono: su quelli propongo un default
   motivato e indico Filippo come owner.

## 8. Split temporali

Non applicabile: nessun addestramento o backtest eseguito. La v3 propone
tre regimi, con definizione operativa in 0C, e la gerarchia delle
evidenze della §1 che stabilisce quali fonti possono promuovere un
candidato e quali solo bloccarlo.

## 9. Codice e commit rilevanti

Nessun codice modificato. Commit invariati rispetto alla richiesta 002:
`640ca0e`, `259eba1`, `06006e3` (HEAD locale), `40bba21`, `5177e86`,
`98994d3`, `9ccaa9d`, `4f54be3`.

File di codice citati dalla v3: `dynamic_universe_final_comparison.py`
(righe 51-105 per score, `NextRet` e `static_equal_weight`),
`model_engine.py` (riga 46 per `pct_change`), `main.py`, `safe_state.py`,
`.github/workflows/run_bot.yml` (dipendenze non bloccate).

## 10. Metriche e risultati completi

| Calcolo | Valore |
| --- | --- |
| `SE = sqrt((1 + 1.155^2/504)/1.941)` | 0.7187 |
| intervallo 95% normale | [-0.254, 2.564] |

Coincide con il valore dell'audit 002 ottenuto dalla durata effettiva.
La v3 adotta questa versione e non più `T = 2`.

Nessun'altra metrica ricalcolata. Tutte le cifre storiche restano
ereditate e non verificate; la §12.3 della roadmap le classifica
individualmente come INVALID, UNRESOLVED, internamente ricomputabile o
UNKNOWN.

## 11. Assunzioni

1. Le dieci correzioni bloccanti dell'audit 002 vanno recepite, non
   discusse. La v3 non ne contesta nessuna.
2. Una roadmap può essere approvata dichiarando che il protocollo
   eseguibile è l'output delle Fasi 0A-0C. **Questa assunzione è
   esattamente ciò che la sezione 2 chiede di verificare**, quindi non
   va data per buona.
3. Le soglie economiche sono mandati di Filippo e non quantità derivabili
   da me.
4. L'auditor legge il working tree locale.

## 12. Limitazioni

1. Ho verificato direttamente sei affermazioni dell'audit 002 (sezione
   5), non tutte. Restano non riverificate da me: la suddivisione dei 52
   CSV per cartella, le finestre esatte per famiglia, la ricomputazione
   interna del run #10, le 4 chiamate download/history senza valore
   esplicito, l'assenza di dataset raw.
2. `AUDIT_RESULT_001.md` resta una ricostruzione. La formulazione DSR è
   stata corretta su indicazione dell'audit 002; potrebbero esistere
   altre discrepanze non rilevate.
3. La v3 non contiene soglie numeriche eseguibili, per scelta dichiarata.
4. Le 24 decisioni sono proposte, non chiuse. Nessuna fase può partire
   prima del relativo decision gate della §9.
5. La riga a 711 osservazioni con -16,26% è una scoperta nuova e **non
   spiegata**. Non so quale delle due righe sia il benchmark inteso, e
   non l'ho determinato perché è una scelta metodologica.
6. Non ho verificato se la mia proposta D4, criteri di eligibility
   generali al posto della break detection, sia sufficiente a gestire
   MSTR nei fatti. È una proposta, non un risultato.

## 13. Conclusione proposta da Claude

Proposta: la v3 risolve le dieci correzioni bloccanti, e le 24 posizioni
sono un punto di partenza difendibile. La v3 è approvabile **come piano
con posizioni proposte**, e non come protocollo eseguibile, che resta
l'output delle Fasi 0A-0C.

Proposta subordinata: anche se la v3 non fosse approvata, R0.1 può
partire, perché è strettamente forense, non adotta alcuna metodologia e
serve a risolvere discrepanze già accertate, incluse le due righe TopK
18 in conflitto.

Questa è una proposta. Chi l'ha scritta è la stessa parte che nell'audit
001 ha prodotto due derivazioni errate presentate come verificate, e
nell'audit 002 ha dichiarato risolti otto blocker quando uno non lo era.

## 14. Possibili rischi di leakage, bias, overfitting o data snooping

- **Lo spostamento come forma di risoluzione.** Il rischio principale
  della v3 è di aver ripetuto l'errore della v2 in forma più ordinata:
  dichiarare risolto un blocker avendolo rinviato a una fase o a una
  decisione. Questo è il primo punto da attaccare.
- **Snooping accumulato attraverso la progettazione.** La D24 ammette i
  risultati legacy solo per generare ipotesi, ma quell'uso è esso stesso
  un canale di snooping che la mappa di contaminazione deve contare, e
  non so se un conteggio sia realmente possibile a posteriori.
- **Ramo B scelto per inerzia economica.** La D1 propone di partire dal
  case study. Se poi la D15 non viene chiusa, il ramo B diventa
  permanente di fatto senza essere stato scelto come definitivo, che è
  il rischio che l'audit 002 segnalava.
- **Soglie non congelate.** Se le soglie 0C fossero fissate dopo avere
  visto risultati preliminari, l'intera impalcatura cade. La §2.5 lo
  vieta ma nulla nel repository lo impedisce tecnicamente.
- **Budget gerarchico come escape hatch.** La D5 e la §10 intendono
  chiudere la deriva dei target ML, ma un budget gerarchico può essere
  riallocato.
- **Difetti dati ancora presenti nel codice.** Le 31 `pct_change` e
  l'incoerenza `auto_adjust` sono documentate e non corrette.
- **Bias di conferma nella preparazione.** La descrizione dei rilievi
  passa attraverso la parte auditata.

## 15. Domande che l'auditor deve verificare

1. La riformulazione della natura del documento (sezione 2) è una
   risposta accettabile al motivo del rigetto della v2, o la v3 va
   respinta per lo stesso motivo?
2. La gerarchia development / robustness / confirmatory della §1 è
   corretta, e la classificazione delle sei fonti è giusta? In
   particolare, è difendibile la regola per cui la robustness evidence
   può solo bloccare una promozione e mai concederla?
3. DSR, PSR e test appaiato nella §2.2 sono ora distinti correttamente,
   con i riferimenti giusti?
4. Il vincolo della §2.1, per cui l'affermazione plurale sugli Sharpe
   resta INFERRED fino al ricalcolo individuale, è sufficiente?
5. La gestione dei calendari misti e di `q` per sleeve nella §2.3 e nella
   D22 è corretta?
6. Il contratto dati della §3.1 è sufficiente a rendere ammissibile un
   risultato, e la restituzione di R1.1 come coerenza interna anziché
   riproduzione da sorgente è accettabile?
7. I quality flag ortogonali della §3.3 sono completi, e il trattamento
   di `stale_value` è corretto?
8. I due rami dell'universo nella §4.2 sono davvero mutuamente
   esclusivi, e la conseguenza "sotto il ramo B, H1 non si esegue" è
   applicata con coerenza in tutto il documento?
9. Il lifecycle a tre stati della §5.2 risolve la contraddizione
   architetturale, o la sposta ancora?
10. La conformance suite della §5.3 copre gli otto punti che l'audit 002
    elencava?
11. La separazione fra baseline, diagnostiche e attribuzione della §6 è
    corretta, e la trend baseline canonica è davvero distinta dalla
    ricerca H2?
12. I tre livelli della §7 eliminano il problema segnalato, cioè che un
    candidato potesse superare i gate violando il mandato di rischio,
    fallendo il placebo o dipendendo da un solo asset?
13. Il placebo come gate inferenziale e lo schema di permutazione della
    D10 sono adeguati?
14. I criteri di stop della §8, incluso l'esito INCONCLUSIVE, sono ora
    verificabili?
15. La definizione di trial della D5 e la gerarchia di correzione della
    D19 rendono calcolabile il DSR?
16. Le 24 posizioni proposte della §11 contengono errori metodologici?
    In particolare la D4 (eligibility generale al posto della break
    detection), la D9 (fusione di H6 in H2), la D16 (convenzione di
    aggiustamento), la D22 (calendari e allocazione), la D24 (uso
    consentito dei risultati legacy).
17. L'elenco delle 24 decisioni è ora completo, o la v3 continua a
    decidere qualcosa implicitamente senza dichiararlo?
18. L'adjudication individuale della §12.1 e le classificazioni della
    §12.3 sono corrette?
19. La doppia riga TopK 18, 487 osservazioni con +87,15% contro 711 con
    -16,26%, ha una spiegazione determinabile dal repository, e quale
    delle due è il benchmark statico inteso?
20. La v3 introduce affermazioni nuove non supportate o contraddizioni
    interne che gli audit precedenti non potevano rilevare?
21. R0.1 può essere autorizzato ora, indipendentemente dall'esito su
    questa roadmap?

## PROMPT DA INVIARE A GPT-5.6 SOL

Agisci come auditor indipendente e avversariale. Non confermare la mia
proposta: cerca di falsificarla.

Oggetto: `docs/V2_RESEARCH_ROADMAP.md` versione 3, nel repository
`bot-trading-ml`. È la terza iterazione. Hai approvato la v1 con
modifiche e respinto la v2.

DOVE GUARDARE. I file sono locali e **non committati**.
`docs/V2_RESEARCH_ROADMAP.md` è untracked e non esiste su `origin/main`,
quindi non lo trovi su GitHub. Lavora sul working tree locale. `main`
locale è `06006e3`, `origin/main` è `640ca0e`, e i due commit di
differenza toccano solo i tre JSON di stato del bot.

Leggi, nell'ordine:

1. `docs/audits/AUDIT_REQUEST_003.md` — questo pacchetto, con assunzioni
   e limitazioni dichiarate;
2. `docs/audits/AUDIT_RESULT_002.md` — il tuo audit precedente, salvato
   verbatim;
3. `docs/V2_RESEARCH_ROADMAP.md` — il documento da auditare, versione 3;
4. `docs/RESEARCH_LOG.md` e `docs/BOT_TRADING_V2_MASTER_CONTEXT.md` —
   verifica che le contraddizioni che avevi segnalato siano chiuse e che
   non ne siano comparse altre;
5. `docs/audits/AUDIT_RESULT_001.md` — ricostruzione non verbatim, con la
   formulazione DSR corretta su tua indicazione.

AFFRONTA PER PRIMA QUESTA DOMANDA. Hai respinto la v2 perché era "un
piano per costruire il protocollo, non il protocollo eseguibile". La v3
non rivendica più di essere un protocollo eseguibile: si dichiara un
piano più un insieme di posizioni proposte, e colloca il protocollo
all'uscita delle Fasi 0A-0C. Stabilisci se questa riformulazione sia una
risposta accettabile o se la v3 vada respinta per lo stesso motivo. Dalla
risposta dipende il resto.

Verifica poi se le dieci correzioni bloccanti siano risolte o soltanto
spostate a una fase o a una decisione. Lo spostamento mascherato da
risoluzione è il rischio principale di questa versione: nella v2 avevo
dichiarato risolti otto blocker mentre uno non lo era.

Rispondi alle 21 domande della sezione 15.

Verifica autonomamente codice, dati e risultati. Non fidarti delle cifre
del pacchetto: ricalcolale. Ho verificato direttamente sei tue
affermazioni e le riporto nella sezione 5; restano non riverificate da
me la suddivisione dei 52 CSV per cartella, le finestre esatte per
famiglia, la ricomputazione interna del run #10, le chiamate
download/history senza valore esplicito e l'assenza di dataset raw.

Una questione empirica aperta su cui chiedo il tuo giudizio:
`dynamic_universe_fair_summary.csv` contiene due righe per TopK 18, una
con 487 osservazioni e +87,15% e una con 711 osservazioni e -16,26% con
drawdown -57,13%. Non è stata sollevata nel tuo audit 002. Determina, se
possibile dal repository, perché differiscano e quale sia il benchmark
statico inteso.

Cerca attivamente: leakage; look-ahead bias; survivorship bias;
selection bias; data snooping; overfitting; multiple testing; confronti
non equi; errori statistici; errori di implementazione; interpretazioni
eccessive; contraddizioni interne; decisioni importanti prese
implicitamente e non dichiarate nella sezione 11.

Valuta criticamente tre scelte che potrebbero essere sbagliate:

- la riformulazione della natura del documento, descritta sopra;
- la separazione delle soglie per origine, statistiche dalla power
  analysis in 0C ed economiche dal mandato 0A, con divieto di fissarle
  dopo aver visto un candidato, al posto di soglie numeriche nel
  documento;
- l'aver proposto una posizione su tutte e 24 le decisioni, incluse
  quelle che sono mandati economici di Filippo e non quantità che io
  possa derivare.

Vincoli operativi: non modificare alcun file; non fare commit; non fare
push; non eseguire workflow; non eseguire il bot; non riattivare il
retraining.

Produci in output:

- un **VERDETTO** esplicito fra `APPROVED`, `APPROVED WITH CHANGES`,
  `REJECTED`;
- per ciascuna delle dieci correzioni bloccanti dell'audit 002, se è
  RISOLTA, SPOSTATA o NON RISOLTA;
- i **blocker** residui, numerati;
- i problemi **metodologici**, **statistici** e di **implementazione**;
- le **correzioni richieste**, distinguendo bloccanti e migliorative;
- quali delle 24 posizioni proposte **approvi**, quali **respingi** e con
  quale controproposta;
- gli elementi approvati;
- i punti non verificabili e perché;
- se R0.1 possa essere autorizzato indipendentemente;
- per ogni affermazione rilevante, l'etichetta VERIFIED, INFERRED,
  HYPOTHESIS o UNKNOWN.
