"""
Script de test pour l'API Form Autofill - Version 3.0 Complète
==============================================================

Configurations prêtes pour :
- httpbin.org (pizza) - Radios + Checkboxes
- Air Arabia - Réservation vol
- Booking.com - Réservation hôtel
- SNCF Connect - Connexion
- Spotify - Inscription multi-étapes
- DemoQA - Formulaire complet de test

Usage:
    1. Lancer l'API: python api_form_autofill_v3.py
    2. Modifier SITE_CONFIG ci-dessous pour choisir le site
    3. Lancer: python test_simple_v3.py
"""
import requests
import time

# ===============================================
# 🔧 CONFIGURATION GLOBALE
# ===============================================

BASE_URL = "http://localhost:8000"
SESSION_ID = "test_session"

# ===============================================
# 🌐 CONFIGURATIONS PAR SITE
# ===============================================

SITE_CONFIGS = {
    
    # ==========================================
    # 1. HTTPBIN PIZZA - Test de base
    # ==========================================
    "httpbin": {
        "url": "https://httpbin.org/forms/post",
        "description": "Formulaire pizza avec radios et checkboxes",
        "values": {
            # Champs texte
            "custname": "Jean Dupont",
            "custtel": "+33612345678",
            "custemail": "jean.dupont@example.com",
            
            # Radio: Taille de pizza
            "size": "medium",  # Options: small, medium, large
            
            # Checkboxes: Garnitures (liste = cocher plusieurs)
            "topping": ["bacon", "cheese", "mushroom"],
            
            # Textarea
            "comments": "Test automatique - Livraison rapide SVP !",
        }
    },
    
    # ==========================================
    # 2. AIR ARABIA - Réservation vol
    # ==========================================
    "airarabia": {
        "url": "https://www.airarabia.com/en",
        "description": "Formulaire passagers compagnie aérienne",
        "values": {
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean.dupont@example.com",
            "phone": "+33612345678",
            "passport": "12AB34567",
            "date_of_birth": "1990-01-15",
            "country": "France",
            "title": "Mr",
            "gender": "Male",
        }
    },
    
    # ==========================================
    # 3. BOOKING.COM - Réservation hôtel
    # ==========================================
    "booking": {
        "url": "https://secure.booking.com/book.html?hotel_id=51900&occupancy_setup_issue_flags=&aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaE2IAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4ApGh4MoGwAIB0gIkNGJkMzJmZGUtOWE5MS00NDRkLTg0NDgtMTI3NTMwZTVhMjIy2AIB4AIB&sid=f23b5f5ded41e4c9b771e1ba9b6783c6&room1=A%2CA&error_url=%2Fhotel%2Ffr%2Fhotelwestminster.html%3Faid%3D304142%26label%3Dgen173nr-10CAEoggI46AdIM1gEaE2IAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4ApGh4MoGwAIB0gIkNGJkMzJmZGUtOWE5MS00NDRkLTg0NDgtMTI3NTMwZTVhMjIy2AIB4AIB%26sid%3Df23b5f5ded41e4c9b771e1ba9b6783c6%26srpvid%3D89eb831356ad0a78%26%26&hostname=www.booking.com&stage=1&checkin=2026-01-08&interval=2&children_extrabeds=&srpvid=89eb831356ad0a78&hp_visits_num=1&rt_pos_selected=1&rt_pos_selected_within_room=1&rt_selected_block_position=1&rt_num_blocks=38&rt_num_rooms=8&rt_num_blocks_per_room=%7B%225190045%22%3A4%2C%225190040%22%3A4%2C%225190005%22%3A6%2C%225190002%22%3A6%2C%225190041%22%3A4%2C%225190001%22%3A6%2C%225190043%22%3A4%2C%225190042%22%3A4%7D&rt_selected_blocks_info=%7B%225190001_91458119_0_2_0%22%3A%7B%22rt_selected_block_position_in_rt%22%3A1%2C%22rt_selected_block_position_in_room_group%22%3A0%2C%22count%22%3A1%2C%22rt_room_symmetry_category%22%3A%22asymmetric%22%7D%7D&rt_relevance_metric_id=cc38af87-f97c-4876-a950-f728c3ac4b8b&rt_pageview_id=f0818318ba26187b&rt_pos_final=1.1&rt_selected_total_price=863&rt_cheapest_search_price=863&rt_with_no_dimensions=&from_source=hotel&nr_rooms_5190001_91458119_0_2_0=1&basket_id=7d80da42-1693-4169-979e-7a91b5f39d67",
        "description": "Réservation hôtel avec options voyage",
        "values": {
            # Identité
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean.dupont@example.com",
            "phone": "+33612345678",
            
            # Radios: Pour qui réservez-vous ?
            "booking_for": "main_guest",  # 'main_guest' ou 'other_guest'
            
            # Radios: Voyagez-vous pour le travail ?
            "traveling_for_work": "no",  # 'yes' ou 'no'
            
            # Select: Heure d'arrivée
            "arrival_time": "15:00",  # Sera matché avec la plage horaire
            
            # Checkboxes: Options supplémentaires
            "car_rental": True,       # Location voiture
            "airport_transfer": True,  # Transfert aéroport
            
            # Adresse
            "address": "15 Rue de la Paix",
            "city": "Paris",
            "zip": "75001",
            "country": "France",
        }
    },
    
    # ==========================================
    # 4. SNCF CONNECT - Connexion
    # ==========================================
    "sncf": {
        "url": "https://www.sncf-connect.com/app/home/login",
        "description": "Page de connexion SNCF avec 'Se souvenir de moi'",
        "values": {
            "email": "jean.dupont@example.com",
            "password": "MonMotDePasse123!",
            
            # Checkbox: Se souvenir de moi
            "remember_me": True,
        }
    },
    
    # ==========================================
    # 5. SPOTIFY - Inscription (multi-étapes)
    # ==========================================
    "spotify": {
        "url": "https://www.spotify.com/signup",
        "description": "Inscription Spotify en plusieurs étapes",
        "values": {
            # Étape 1: Email
            "email": "jean.dupont.test@gmail.com",
            
            # Étape 2: Mot de passe (avec contraintes)
            "password": "SecurePass123!",  # Min 10 chars, 1 lettre, 1 chiffre/special
            
            # Étape 3: Profil
            "username": "jean.dupont.test@gmail.com",
            "date_of_birth": "15-november-1990",
            "gender": "Female",
            
            # Checkboxes
            "newsletter": False,
            "terms": True,
            "gender": "Female",
        }
    },
    
    # ==========================================
    # 6. DEMOQA - Formulaire de test complet
    # ==========================================
    "demoqa": {
        "url": "https://demoqa.com/automation-practice-form",
        "description": "Formulaire de test avec tous types de champs",
        "values": {
            "firstName": "Jean",
            "lastName": "Dupont",
            "userEmail": "jean.dupont@example.com",
            "userNumber": "0612345678",
            
            # Radio: Genre
            "gender": "Male",  # Male, Female, Other
            
            # Checkboxes: Hobbies
            "hobbies": ["Sports", "Reading", "Music"],
            
            # Adresse
            "currentAddress": "15 Rue de la Paix, 75001 Paris",
            
            # Date
            "dateOfBirthInput": "15 Jan 1990",
        }
    },
    
    # ==========================================
    # 7. FORMY - Formulaire simple
    # ==========================================
    "formy": {
        "url": "https://formy-project.herokuapp.com/form",
        "description": "Formulaire simple de test",
        "values": {
            "first-name": "Jean",
            "last-name": "Dupont",
            "job-title": "Data Scientist",
            "date": "01/15/1990",
            
            # Radio: Niveau d'éducation
            "education": "college",  # high-school, college, grad-school
            
            # Checkbox
            "sex": "Male",
        }
    },
    
    # ==========================================
    # 8. THE INTERNET - Checkboxes isolées
    # ==========================================
    "checkboxes": {
        "url": "https://the-internet.herokuapp.com/checkboxes",
        "description": "Page de test avec checkboxes uniquement",
        "values": {
            # Cocher les deux checkboxes
            "checkbox": True,
        }
    },
}

# ==========================================
# 👇 CHOISIR LE SITE À TESTER ICI
# ==========================================
CURRENT_SITE = "booking"  # Modifier cette ligne pour changer de site
# Options: "httpbin", "airarabia", "booking", "sncf", "spotify", "demoqa", "formy", "checkboxes"

# ===============================================
# 📊 FONCTIONS D'AFFICHAGE
# ===============================================

def afficher_header(config):
    """Affiche l'en-tête avec les infos du site"""
    print()
    print("=" * 70)
    print("🚀 TEST API FORM AUTOFILL - VERSION 3.0 COMPLÈTE")
    print("=" * 70)
    print(f"📍 Site: {CURRENT_SITE.upper()}")
    print(f"🌐 URL: {config['url']}")
    print(f"📝 Description: {config['description']}")
    print(f"📦 Nombre de valeurs configurées: {len(config['values'])}")
    print("=" * 70)
    print()


def afficher_resume(result):
    """Affiche un résumé formaté du remplissage"""
    print(f"\n{'='*70}")
    print(f"📋 RÉSUMÉ DES CHAMPS REMPLIS")
    print(f"{'='*70}")
    
    fields = result.get('filled_fields', [])
    print(f"📊 Total: {len(fields)} champ(s) rempli(s)\n")
    
    # Grouper par type
    by_type = {}
    for field in fields:
        ftype = field.get('type', 'unknown')
        if ftype not in by_type:
            by_type[ftype] = []
        by_type[ftype].append(field)
    
    # Icônes par type
    icons = {
        'text': '✏️', 'email': '📧', 'tel': '📞', 'number': '🔢',
        'checkbox': '☑️', 'radio': '🔘', 'select': '🔽',
        'textarea': '📝', 'password': '🔒', 'date': '📅'
    }
    
    for ftype, fields_list in by_type.items():
        icon = icons.get(ftype, '📌')
        print(f"{icon} {ftype.upper()} ({len(fields_list)})")
        for f in fields_list:
            name = f.get('name', '?')
            value = f.get('value', '?')
            if ftype == 'password':
                value = '********'
            print(f"   └─ {name}: {value}")
        print()
    
    print(f"{'='*70}\n")


def afficher_sites_disponibles():
    """Affiche la liste des sites configurés"""
    print("\n📚 SITES DISPONIBLES:")
    print("-" * 50)
    for key, config in SITE_CONFIGS.items():
        marker = "→" if key == CURRENT_SITE else " "
        print(f"  {marker} {key:12} : {config['description'][:40]}")
    print("-" * 50)
    print(f"💡 Pour changer de site, modifier CURRENT_SITE = \"{CURRENT_SITE}\"")
    print()


# ===============================================
# 🚀 SCRIPT PRINCIPAL
# ===============================================

def main():
    # Récupérer la config du site choisi
    if CURRENT_SITE not in SITE_CONFIGS:
        print(f"❌ Site '{CURRENT_SITE}' non trouvé!")
        afficher_sites_disponibles()
        return
    
    config = SITE_CONFIGS[CURRENT_SITE]
    
    afficher_header(config)
    afficher_sites_disponibles()
    
    try:
        # =========================================
        # 1. CRÉER UNE SESSION
        # =========================================
        print("1️⃣  Création de la session...")
        
        response = requests.post(f"{BASE_URL}/session/create", json={
            "session_id": SESSION_ID,
            "url": config["url"],
            "maximize": True
        })
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.json()}")
            return
        
        print(f"   ✅ Session '{SESSION_ID}' créée")
        time.sleep(3)
        
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
        print(f"\n3️⃣  Remplissage du formulaire...")
        print(f"\n   📝 Valeurs à remplir:")
        for key, value in config["values"].items():
            if isinstance(value, list):
                print(f"      - {key}: {', '.join(str(v) for v in value)}")
            elif key == 'password':
                print(f"      - {key}: ********")
            else:
                print(f"      - {key}: {value}")
        
        response = requests.post(f"{BASE_URL}/form/fill", json={
            "session_id": SESSION_ID,
            "values": config["values"],
            "use_levenshtein": True,
            "levenshtein_threshold": 0.6
        })
        
        result = response.json()
        
        if response.status_code != 200:
            print(f"\n❌ Erreur: {result}")
            return
        
        afficher_resume(result)
        
        # =========================================
        # 4. MODE SURVEILLANCE
        # =========================================
        print("=" * 70)
        print("🔄 MODE SURVEILLANCE ACTIVÉ")
        print("=" * 70)
        print("💡 Le script surveille les changements de page.")
        print("   Navigue librement dans le navigateur.")
        print("   Les formulaires seront remplis automatiquement.")
        print("\n   Appuie sur Ctrl+C pour arrêter.\n")
        
        filled_urls = {session_info['current_url']}
        last_url = session_info['current_url']
        
        while True:
            try:
                time.sleep(3)
                
                response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")
                
                if response.status_code != 200:
                    print("⚠️  Session perdue. Fin du programme.")
                    break
                
                session_info = response.json()
                current_url = session_info['current_url']
                
                if current_url != last_url and current_url not in filled_urls:
                    print(f"\n🔔 NOUVELLE PAGE DÉTECTÉE!")
                    print(f"   📍 URL: {current_url[:60]}...")
                    print(f"   📄 Titre: {session_info['title']}")
                    
                    time.sleep(2)
                    
                    print("   🔄 Remplissage en cours...")
                    response = requests.post(f"{BASE_URL}/form/fill", json={
                        "session_id": SESSION_ID,
                        "values": config["values"],
                        "use_levenshtein": True,
                        "levenshtein_threshold": 0.6
                    })
                    
                    result = response.json()
                    if response.status_code == 200:
                        nb = len(result.get('filled_fields', []))
                        print(f"   ✅ {nb} champ(s) rempli(s)")
                        
                        # Afficher les détails
                        for f in result.get('filled_fields', []):
                            print(f"      - {f['type']}: {f['name']} = {f['value']}")
                    else:
                        print(f"   ⚠️  Erreur: {result}")
                    
                    filled_urls.add(current_url)
                
                last_url = current_url
            
            except KeyboardInterrupt:
                print("\n\n" + "=" * 70)
                print("🛑 ARRÊT PAR L'UTILISATEUR")
                print("=" * 70)
                print("💡 Le navigateur reste ouvert. Ferme-le manuellement.")
                break
            
            except Exception as e:
                print(f"⚠️  Erreur: {e}")
                time.sleep(1)
    
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter à l'API")
        print("   Assure-toi que l'API est démarrée:")
        print("   → python api_form_autofill_v3.py")
    
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")


if __name__ == "__main__":
    main()
