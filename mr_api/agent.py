#!/usr/bin/env python3
"""
Munki Report Agent - Spør om din maskinpark
Analyser machines.json og svar på spørsmål
"""

import json
import sys
from datetime import datetime

def load_machines(filename="machines.json"):
    """Load machines from JSON"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ {filename} ikke funnet. Kjør først: ./export_machines.py")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ {filename} er ikke gyldig JSON")
        sys.exit(1)

def ask_question(machines, question):
    """Svar på spørsmål om maskinene"""
    
    q = question.lower()
    
    # THERMAL/PERFORMANCE
    if any(word in q for word in ['thermal', 'varme', 'heat', 'stress', 'heavy']):
        thermal_issues = [m for m in machines if m.get('thermal_pressure') == 'Heavy']
        if thermal_issues:
            print(f"\n🌡️  {len(thermal_issues)} maskiner med HEAVY thermal pressure:")
            for m in thermal_issues:
                age = m['last_report']['age_human'] or 'ukjent'
                print(f"\n  {m['hostname']} (Bruker: {m['console_user']})")
                print(f"    Modell: {m['description']}")
                print(f"    Sist rapport: {age}")
        else:
            print("\n✓ Alle maskiner har normal termisk belastning")
        return
    
    # CPU LOAD / HIGH LOAD
    if any(word in q for word in ['cpu', 'load', 'belastning', 'høy', 'high', 'stall']):
        high_cpu = [m for m in machines if m['cpu']['load_percent'] and m['cpu']['load_percent'] > 75]
        if high_cpu:
            high_cpu = sorted(high_cpu, key=lambda x: x['cpu']['load_percent'], reverse=True)
            print(f"\n⚙️  {len(high_cpu)} maskiner med høy CPU-belastning (>75%):")
            for m in high_cpu:
                age = m['last_report']['age_human'] or 'ukjent'
                print(f"\n  {m['hostname']:<20} CPU: {m['cpu']['load_percent']:.1f}%")
                print(f"    Bruker: {m['console_user']}")
                print(f"    Modell: {m['description']}")
                print(f"    Sist rapport: {age}")
        else:
            print("\n✓ Alle maskiner har CPU-belastning < 75%")
        return
    
    # INAKTIVE / OLD / NOT REPORTED
    if any(word in q for word in ['inaktiv', 'inactive', 'old', 'gammel', 'aldri', 'rapportert', 'report']):
        inactive = [m for m in machines if m['last_report']['age_seconds'] and m['last_report']['age_seconds'] > 2592000]
        if inactive:
            inactive = sorted(inactive, key=lambda x: x['last_report']['age_seconds'], reverse=True)
            print(f"\n⏱️  {len(inactive)} maskiner som ikke har rapportert på >30 dager:")
            for m in inactive:
                print(f"\n  {m['hostname']:<20} Sist rapport: {m['last_report']['age_human']}")
                print(f"    Bruker: {m['console_user']}")
                print(f"    Modell: {m['description']}")
        else:
            print("\n✓ Alle maskiner har rapportert innen de siste 30 dagene")
        return
    
    # REPLACE / UPGRADE / BYTTE UT
    if any(word in q for word in ['bytt', 'replace', 'upgrade', 'oppdater', 'nye', 'ny']):
        candidates = []
        
        # Maskiner med både høy CPU og thermal issues
        for m in machines:
            score = 0
            reasons = []
            
            if m.get('thermal_pressure') == 'Heavy':
                score += 2
                reasons.append("Heavy thermal pressure")
            
            if m['cpu']['load_percent'] and m['cpu']['load_percent'] > 85:
                score += 2
                reasons.append(f"CPU: {m['cpu']['load_percent']:.1f}%")
            
            if score > 0:
                candidates.append((m, score, reasons))
        
        if candidates:
            candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
            print(f"\n🔴 {len(candidates)} maskiner som bør vurderes byttet ut:")
            for m, score, reasons in candidates[:10]:
                age = m['last_report']['age_human'] or 'ukjent'
                print(f"\n  {m['hostname']:<20} (Prioritet: {score}/4)")
                print(f"    Bruker: {m['console_user']}")
                print(f"    Modell: {m['description']}")
                print(f"    Problemer: {', '.join(reasons)}")
                print(f"    Sist rapport: {age}")
        else:
            print("\n✓ Ingen maskiner som oppfyller kriteriene for utskifting")
        return
    
    # DEFAULT - oversikt
    print("\n📊 MASKINPARK OVERSIKT")
    print(f"Total maskiner: {len(machines)}")
    
    thermal_heavy = len([m for m in machines if m.get('thermal_pressure') == 'Heavy'])
    high_cpu = len([m for m in machines if m['cpu']['load_percent'] and m['cpu']['load_percent'] > 75])
    inactive = len([m for m in machines if m['last_report']['age_seconds'] and m['last_report']['age_seconds'] > 2592000])
    
    print(f"Heavy thermal pressure: {thermal_heavy}")
    print(f"Høy CPU-belastning (>75%): {high_cpu}")
    print(f"Inaktive (>30 dager): {inactive}")
    
    print(f"\n💡 Prøv: 'thermal', 'cpu', 'inaktiv', 'bytt ut'")

if __name__ == "__main__":
    machines = load_machines()
    
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        ask_question(machines, question)
    else:
        print("🤖 Munki Report Agent")
        print(f"Lastet {len(machines)} maskiner fra machines.json\n")
        print("Stille spørsmål: agent.py \"ditt spørsmål\"")
        print("\nEksempler:")
        print("  agent.py \"Hvilke maskiner har høyt thermal pressure?\"")
        print("  agent.py \"Vis maskiner med høy CPU-belastning\"")
        print("  agent.py \"Hvilke maskiner burde byttet ut?\"")
        print("  agent.py \"Inaktive maskiner\"")
