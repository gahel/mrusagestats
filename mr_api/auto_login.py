#!/usr/bin/env python3
"""
Munki Report - Auto-login and extract session cookie
Bruker Selenium til å logge inn automatisk
"""

import os
import keyring
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net",
    "keychain_account": "gaute.helfjord@spk.no",
}

def get_credentials():
    """Hent kredentialer fra Keychain"""
    account = CONFIG['keychain_account']
    password = keyring.get_password(account, account)
    
    if not password:
        print(f"❌ Passord for '{account}' ikke funnet i Keychain")
        exit(1)
    
    return account, password

def auto_login_and_get_cookie():
    """Åpne nettleseren, logg inn, og hent PHPSESSID"""
    
    print("🔐 Auto-login and Extract Session Cookie\n")
    
    username, password = get_credentials()
    print(f"Bruker: {username}\n")
    
    # Start Chrome
    print("Åpner nettleseren...")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Fjern kommentar for headless mode
    driver = webdriver.Chrome(options=options)
    
    try:
        # Åpne login-siden
        print("Navigerer til Munki Report...")
        driver.get(CONFIG['base_url'])
        
        # Vent på login-form
        print("Venter på login-form...")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginfmt"))
        )
        
        # Skriv inn email
        print(f"Logger inn som {username}...")
        email_input.send_keys(username)
        driver.find_element(By.ID, "idSIButton9").click()
        
        # Vent på password-felt
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "passwd"))
        )
        
        # Skriv inn passord
        password_input.send_keys(password)
        driver.find_element(By.ID, "idSIButton9").click()
        
        # Vent på at siden laster (veit ikke eksakt element, så vent litt)
        print("Venter på autentisering...")
        time.sleep(5)
        
        # Hent PHPSESSID cookie
        cookies = driver.get_cookies()
        phpsessid = None
        
        for cookie in cookies:
            if cookie['name'] == 'PHPSESSID':
                phpsessid = cookie['value']
                break
        
        if not phpsessid:
            print("❌ PHPSESSID cookie ikke funnet")
            print(f"Cookies funnet: {[c['name'] for c in cookies]}")
            return False
        
        # Lagre cookie
        cookie_file = os.path.expanduser("~/.mr_session_cookie")
        with open(cookie_file, 'w') as f:
            f.write(f'PHPSESSID={phpsessid}')
        os.chmod(cookie_file, 0o600)
        
        print(f"\n✓ Session cookie lagret!")
        print(f"✓ PHPSESSID: {phpsessid[:20]}...")
        print(f"\nDu kan nå kjøre: ./munki_report.py")
        return True
    
    except Exception as e:
        print(f"❌ Feil: {e}")
        return False
    
    finally:
        driver.quit()

if __name__ == "__main__":
    auto_login_and_get_cookie()
