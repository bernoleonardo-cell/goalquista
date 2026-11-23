# Goalquista

Conquista l'Europa una domanda di calcio alla volta. Gioco di strategia e quiz sul calcio europeo, in italiano e in inglese.

Gioca: https://bernoleonardo-cell.github.io/goalquista/

Il sito è generato dal prototipo in Claude Design con `build_web.py`: non modificare i file a mano.

## Sfida un amico (online)

La sfida tra due amici passa per Firebase Realtime Database (progetto `goalquista`, regione europe-west1).
Le regole di sicurezza del database sono in `database.rules.json`: vanno incollate nella console di Firebase,
Realtime Database → Regole → Pubblica. L'accesso anonimo deve essere attivo (Authentication → Metodo di accesso → Anonimo).
Il SDK di Firebase è in `vendor/` e si carica solo quando un giocatore apre «Sfida un amico».
Prova con due telefoni simulati: `python3 tools/test/mp_test.py <cartella del sito>` (usa un Firebase finto, nessuna rete).
