"""
Script de test pour l'API Form Autofill - Version 5.0 NOUVEAU
==============================================================

NOUVELLE VERSION COMPLÈTE - DÉTECTION + REMPLISSAGE:
- ✅ Demande l'URL du site en terminal
- ✅ Demande le profil/personne concernée (profile1, profile2, profile3)
- ✅ Récupère les infos génériques des profils
- ✅ DÉTECTE les champs avec Levenshtein
- ✅ Affiche les matchings détectés
- ✅ REMPLIT automatiquement les formulaires
- ✅ Affiche le résultat du remplissage

Usage:
    python test_simple_v5_new.py
    
    Ou avec paramètres:
    python test_simple_v5_new.py https://example.com profile1
    python test_simple_v5_new.py https://example.com profile2
"""
import requests
import time
import sys
import json

# ===============================================
# 🔧 CONFIGURATION GLOBALE
# ===============================================

BASE_URL = "http://localhost:8000"
SESSION_ID = "test_session_generic"

# ===============================================
# 📋 PROFILS GÉNÉRIQUES
# ===============================================

AVAILABLE_PROFILES = {
    'profile1': 'Profil 1 - Voyageur Standard (Jean Dupont)',
    'profile2': 'Profil 2 - Client Affaires (Marie Martin)',
    'profile3': 'Profil 3 - Touriste International (Anna Schmidt)',
}

# ===============================================
# 🔧 FONCTIONS UTILITAIRES
# ===============================================

def print_header():
    """Affiche le header du programme"""
    print()
    print("=" * 70)
    print("🚀 FORM AUTOFILL - VERSION 5.0 GÉNÉRIQUE")
    print("=" * 70)
    print()

def get_profile_from_api(profile_id: str) -> dict:
    """Récupère les données d'un profil depuis l'API"""
    try:
        response = requests.get(f"{BASE_URL}/profiles/{profile_id}")
        if response.status_code == 200:
            return response.json()['data']
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erreur connexion API: {e}")
        return None

def list_available_profiles():
    """Affiche la liste des profils disponibles"""
    print("\n📋 PROFILS DISPONIBLES:")
    print("-" * 70)
    for profile_id, description in AVAILABLE_PROFILES.items():
        print(f"  • {profile_id}: {description}")
    print()

def ask_for_url() -> str:
    """Demande l'URL du site"""
    while True:
        url = input("🌐 Entrez l'URL du site (ou 'quit' pour quitter): ").strip()
        if url.lower() == 'quit':
            return None
        if url.startswith('http://') or url.startswith('https://'):
            return url
        else:
            print("❌ URL invalide. Utilisez http:// ou https://")

def ask_for_profile() -> str:
    """Demande le choix du profil"""
    while True:
        profile_id = input("👤 Choisissez un profil (profile1/profile2/profile3): ").strip().lower()
        if profile_id in AVAILABLE_PROFILES:
            return profile_id
        else:
            print(f"❌ Profil invalide. Disponibles: {', '.join(AVAILABLE_PROFILES.keys())}")

def ask_for_levenshtein_threshold() -> float:
    """Demande le seuil Levenshtein"""
    while True:
        try:
            threshold_str = input("📊 Seuil Levenshtein pour détection (0.0-1.0) [défaut: 0.5]: ").strip()
            if not threshold_str:
                return 0.5
            threshold = float(threshold_str)
            if 0.0 <= threshold <= 1.0:
                return threshold
            else:
                print("❌ Veuillez entrer une valeur entre 0.0 et 1.0")
        except ValueError:
            print("❌ Entrez un nombre valide")

def detect_and_fill_form(session_id: str, profile_data: dict, threshold: float = 0.5, form_number: int = 1) -> int:
    """
    Détecte et remplit UN formulaire.
    NOUVEAU: Utilise form_id pour s'assurer que detect et fill ciblent le même formulaire.
    Retourne le nombre de champs remplis (0 si aucun formulaire)
    """
    try:
        # DÉTECTION des champs du formulaire
        print(f"\n🔍 FORMULAIRE #{form_number} - DÉTECTION DES CHAMPS")
        print("=" * 70)
        
        response = requests.post(f"{BASE_URL}/form/detect", json={
            "session_id": session_id,
            "use_levenshtein": True,
            "levenshtein_threshold": threshold
        })
        
        if response.status_code != 200:
            print(f"❌ Erreur lors de la détection: {response.status_code}")
            return 0
        
        detect_result = response.json()
        detected_fields = detect_result.get('fields', [])
        total_fields = detect_result.get('total', 0)
        
        if total_fields == 0:
            print("❌ Aucun champ détecté")
            return 0
        
        # NOUVEAU: Extraire le form_id du premier champ détecté
        form_id = None
        if detected_fields:
            form_id = detected_fields[0].get('form_id')
        
        # Grouper les champs par form_id
        fields_by_form = {}
        for field in detected_fields:
            fid = field.get('form_id', 'unknown')
            if fid not in fields_by_form:
                fields_by_form[fid] = []
            fields_by_form[fid].append(field)
        
        print(f"\n✅ {len(detected_fields)} champ(s) détectés dans {len(fields_by_form)} formulaire(s):")
        print("-" * 70)
        
        # Afficher les champs par formulaire
        for fid, fields in fields_by_form.items():
            print(f"\n📋 FORMULAIRE: {fid}")
            for field in fields:
                field_type = field.get('type', '').upper()
                field_name = field.get('name', 'unknown')
                suggestions = field.get('suggestions', [])
                
                suggestion_str = ""
                if suggestions:
                    top_suggestion = suggestions[0]
                    suggestion_str = f" → {top_suggestion['field_type']} ({top_suggestion['score']})"
                
                print(f"  [{field_type:8}] {field_name:30} {suggestion_str}")
        
        print("-" * 70)
        
        # REMPLISSAGE du formulaire CIBLÉ
        print(f"\n📝 REMPLISSAGE DU FORMULAIRE: {form_id}")
        print("=" * 70)
        
        if not form_id:
            print("❌ Impossible de déterminer le form_id")
            return 0
        
        response = requests.post(f"{BASE_URL}/form/fill", json={
            "session_id": session_id,
            "values": profile_data,
            "use_levenshtein": True,
            "levenshtein_threshold": threshold,
            "form_id": form_id  # NOUVEAU: Passer le form_id pour cibler le bon formulaire
        })
        
        if response.status_code == 200:
            result = response.json()
            filled_fields = result.get('filled_fields', [])
            nb = len(filled_fields)
            
            print(f"\n✅ RÉSULTAT: {nb} champ(s) rempli(s) avec succès!")
            print("-" * 70)
            
            if filled_fields:
                for field in filled_fields:
                    field_type = field.get('type', '').upper()
                    field_name = field.get('name', 'unknown')
                    field_value = field.get('value', '')
                    
                    # Masquer les mots de passe
                    if field_type == 'PASSWORD':
                        field_value = '********'
                    
                    print(f"  ✓ [{field_type:8}] {field_name:30} = {field_value}")
            else:
                print("  ⚠️  Aucun champ rempli")
            
            print("-" * 70)
            return nb
        
        else:
            print(f"❌ Erreur lors du remplissage: {response.status_code}")
            print(response.text)
            return 0
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0

def run_test(url: str, profile_id: str, threshold: float = 0.5):
    """Exécute le monitoring CONTINU: détecte et remplit les formulaires quand vous naviguez"""
    
    print()
    print("=" * 70)
    print(f"🔗 URL: {url}")
    print(f"👤 Profil: {AVAILABLE_PROFILES.get(profile_id, profile_id)}")
    print(f"📊 Seuil Levenshtein: {threshold}")
    print("=" * 70)
    
    # 1. Récupérer les données du profil depuis l'API
    print("\n📥 Récupération des données du profil...")
    profile_data = get_profile_from_api(profile_id)
    if not profile_data:
        print("❌ Impossible de récupérer les données du profil")
        return False
    
    print(f"✅ Données du profil '{profile_id}' récupérées:")
    print(f"   Nom: {profile_data.get('first_name')} {profile_data.get('last_name')}")
    print(f"   Email: {profile_data.get('email')}")
    print(f"   Pays: {profile_data.get('country')}")
    
    # 2. Créer une session
    print("\n🌐 Création de session...")
    try:
        response = requests.post(f"{BASE_URL}/session/create", json={
            "session_id": SESSION_ID,
            "url": url,
            "maximize": True
        })
        
        if response.status_code != 200:
            print(f"❌ Erreur création session: {response.status_code}")
            print(response.text)
            return False
        
        print("✅ Session créée")
        
    except requests.exceptions.ConnectionError:
        print("❌ API non connectée!")
        print("   Lancez d'abord: python api_form_autofill_v5.py")
        return False
    
    # 3. Attendre le chargement
    print(f"⏳ Chargement de la page ({url})...")
    time.sleep(4)
    
    # 4. MONITORING CONTINU
    print("\n" + "=" * 70)
    print("🎯 MODE MONITORING CONTINU ACTIVÉ")
    print("=" * 70)
    print("\n📌 Comportement:")
    print("   • Remplissage AUTOMATIQUE UNE SEULE FOIS par formulaire")
    print("   • Naviguez librement sur le site")
    print("   • Chaque page sera remplie qu'une seule fois")
    print("   • Appuyez sur Ctrl+C pour arrêter")
    print("\n" + "=" * 70)
    
    form_number = 1
    last_url = url
    filled_urls = set()  # Tracker les URLs déjà remplies
    last_filled_url = None  # Dernière URL remplie
    no_form_count = 0
    max_no_form_attempts = 3  # Nombre de tentatives sans formulaire avant de déclarer fin
    
    try:
        while True:
            # Obtenir l'URL actuelle
            try:
                response = requests.get(f"{BASE_URL}/sessions")
                sessions = response.json().get('sessions', [])
                current_session = next((s for s in sessions if s['id'] == SESSION_ID), None)
                current_url = current_session['url'] if current_session else last_url
            except:
                current_url = last_url
            
            # Vérifier si l'URL a changé (navigation)
            if current_url != last_url:
                print(f"\n🌍 NAVIGATION DÉTECTÉE")
                print(f"   Ancienne URL: {last_url}")
                print(f"   Nouvelle URL: {current_url}")
                last_url = current_url
                no_form_count = 0  # Réinitialiser le compteur
                time.sleep(3)  # Attendre le chargement
            
            # Vérifier si cette URL a déjà été remplie
            if current_url in filled_urls:
                if current_url == last_filled_url:
                    # Même URL, même formulaire - éviter la boucle infinie
                    no_form_count += 1
                    if no_form_count >= max_no_form_attempts:
                        print(f"\n⏸️  Trop de tentatives sur la même page")
                        print(f"   URL: {current_url}")
                        print(f"   (Naviguez vers une autre page)")
                        time.sleep(2)
                        continue
                else:
                    # URL différente mais déjà traitée
                    print(f"\n✅ Cette page a déjà été remplie")
                    print(f"   (Naviguez vers une autre page)")
                    time.sleep(2)
                    continue
            
            # Essayer de détecter et remplir un formulaire
            filled_count = detect_and_fill_form(SESSION_ID, profile_data, threshold, form_number)
            
            if filled_count > 0:
                # Formulaire trouvé et rempli - tracker cette URL
                filled_urls.add(current_url)
                last_filled_url = current_url
                form_number += 1
                no_form_count = 0
                print(f"\n✅ Formulaire #{form_number-1} rempli et mémorisé")
                print(f"⏳ En attente de navigation vers une nouvelle page...")
                print(f"   (Appuyez sur Ctrl+C pour arrêter)")
                time.sleep(3)  # Attendre avant la prochaine tentative
            else:
                # Aucun formulaire trouvé
                no_form_count += 1
                if no_form_count == 1:
                    print(f"\n⏳ Aucun formulaire détecté sur cette page")
                    print(f"   Naviguez vers une page avec un formulaire...")
                
                # Vérifier régulièrement s'il y a un nouveau formulaire
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt de l'utilisateur")
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    finally:
        print("\n👀 Le navigateur reste ouvert pour inspection")
        print("   Appuyez sur Ctrl+C pour fermer le navigateur")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Fermeture du navigateur...")


def main():
    """Fonction principale"""
    print_header()
    
    # Vérifier les paramètres en ligne de commande
    if len(sys.argv) >= 3:
        # Mode non-interactif avec paramètres
        url = sys.argv[1]
        profile_id = sys.argv[2]
        threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
        
        print(f"📌 Mode paramètres détecté")
        print(f"   URL: {url}")
        print(f"   Profil: {profile_id}")
        print(f"   Seuil: {threshold}")
        
    else:
        # Mode interactif
        list_available_profiles()
        
        # Demander l'URL
        url = ask_for_url()
        if not url:
            print("\n👋 Au revoir!")
            return
        
        # Demander le profil
        profile_id = ask_for_profile()
        
        # Demander le seuil Levenshtein
        threshold = ask_for_levenshtein_threshold()
    
    # Exécuter le test
    run_test(url, profile_id, threshold)

if __name__ == "__main__":
    main()
