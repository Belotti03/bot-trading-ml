# CURSOR / CLAUDE WORKFLOW

## Roles

### ChatGPT

Independent researcher/reviewer. Challenge hypotheses, inspect results,
and independently audit Claude/Cursor work.

### Claude/Cursor

Repository-aware quant researcher/developer. Inspect actual
code/history, reproduce claims, propose experiments, and implement only
after approval.

## Golden rule

The repository is the long-term memory. Chats are temporary.

Record important discoveries in: - `docs/RESEARCH_LOG.md` - V1/V2 design
documents - experiment result files - tests/code where appropriate

## New chat

1. Read `AGENTS.md` or `CLAUDE.md`.
2. Read `docs/BOT_TRADING_V2_MASTER_CONTEXT.md`.
3. Inspect the relevant current code.
4. State what is verified versus inherited.
5. Do not edit automatically.



## Research phase

Use Ask/Plan/read-only behavior. Return: - hypothesis - baseline/null -
data period - train/test protocol - leakage controls - costs/slippage -
metrics - failure modes - acceptance/rejection criteria

## Implementation phase

Only after explicit approval: - use a branch - make coherent changes -
add tests - run validation - report exact files changed and tests run -
never silently change research assumptions

## Audit phase

After implementation, ChatGPT independently reviews the diff and
results.

## V1 safety

Do not resume the V1 cron while NaN corruption is unresolved. Do not
erase corrupted state before forensic reconstruction. Do not rely on
historical metrics until their code/data provenance is verified.

Status 2026-10-06: the first condition is satisfied and the cron pause
is revoked; `run_bot.yml` is active, `retrain.yml` is
`disabled_manually`. The second and third rules remain in force. The
reasoning is recorded in `docs/RESEARCH_LOG.md` and
`docs/BOT_TRADING_V2_MASTER_CONTEXT.md`. If the cron is ever paused
again, record the reason and the revocation condition in the research
log rather than leaving it implicit.

## Communication

Be direct and quantitative. Label claims VERIFIED / INFERRED /
HYPOTHESIS / UNKNOWN.

## REGOLA OBBLIGATORIA DI AUDIT INDIPENDENTE V2

Durante lo sviluppo di V2, Claude è il ricercatore e sviluppatore principale, ma non è l'autorità finale sulle decisioni metodologiche, architetturali o strategiche.

Ogni volta che un risultato, un esperimento o una proposta può modificare una decisione importante di V2, Claude DEVE fermarsi prima di implementare o adottare quella decisione e richiedere un audit indipendente a GPT-5.6 Sol.

Sono considerate decisioni importanti almeno:

- modifica dell'universo degli asset;
- modifica del target o dell'horizon ML;
- scelta, aggiunta o eliminazione di feature;
- scelta o sostituzione del modello/algoritmo;
- modifica della metodologia di training, validation o walk-forward;
- modifica delle regole di ingresso o uscita;
- modifica di position sizing, risk management, stop o trailing stop;
- modifica delle assunzioni di costi, commissioni o slippage;
- scelta di parametri ottenuti tramite ottimizzazione;
- confronto tra strategie o architetture;
- conclusione che una variante è migliore di V1 o di un'altra variante;
- qualsiasi modifica architetturale o strategica di V2;
- qualsiasi risultato che possa essere influenzato da leakage, look-ahead bias, survivorship bias, overfitting o data snooping.

Prima dell'audit, Claude deve preparare un riepilogo riproducibile contenente:

1. domanda o decisione da valutare;
2. ipotesi testata;
3. dati e periodo utilizzati;
4. metodologia e split temporali;
5. codice e commit rilevanti;
6. metriche e risultati completi;
7. assunzioni e limitazioni;
8. conclusione proposta da Claude.

L'audit GPT-5.6 Sol deve essere avversariale e indipendente: deve cercare attivamente errori metodologici, leakage, bias, overfitting, data snooping, confronti non equi, problemi statistici e interpretazioni eccessive dei risultati, senza assumere che la conclusione di Claude sia corretta.

Claude NON deve procedere con l'implementazione della decisione contestata finché l'audit non è stato completato e Filippo non ha approvato la decisione finale.

Per modifiche puramente tecniche e non strategiche (bugfix evidente, refactoring senza cambio di comportamento, test, logging, documentazione, ecc.) non è necessario un audit preventivo.

In caso di dubbio, Claude deve considerare la modifica importante e richiedere l'audit.

## PROCEDURA OPERATIVA PER RICHIEDERE AUDIT A GPT-5.6 SOL

Quando una decisione richiede audit indipendente, Claude NON deve chiedere a Filippo di inventare o scrivere manualmente il prompt per GPT.

Claude deve preparare automaticamente un pacchetto di audit riproducibile.

### 1. Creazione della richiesta di audit

Claude deve creare un file:

`docs/audits/AUDIT_REQUEST_<ID>.md`

dove `<ID>` è progressivo o comunque univoco.

Il file deve contenere:

1. Titolo della decisione da auditare.

2. Domanda precisa a cui GPT deve rispondere.

3. Contesto necessario.

4. Ipotesi testata.

5. Dati utilizzati.

6. Periodo temporale.

7. Metodologia.

8. Split temporali.

9. Codice e commit rilevanti.

10. Metriche e risultati completi.

11. Assunzioni.

12. Limitazioni.

13. Conclusione proposta da Claude.

14. Possibili rischi di leakage, bias, overfitting o data snooping.

15. Elenco preciso delle domande che GPT deve verificare.

### 2. Prompt pronto per GPT

Lo stesso file deve contenere alla fine una sezione:

`## PROMPT DA INVIARE A GPT-5.6 SOL`

Claude deve scrivere qui un prompt completo, già pronto per essere copiato e incollato nella chat GPT-5.6 Sol di Cursor.

Il prompt deve chiedere a GPT di:

- leggere direttamente il repository;

- verificare autonomamente codice, dati e risultati;

- cercare di falsificare la conclusione di Claude;

- non modificare file;

- non fare commit;

- non fare push;

- produrre un verdetto esplicito;

- elencare eventuali blocker;

- distinguere fatti verificati, inferenze e punti non verificabili.

Filippo non deve essere obbligato a costruire manualmente il prompt.

### 3. Stop obbligatorio

Dopo aver creato `AUDIT_REQUEST_<ID>.md`, Claude deve fermarsi.

Claude NON deve:

- implementare la decisione auditata;

- modificare codice strategico;

- fare commit;

- fare push;

- considerare la propria proposta approvata.

Deve comunicare semplicemente a Filippo che il pacchetto di audit è pronto.

### 4. Audit GPT

Filippo copia la sezione `PROMPT DA INVIARE A GPT-5.6 SOL` nella chat GPT di Cursor.

GPT deve lavorare esclusivamente come auditor indipendente.

GPT non deve modificare il repository.

### 5. Risultato dell'audit

Il risultato di GPT deve essere salvato nel repository come:

`docs/audits/AUDIT_RESULT_<ID>.md`

Il risultato deve contenere almeno:

- VERDETTO:

  - APPROVED

  - APPROVED WITH CHANGES

  - REJECTED

- blocker;

- problemi metodologici;

- problemi statistici;

- problemi di implementazione;

- correzioni richieste;

- eventuali elementi approvati;

- eventuali punti non verificabili.

### 6. Ripresa del lavoro da parte di Claude

Claude deve leggere `AUDIT_RESULT_<ID>.md`.

Se il risultato è `REJECTED`, Claude deve fermarsi e non implementare la decisione.

Se il risultato è `APPROVED WITH CHANGES`, Claude deve prima recepire le modifiche richieste e, se necessario, richiedere un nuovo audit.

Se il risultato è `APPROVED`, Claude può procedere con l'implementazione solo dopo l'approvazione esplicita di Filippo.

### 7. Indipendenza dell'audit

Claude deve preparare il problema in modo neutrale.

Non deve costruire il prompt per convincere GPT che la propria conclusione sia corretta.

Il prompt deve chiedere esplicitamente a GPT di cercare errori, falsificare l'ipotesi e verificare:

- leakage;

- look-ahead bias;

- survivorship bias;

- selection bias;

- data snooping;

- overfitting;

- multiple testing;

- confronti non equi;

- errori statistici;

- errori di implementazione;

- interpretazioni eccessive dei risultati.

### 8. Quando NON creare un audit

Non è necessario creare un audit per:

- bugfix evidente;

- refactoring senza cambio di comportamento;

- test;

- logging;

- documentazione;

- pulizia del codice;

- miglioramenti tecnici che non modificano metodologia, strategia o risultati.

In caso di dubbio, Claude deve richiedere l'audit.