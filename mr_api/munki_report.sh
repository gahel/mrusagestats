#!/bin/bash

# Munki Report API Script - Using curl with username/password auth
# This script authenticates with username and password

BASE_URL="https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
AUTH_ENDPOINT="/auth/login"
QUERY_ENDPOINT="/datatables/data"

# Autentiseringsdetaljer - OPPDATER DISSE
MR_USERNAME="${MR_USERNAME:-}" 
MR_PASSWORD="${MR_PASSWORD:-}"

if [ -z "$MR_USERNAME" ] || [ -z "$MR_PASSWORD" ]; then
    echo "❌ Feil: MR_USERNAME og MR_PASSWORD må settes som miljøvariabler"
    echo "   Eksempel: MR_USERNAME=user MR_PASSWORD=pass bash munki_report.sh"
    exit 1
fi

# Kolonnene vi ønsker å hente
COLUMNS=(
    "machine.name"
    "machine.serial_number"
    "machine.username"
    "reportdata.thermal_pressure"
    "reportdata.bytes_in"
)

# Bygg query string
QUERY=""
for i in "${!COLUMNS[@]}"; do
    QUERY="${QUERY}columns[${i}][name]=${COLUMNS[$i]}&"
done

echo "🔍 Munki Report - Thermal Pressure Checker"
echo ""

# Autentisering
echo "🔐 Autentiserer..."
AUTH_RESPONSE=$(curl -s -k \
    --cookie-jar /tmp/munki_cookies.txt \
    -d "login=${MR_USERNAME}&password=${MR_PASSWORD}" \
    "${BASE_URL}${AUTH_ENDPOINT}")

# Hent CSRF-token fra cookies
CSRF_TOKEN=$(grep -oP '(?<=CSRF-TOKEN\t)[^\t]+$' /tmp/munki_cookies.txt 2>/dev/null | tail -1)

if [ -z "$CSRF_TOKEN" ]; then
    echo "❌ Feil: Kunne ikke få CSRF-token. Sjekk brukernavn og passord."
    exit 1
fi

echo "✓ Autentisering vellykket"
echo "Henter maskiner fra Munki Report..."

# Gjør API-kall med CSRF-token og session cookie
RESPONSE=$(curl -s -k \
    -H "X-CSRF-TOKEN: $CSRF_TOKEN" \
    --cookie /tmp/munki_cookies.txt \
    -d "${QUERY}" \
    "${BASE_URL}${QUERY_ENDPOINT}")

# Parse JSON og filtrer thermal pressure
echo "$RESPONSE" | python3 << 'PYTHON'
import json
import sys

try:
    data = json.load(sys.stdin)
    machines = data.get('data', [])
    
    if not machines:
        print("✓ Alle maskiner har normal thermal pressure")
        sys.exit(0)
    
    # Filtrer maskiner med non-nominal thermal pressure
    issues = []
    for machine in machines:
        thermal = str(machine[3] if len(machine) > 3 else "unknown").lower()
        if thermal and thermal != "nominal":
            issues.append(machine)
    
    if not issues:
        print("✓ Alle maskiner har normal thermal pressure")
    else:
        print(f"\n⚠️  Fant {len(issues)} maskin(er) med termisk stress:\n")
        print(f"{'Navn':<20} {'Serial':<20} {'Bruker':<20} {'Thermal':<12}")
        print("-" * 72)
        for machine in issues:
            name = str(machine[0])[:20] if len(machine) > 0 else "unknown"
            serial = str(machine[1])[:20] if len(machine) > 1 else "unknown"
            user = str(machine[2])[:20] if len(machine) > 2 else "unknown"
            thermal = str(machine[3])[:12] if len(machine) > 3 else "unknown"
            print(f"{name:<20} {serial:<20} {user:<20} {thermal:<12}")
except json.JSONDecodeError as e:
    print(f"Feil: Kunne ikke parse JSON response: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Feil: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON
