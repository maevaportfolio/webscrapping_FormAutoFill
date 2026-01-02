"""
Script de test pour l'API Form Autofill - Version Améliorée
============================================================

Supporte:
- ✅ Formulaires classiques (nom, email, téléphone)
- ✅ Checkboxes (ex: garnitures pizza)
- ✅ Radios (ex: taille pizza)
- ✅ Selects
- ✅ Détection automatique des changements de page

Usage:
    1. Lancer l'API: python api_form_autofill_v2.py
    2. Lancer ce test: python test_simple_v2.py
"""
import requests
import time

# ===============================================
# 🔧 CONFIGURATION
# ===============================================

BASE_URL = "http://localhost:8000"
SESSION_ID = "test_session"

# 👇 URL À TESTER (modifier selon le site voulu)
TARGET_URL = "https://httpbin.org/forms/post"  # Formulaire pizza avec radios et checkboxes
# TARGET_URL = "https://www.airarabia.com/en"   # Site Air Arabia

# ===============================================
# 📝 VALEURS À REMPLIR
# ===============================================

# Valeurs pour le formulaire PIZZA (httpbin.org/forms/post)
PIZZA_VALUES = {
    # Champs texte
    "custname": "Jean Dupont",           # Nom du client
    "custtel": "+33123456789",           # Téléphone
    "custemail": "jean@example.com",     # Email
    "comments": "Test automatique - Livraison rapide SVP",  # Commentaires
    
    # Radio: Taille de pizza (choisir UNE valeur)
    "size": "medium",                    # Options: small, medium, large
    
    # Checkboxes: Garnitures (liste = cocher plusieurs)
    "topping": ["bacon", "cheese", "mushroom"],  # Cocher ces garnitures
}

# Valeurs pour formulaires CLASSIQUES (inscription, contact, etc.)
CLASSIC_VALUES = {
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.fr",
    "phone": "+33123456789",
    "address": "1 Rue Exemple",
    "city": "Paris",
    "zip": "75001",
    "passport": "12345678",
    "date_of_birth": "1990-01-15",
    "country": "France",
    "title": "Mrs."
}

# Choisir les valeurs selon l'URL
if "httpbin" in TARGET_URL:
    FORM_VALUES = PIZZA_VALUES
else:
    FORM_VALUES = CLASSIC_VALUES

# ===============================================
# 📊 FONCTIONS D'AFFICHAGE
# ===============================================

def afficher_resume(result):
    """Affiche un résumé formaté du remplissage"""
    print(f"\n{'='*60}")
    print(f"📋 RÉSUMÉ DES CHAMPS REMPLIS")
    print(f"{'='*60}")
    
    fields = result.get('filled_fields', [])
    print(f"📊 Total: {len(fields)} champ(s) rempli(s)\n")
    
    # Grouper par type
    by_type = {}
    for field in fields:
        ftype = field.get('type', 'unknown')
        if ftype not in by_type:
            by_type[ftype] = []
        by_type[ftype].append(field)
    
    # Afficher par type
    type_icons = {
        'text': '✏️',
        'email': '📧',
        'tel': '📞',
        'checkbox': '☑️',
        'radio': '🔘',
        'select': '🔽',
        'textarea': '📝'
    }
    
    for ftype, fields_list in by_type.items():
        icon = type_icons.get(ftype, '📌')
        print(f"{icon} {ftype.upper()} ({len(fields_list)})")
        for f in fields_list:
            print(f"   └─ {f.get('name', '?')}: {f.get('value', '?')}")
        print()
    
    print(f"{'='*60}\n")


def afficher_header():
    """Affiche l'en-tête du script"""
    print()
    print("="*60)
    print("🚀 TEST API FORM AUTOFILL - VERSION AMÉLIORÉE")
    print("="*60)
    print(f"📍 URL cible: {TARGET_URL}")
    print(f"📦 Valeurs: {len(FORM_VALUES)} champ(s) configuré(s)")
    print()


# ===============================================
# 🚀 SCRIPT PRINCIPAL
# ===============================================

def main():
    afficher_header()
    
    try:
        # =========================================
        # 1. CRÉER UNE SESSION
        # =========================================
        print("1️⃣  Création de la session...")
        
        response = requests.post(f"{BASE_URL}/session/create", json={
            "session_id": SESSION_ID,
            "url": TARGET_URL,
            "maximize": True
        })
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.json()}")
            return
        
        print(f"   ✅ Session '{SESSION_ID}' créée")
        time.sleep(3)  # Attendre le chargement
        
        # =========================================
        # 2. VÉRIFIER LA SESSION
        # =========================================
        print("\n2️⃣  Vérification de la session...")
        
        response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")
        session_info = response.json()
        
        print(f"   ✅ URL actuelle: {session_info['current_url']}")
        print(f"   ✅ Titre: {session_info['title']}")
        
        # =========================================
        # 3. REMPLIR LE FORMULAIRE
        # =========================================
        print("\n3️⃣  Remplissage du formulaire...")
        print(f"\n   📝 Valeurs à remplir:")
        for key, value in FORM_VALUES.items():
            if isinstance(value, list):
                print(f"      - {key}: {', '.join(value)}")
            else:
                print(f"      - {key}: {value}")
        
        response = requests.post(f"{BASE_URL}/form/fill", json={
            "session_id": SESSION_ID,
            "values": FORM_VALUES,
            "use_levenshtein": True,
            "levenshtein_threshold": 0.7
        })
        
        result = response.json()
        
        if response.status_code != 200:
            print(f"\n❌ Erreur: {result}")
            return
        
        afficher_resume(result)
        
        # =========================================
        # 4. MODE SURVEILLANCE
        # =========================================
        print("="*60)
        print("🔄 MODE SURVEILLANCE ACTIVÉ")
        print("="*60)
        print("💡 Le script surveille les changements de page.")
        print("   Navigue librement dans le navigateur.")
        print("   Les formulaires seront remplis automatiquement.")
        print("\n   Appuie sur Ctrl+C pour arrêter.\n")
        
        filled_urls = {session_info['current_url']}
        last_url = session_info['current_url']
        
        while True:
            try:
                time.sleep(3)
                
                # Vérifier l'URL actuelle
                response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")
                
                if response.status_code != 200:
                    print("⚠️  Session perdue. Fin du programme.")
                    break
                
                session_info = response.json()
                current_url = session_info['current_url']
                
                # Si changement de page
                if current_url != last_url and current_url not in filled_urls:
                    print(f"\n🔔 NOUVELLE PAGE DÉTECTÉE!")
                    print(f"   📍 URL: {current_url}")
                    print(f"   📄 Titre: {session_info['title']}")
                    
                    time.sleep(2)
                    
                    # Remplir le formulaire
                    print("   🔄 Remplissage en cours...")
                    response = requests.post(f"{BASE_URL}/form/fill", json={
                        "session_id": SESSION_ID,
                        "values": FORM_VALUES,
                        "use_levenshtein": True,
                        "levenshtein_threshold": 0.7
                    })
                    
                    result = response.json()
                    if response.status_code == 200:
                        nb = len(result.get('filled_fields', []))
                        print(f"   ✅ {nb} champ(s) rempli(s)")
                    else:
                        print(f"   ⚠️  Erreur: {result}")
                    
                    filled_urls.add(current_url)
                
                last_url = current_url
            
            except KeyboardInterrupt:
                print("\n\n" + "="*60)
                print("🛑 ARRÊT PAR L'UTILISATEUR")
                print("="*60)
                print("💡 Le navigateur reste ouvert. Ferme-le manuellement.")
                break
            
            except Exception as e:
                print(f"⚠️  Erreur: {e}")
                time.sleep(1)
    
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter à l'API")
        print("   Assure-toi que l'API est démarrée:")
        print("   → python api_form_autofill_v2.py")
    
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")


if __name__ == "__main__":
    main()
