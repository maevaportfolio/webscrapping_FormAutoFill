"""
Script de test pour l'API Form Autofill - Version 5.0
=====================================================

CORRECTIONS v5 :
- ✅ Basic-Fit : Adresses séparées correctement (rue ≠ numéro ≠ ville)
- ✅ Basic-Fit : Radio genre Homme/Femme/Autre corrigé
- ✅ Basic-Fit : Checkboxes communication corrigées
- ✅ Meilleure détection par attributs HTML (name, id, placeholder)

Usage:
    python test_simple_v5.py
    python test_simple_v5.py basicfit
    python test_simple_v5.py spotify
"""
import requests
import time
import sys

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
    # 1. HTTPBIN PIZZA
    # ==========================================
    "httpbin": {
        "url": "https://httpbin.org/forms/post",
        "description": "Formulaire pizza avec radios et checkboxes",
        "values": {
            "custname": "Jean Dupont",
            "custtel": "+33612345678",
            "custemail": "jean.dupont@example.com",
            "size": "medium",
            "topping": ["bacon", "cheese", "mushroom"],
            "delivery": "11:00", 
            "comments": "Test automatique - Livraison rapide SVP !",
        }
    },
    
    # ==========================================
    # 2. COPINE DE VOYAGE
    # ==========================================
    "copinevoyage": {
        "url": "https://www.copinesdevoyage.com/connexion?_target_path=https%3A%2F%2Fwww.copinesdevoyage.com%2F",
        "description": "Formulaire d'inscription complet",
        "values": {
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean.dupont@example.com",
            "phone": "+33612345678",
            "passport": "12AB34567",
            "date_of_birth": "1990-01-15",
            "country": "France",
            "title": "Mr",
            "gender": "male",
            "password": "MonMotDePasse123!",
        }
    },
    
    # ==========================================
    # 3. BOOKING.COM
    # ==========================================
    "booking": {
        "url": "https://secure.booking.com/book.html?hotel_id=79870&occupancy_setup_issue_flags=&aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaE2IAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AuyO4MoGwAIB0gIkOTU2MDQxNmUtYWJlYy00NDQ1LTgzNWItNTdjNzczNTUxNDZl2AIB4AIB&sid=55694d8635b921de6b1c4268c78e95bc&room1=A%2CA&error_url=%2Fhotel%2Ffr%2Fa-la-villa-madame.fr.html%3Faid%3D304142%26label%3Dgen173nr-10CAEoggI46AdIM1gEaE2IAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AuyO4MoGwAIB0gIkOTU2MDQxNmUtYWJlYy00NDQ1LTgzNWItNTdjNzczNTUxNDZl2AIB4AIB%26sid%3D55694d8635b921de6b1c4268c78e95bc%26srpvid%3Db3c9955021ed0d1b%26%26&hostname=www.booking.com&stage=1&checkin=2026-01-09&interval=2&children_extrabeds=&srpvid=b3c9955021ed0d1b&hp_visits_num=1&rt_pos_selected=1&rt_pos_selected_within_room=1&rt_selected_block_position=1&rt_num_blocks=27&rt_num_rooms=5&rt_num_blocks_per_room=%7B%227987002%22%3A6%2C%227987013%22%3A6%2C%227987001%22%3A6%2C%227987012%22%3A6%2C%227987016%22%3A3%7D&rt_selected_blocks_info=%7B%227987001_88550925_0_2_0%22%3A%7B%22rt_selected_block_position_in_rt%22%3A1%2C%22rt_selected_block_position_in_room_group%22%3A0%2C%22count%22%3A1%2C%22rt_room_symmetry_category%22%3A%22asymmetric%22%7D%7D&rt_relevance_metric_id=bb9e62cb-5bce-4c4f-adfc-d1eddc037d14&rt_pageview_id=9fe2955692861a6d&rt_pos_final=1.1&rt_selected_total_price=555&rt_cheapest_search_price=555&rt_with_no_dimensions=&from_source=hotel&nr_rooms_7987001_88550925_0_2_0=1&basket_id=c95b3856-9253-4a19-beac-3014d2bc5409",
        "description": "Réservation hôtel avec radios Yes/No",
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
    # 4. SNCF CONNECT
    # ==========================================
    "sncf": {
        "url": "https://www.sncf-connect.com/app/home/login",
        "description": "Connexion SNCF avec 'Se souvenir de moi'",
        "values": {
            "email": "jean.dupont@example.com",
            "password": "MonMotDePasse123!",
            "remember_me": True,
        }
    },
    
    # ==========================================
    # 5. SPOTIFY
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
            "name": "jean.dupont",
            "date_of_birth": "15-november-1990",
            "gender": "Female",
            "newsletter": False,
            "terms": True,
        }
    },
    
    # ==========================================
    # 6. DOMINO'S PIZZA
    # ==========================================
    "dominos": {
        "url": "https://commande.dominos.fr/login",
        "description": "Inscription avec programme fidélité",
        "values": {
            "email": "jean.dupont@example.com",
            "full_name": "Jean Dupont",
            "first_name": "Jean",
            "last_name": "Dupont",
            "phone": "+33612345678",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "loyalty": True,
            "newsletter": True,
            "terms": True,
            # CGU Domino's - plusieurs variantes
            "accept": True,
            "terms_of_use": True,
            "personal_data": True,
            "checking": True,  # "By checking this box"
        }
    },
    
    # ==========================================
    # 7. BASIC-FIT - CORRIGÉ ✅
    # ==========================================
    "basicfit": {
        "url": "https://www.basic-fit.com/fr-fr/inscription",
        "description": "Inscription Basic-Fit (genre, adresse, communication)",
        "values": {
            # ===== RADIO GENRE =====
            # Les valeurs exactes du site Basic-Fit
            "gender": "Homme",  # Options exactes: "Homme", "Femme", "Autre"
            
            # ===== IDENTITÉ =====
            "first_name": "Jean",
            "last_name": "Dupont",
            "phone": "+33612345678",
            
            # ===== EMAIL =====
            "email": "jean.dupont@example.com",
            "email_confirm": "jean.dupont@example.com",
            
            # ===== DATE DE NAISSANCE =====
            "date_of_birth": "15/01/1990",  # Format DD/MM/YYYY pour Basic-Fit
            "birthday": "15/01/1990",
            "anniversaire": "15/01/1990",
            
            # ===== ADRESSE - CHAMPS SÉPARÉS =====
            # Basic-Fit a des champs séparés, il faut les identifier par leur nom exact
            "zip": "75001",
            "postal": "75001",
            "postcode": "75001",
            "code_postal": "75001",
            
            "numero": "15",
            "number": "15",
            "numéro": "15",
            "housenumber": "15",
            
            "rue": "Rue de la Paix",
            "street": "Rue de la Paix",
            
            "complement": "Appartement 3B",
            "extra": "Appartement 3B",
            "additional": "Appartement 3B",
            
            "city": "Paris",
            "ville": "Paris",
            
            # ===== CHECKBOXES COMMUNICATION =====
            # Textes exacts des checkboxes Basic-Fit
            "partenaires": False,      # "promotions de la part des partenaires"
            "partner": False,
            "partner_promo": False,
            "promotions": False,
            
            "assistance": True,        # "utiliser mes données...assistance"
            "profil": True,
            "contact": True,
            "communication": True,
            "data_usage": True,
            
            # ===== CGU =====
            "terms": True,
            "conditions": True,
            "accept": True,
        }
    },
    
    # ==========================================
    # 8. DEMOQA
    # ==========================================
    "demoqa": {
        "url": "https://demoqa.com/automation-practice-form",
        "description": "Formulaire de test complet",
        "values": {
            "firstName": "Jean",
            "lastName": "Dupont",
            "userEmail": "jean.dupont@example.com",
            "userNumber": "0612345678",
            "gender": "Male",
            "hobbies": ["Sports", "Reading", "Music"],
            "currentAddress": "15 Rue de la Paix, 75001 Paris",
        }
    },
    
    # ==========================================
    # 9. FORMY
    # ==========================================
    "formy": {
        "url": "https://formy-project.herokuapp.com/form",
        "description": "Formulaire simple de test",
        "values": {
            "first-name": "Jean",
            "last-name": "Dupont",
            "job-title": "Data Scientist",
            "date": "01/15/1990",
            "education": "college",
            "sex": "Male",
        }
    },
    
    # ==========================================
    # 10. CHECKBOXES
    # ==========================================
    "checkboxes": {
        "url": "https://the-internet.herokuapp.com/checkboxes",
        "description": "Test checkboxes uniquement",
        "values": {
            "checkbox": True,
        }
    },
}

# ===============================================
# 📊 FONCTIONS D'AFFICHAGE
# ===============================================

def afficher_menu():
    """Affiche le menu de sélection des sites"""
    print()
    print("=" * 60)
    print("🚀 FORM AUTOFILL - SÉLECTION DU SITE")
    print("=" * 60)
    print()
    
    sites = list(SITE_CONFIGS.keys())
    
    for i, site in enumerate(sites, 1):
        config = SITE_CONFIGS[site]
        print(f"  {i:2}. {site:12} - {config['description'][:40]}")
    
    print()
    print(f"  0. Quitter")
    print()
    print("-" * 60)
    
    return sites


def choisir_site():
    """Demande à l'utilisateur de choisir un site"""
    sites = afficher_menu()
    
    while True:
        try:
            choix = input("👉 Entre le numéro ou le nom du site : ").strip()
            
            if choix == "0" or choix.lower() == "q":
                print("👋 Au revoir !")
                return None
            
            if choix.isdigit():
                index = int(choix) - 1
                if 0 <= index < len(sites):
                    return sites[index]
                else:
                    print(f"❌ Numéro invalide (1-{len(sites)})")
            
            elif choix.lower() in SITE_CONFIGS:
                return choix.lower()
            
            else:
                print(f"❌ Site '{choix}' non trouvé")
        
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            return None


def afficher_resume(result):
    """Affiche un résumé formaté"""
    print(f"\n{'='*60}")
    print(f"📋 RÉSUMÉ DES CHAMPS REMPLIS")
    print(f"{'='*60}")
    
    fields = result.get('filled_fields', [])
    print(f"📊 Total: {len(fields)} champ(s)\n")
    
    by_type = {}
    for field in fields:
        ftype = field.get('type', 'unknown')
        if ftype not in by_type:
            by_type[ftype] = []
        by_type[ftype].append(field)
    
    icons = {
        'text': '✏️', 'email': '📧', 'tel': '📞',
        'checkbox': '☑️', 'radio': '🔘', 'select': '🔽',
        'textarea': '📝', 'password': '🔒'
    }
    
    for ftype, fields_list in by_type.items():
        icon = icons.get(ftype, '📌')
        print(f"{icon} {ftype.upper()} ({len(fields_list)})")
        for f in fields_list:
            val = '********' if ftype == 'password' else f.get('value', '?')
            print(f"   └─ {f.get('name', '?')}: {val}")
        print()
    
    print(f"{'='*60}\n")


# ===============================================
# 🚀 SCRIPT PRINCIPAL
# ===============================================

def run_test(site_name):
    """Lance le test pour un site"""
    
    if site_name not in SITE_CONFIGS:
        print(f"❌ Site '{site_name}' non trouvé!")
        return False
    
    config = SITE_CONFIGS[site_name]
    
    print()
    print("=" * 60)
    print(f"🚀 TEST: {site_name.upper()}")
    print("=" * 60)
    print(f"🌐 URL: {config['url']}")
    print(f"📝 {config['description']}")
    print("=" * 60)
    
    try:
        # 1. Créer session
        print("\n1️⃣  Création de la session...")
        
        response = requests.post(f"{BASE_URL}/session/create", json={
            "session_id": SESSION_ID,
            "url": config["url"],
            "maximize": True
        })
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.json()}")
            return False
        
        print(f"   ✅ Session créée")
        time.sleep(3)
        
        # 2. Vérifier session
        print("\n2️⃣  Vérification...")
        
        response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")
        session_info = response.json()
        
        print(f"   ✅ Titre: {session_info['title']}")
        
        # 3. Remplir
        print(f"\n3️⃣  Remplissage du formulaire...")
        
        response = requests.post(f"{BASE_URL}/form/fill", json={
            "session_id": SESSION_ID,
            "values": config["values"],
            "use_levenshtein": True,
            "levenshtein_threshold": 0.5
        })
        
        result = response.json()
        
        if response.status_code != 200:
            print(f"\n❌ Erreur: {result}")
            return False
        
        afficher_resume(result)
        
        # 4. Surveillance
        print("=" * 60)
        print("🔄 MODE SURVEILLANCE")
        print("=" * 60)
        print("💡 Navigue librement, Ctrl+C pour arrêter.\n")
        
        filled_urls = {session_info['current_url']}
        last_url = session_info['current_url']
        
        while True:
            try:
                time.sleep(3)
                
                response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")
                if response.status_code != 200:
                    break
                
                session_info = response.json()
                current_url = session_info['current_url']
                
                if current_url != last_url and current_url not in filled_urls:
                    print(f"\n🔔 Nouvelle page: {session_info['title']}")
                    time.sleep(2)
                    
                    response = requests.post(f"{BASE_URL}/form/fill", json={
                        "session_id": SESSION_ID,
                        "values": config["values"],
                        "use_levenshtein": True,
                        "levenshtein_threshold": 0.5
                    })
                    
                    if response.status_code == 200:
                        nb = len(response.json().get('filled_fields', []))
                        print(f"   ✅ {nb} champ(s) rempli(s)")
                    
                    filled_urls.add(current_url)
                
                last_url = current_url
            
            except KeyboardInterrupt:
                print("\n\n🛑 Arrêt. Navigateur ouvert.")
                break
        
        return True
    
    except requests.exceptions.ConnectionError:
        print("❌ API non connectée. Lance: python api_form_autofill_v5.py")
        return False


def main():
    print()
    print("=" * 60)
    print("🚀 FORM AUTOFILL - VERSION 5.0")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        site_name = sys.argv[1].lower()
        if site_name in SITE_CONFIGS:
            run_test(site_name)
        else:
            print(f"❌ Site '{site_name}' non trouvé!")
            print(f"   Disponibles: {', '.join(SITE_CONFIGS.keys())}")
    else:
        site_name = choisir_site()
        if site_name:
            run_test(site_name)


if __name__ == "__main__":
    main()
