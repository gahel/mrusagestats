# CLAUDE.md - Instruksjoner for AI-assistenter

## Prosjektoversikt
Dette er et Python-prosjekt for å interagere med MunkiReport API. Scriptsene brukes til å hente data, analysere maskiner, og administrere MunkiReport-databasen.

## Virtual Environment
**VIKTIG:** Alltid aktiver virtual environment før du kjører Python-scripts:

```bash
source .venv/bin/activate
```

Eller kjør med full path:
```bash
.venv/bin/python3 script.py
```

## Vanlige kommandoer

### Slette en maskin fra MunkiReport
```bash
source .venv/bin/activate && python3 delete_machine.py <SERIENUMMER>
```

For å finne serienummeret fra maskinnavn (f.eks. MBP-17675):
```bash
bash get_data.sh | python3 -c "import sys, json; data = json.load(sys.stdin); machines = [m for m in data.get('data', []) if 'MBP-17675' in str(m)]; print(machines[0][1] if machines else 'Ikke funnet')"
```

### Hente data fra MunkiReport
```bash
bash get_data.sh
```

### Analysere en maskin
```bash
source .venv/bin/activate && python3 analyze_machine.py <MASKINNAVN>
```

## Autentisering
- Passord hentes automatisk fra macOS Keychain (`munkireport-api`)
- Bruker: `localuser`
- Base URL: `https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?`

## Dataformat
- Serienummer er andre kolonne (indeks 1) i API-responsen
- Maskinnavn/hostname er tredje kolonne (indeks 2)
