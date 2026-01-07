# Munki Report API Script

Python-script for å hente maskiner med termisk stress fra Munki Report API.

Passordet lagres **sikkert i macOS Keychain** i stedet for hardkoding.

## Oppsett

### 1. Installer dependencies
```bash
pip install -r requirements.txt
```

### 2. Opprett en dedikert API-bruker i Munki Report

**Enkel oppsett:**
1. Logg inn i Munki Report som admin
2. Gå til **Administration** → **Users** (eller **Settings** → **Users**)
3. Klikk **Add User** eller **New User**
4. Fyll inn:
   - **Username**: `api_user` (eller ditt valgte navn)
   - **Password**: Velg et sterkt passord
   - **Email**: (valgfritt) `api@example.com`
5. Lagre brukeren

Det er det! Du trenger ikke å gi brukeren spesielle tillatelser - scriptet bruker bare sitt eget accountt for å hente data.

### 3. Konfigurer scriptet
Åpne `munki_report.py` og sett:
```python
CONFIG = {
    "base_url": "https://munkireport.example.com/index.php?",  # Din URL
    "keychain_service": "munki-report-api",  # Kan endres
    "keychain_username": "api_user",  # Ditt brukernavn i Munki Report
    ...
}
```

### 4. Lagre passord i Keychain
Kjør setupkommandoen første gang:
```bash
python3 munki_report.py --setup
```

Scriptet vil spørre deg om passordet og lagre det sikkert i macOS Keychain.

### 5. Kjør scriptet
```bash
python3 munki_report.py
```

## Alternativ: Manuel lagring i Keychain
Hvis du foretrekker det, kan du lagre passordet direkte:
```bash
security add-generic-password -s "munki-report-api" -a "api_user" -w
```

Så vil security vise en prompt der du kan paste passordet.

## Output

```
🔍 Munki Report - Thermal Pressure Checker

Henter kredentialer fra Keychain...
Autentiserer...
✓ Autentisert

Henter maskiner fra Munki Report...
Hentet 107 maskiner, filtrerer thermal pressure...

⚠️  Fant 2 maskin(er) med termisk stress:

Navn                 Serial               Bruker               Thermal      Bytes In    
------------------------------------------------------------------------------------
MBP-26692            XG506M5JYY           Arne Sæten           Heavy        1.09 MB/s   
MBP-09790            MY7NY4PWPK           Live Wang Jensen     Heavy        174.49 kB/s
```

## Sikkerhet

✓ Passordet lagres **kryptert** i macOS Keychain
✓ Scriptet bruker dedikert bruker (ikke admin)
✓ CSRF-token håndteres automatisk
✓ SSL kan verifiseres i produksjon

## Tilpasninger

Du kan enkelt endre scriptet til å:
- Legge til flere kolonner i `COLUMNS`
- Filtrer på andre thermal pressure-nivåer
- Lagre resultater til fil (CSV/JSON)
- Sende varsler (epost, Slack, etc.)
- Kjøre på et tidsplan (cron)
