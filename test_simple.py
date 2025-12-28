"""
Script de test simple pour l'API Form Autofill
Testez sur le lien de votre choix
"""
import requests
import time

# ===============================================
# 🔧 CONFIGURATION - Modifiez ces valeurs
# ===============================================

BASE_URL = "http://localhost:8000"
SESSION_ID = "test_session"

# 👇 VOTRE LIEN A TESTER ICI (A modifier si tu veux tester un autre lien)
TARGET_URL = "https://httpbin.org/forms/post"
#"https://www.airarabia.com/en"

# Valeurs à remplir dans le formulaire
FORM_VALUES = {
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

# ===============================================
# 🚀 SCRIPT DE TEST
# ===============================================

def afficher_resume(result):
    """Affiche un résumé formaté du remplissage"""
    print(f"\n✅ Remplissage complété!")
    print(f"{'='*60}")
    print(f"📋 RÉSUMÉ DES CHAMPS REMPLIS")
    print(f"{'='*60}")
    print(f"📊 Total: {len(result.get('filled_fields', []))} champs remplis\n")
    
    for i, field in enumerate(result.get('filled_fields', []), 1):
        print(f"  {i}. {field['name']}")
        print(f"     └─ Type: {field['type']}")
        print(f"     └─ Valeur: {field['value']}")
    
    print(f"\n{'='*60}\n")


def main():
    print("="*60)
    print("TEST API FORM AUTOFILL")
    print("="*60)
    
    try:
        # 1. Créer une session
        print(f"\n1️⃣ Création d'une session...")
        print(f"   URL: {TARGET_URL}")
        
        response = requests.post(f"{BASE_URL}/session/create", json={
            "session_id": SESSION_ID,
            "url": TARGET_URL,
            "maximize": True
        })
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.json()}")
            return
        
        print(f"✅ Session créée: {response.json()['session_id']}")
        time.sleep(3)  # Attendre que la page charge
        
        # 2. Vérifier la session
        print(f"\n2️⃣ Vérification de la session (GET)...")
        response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")
        session_info = response.json()
        print(f"   ✅ Page actuellement ouverte: {session_info['current_url']}")
        print(f"   ✅ Titre: {session_info['title']}")
        
        # 3. Remplir le formulaire initial
        print(f"\n3️⃣ Remplissage du formulaire initial...")
        print(f"   Valeurs à remplir:")
        for key, value in FORM_VALUES.items():
            print(f"     - {key}: {value}")
        
        response = requests.post(f"{BASE_URL}/form/fill", json={
            "session_id": SESSION_ID,
            "values": FORM_VALUES,
            "use_levenshtein": True,
            "levenshtein_threshold": 0.7
        })
        
        result = response.json()
        if response.status_code != 200:
            print(f"❌ Erreur: {result}")
            return
        
        afficher_resume(result)
        
        # Boucle de détection automatique des changements de page
        print(f"{'='*60}")
        print(f"🔄 SURVEILLANCE AUTOMATIQUE DES CHANGEMENTS DE PAGE")
        print(f"{'='*60}")
        print(f"💡 Le script surveille automatiquement les changements de page")
        print(f"   Navigue librement, les formulaires seront remplis auto.\n")
        
        # Tracker les URLs déjà remplies pour éviter les doublons
        filled_urls = {session_info['current_url']}
        last_url = session_info['current_url']
        time.sleep(3)  # Attendre 3 secondes avant de commencer la surveillance
        check_interval = 3  # Vérifier toutes les 3 secondes
        
        while True:
            try:
                time.sleep(check_interval)
                
                # Vérifier si l'URL a changé
                response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")
                if response.status_code != 200:
                    print(f"⚠️ Session perdue. Fin du programme.")
                    break
                
                session_info = response.json()
                current_url = session_info['current_url']
                current_title = session_info['title']
                
                # Si la page a changé ET n'a pas déjà été remplie
                if current_url != last_url and current_url not in filled_urls:
                    print(f"\n{'='*60}")
                    print(f"📍 CHANGEMENT DE PAGE DÉTECTÉ!")
                    print(f"{'='*60}")
                    print(f"   📄 Nouvelle URL: {current_url}")
                    print(f"   📑 Titre: {current_title}\n")
                    
                    # Attendre que la page se charge complètement
                    time.sleep(2)
                    
                    # Remplir le formulaire
                    print(f"🔄 Remplissage automatique du formulaire...")
                    response = requests.post(f"{BASE_URL}/form/fill", json={
                        "session_id": SESSION_ID,
                        "values": FORM_VALUES,
                        "use_levenshtein": True,
                        "levenshtein_threshold": 0.7
                    })
                    
                    result = response.json()
                    if response.status_code == 200:
                        afficher_resume(result)
                    else:
                        print(f"⚠️ Erreur lors du remplissage: {result}\n")
                    
                    # Enregistrer cette URL comme remplie
                    filled_urls.add(current_url)
                
                last_url = current_url
            
            except KeyboardInterrupt:
                print(f"\n\n{'='*60}")
                print(f"🛑 ARRÊT PAR L'UTILISATEUR")
                print(f"{'='*60}")
                print(f"💡 Le navigateur reste ouvert. Ferme-le manuellement.")
                break
            
            except Exception as e:
                print(f"⚠️ Erreur: {e}")
                time.sleep(1)
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Erreur: Impossible de se connecter à l'API")
        print(f"   Assure-toi que l'API est démarrée avec: python api_form_autofill.py")
        return
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return


if __name__ == "__main__":
    main()
