"""
CLI Form Autofill - Remplissage automatique de formulaires
Choisissez un profil et un site à visiter
"""

import argparse
import sys
from api_form_autofill_v5 import (
    create_driver, fill_forms, detect_fields, GENERIC_PROFILES
)
import time

def print_header(text):
    """Affiche un header avec du style"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_profiles():
    """Affiche la liste des profils disponibles"""
    print_header("📋 PROFILS DISPONIBLES")
    
    for idx, (profile_id, profile_data) in enumerate(GENERIC_PROFILES.items(), 1):
        name = profile_data.get('name', profile_id)
        email = profile_data.get('email', '---')
        country = profile_data.get('country', '---')
        print(f"{idx}. {profile_id.upper()}")
        print(f"   📝 Nom: {name}")
        print(f"   📧 Email: {email}")
        print(f"   🌍 Pays: {country}")
        print()

def get_profile_interactive():
    """Sélectionne un profil interactivement"""
    print_header("🎯 SÉLECTION DU PROFIL")
    
    profiles = list(GENERIC_PROFILES.keys())
    
    for idx, profile_id in enumerate(profiles, 1):
        print(f"{idx}. {profile_id}")
    
    while True:
        try:
            choice = input(f"\nChoisissez un profil (1-{len(profiles)}): ").strip()
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(profiles):
                selected = profiles[choice_idx]
                return selected
            else:
                print(f"❌ Veuillez entrer un nombre entre 1 et {len(profiles)}")
        except ValueError:
            print(f"❌ Entrée invalide. Veuillez entrer un nombre.")

def display_profile_info(profile_id):
    """Affiche les informations détaillées du profil"""
    profile = GENERIC_PROFILES.get(profile_id)
    if not profile:
        return
    
    print_header(f"👤 PROFIL: {profile_id.upper()}")
    
    print(f"📝 Nom: {profile.get('name', '---')}")
    print(f"👤 Prénom: {profile.get('first_name', '---')}")
    print(f"👤 Nom de famille: {profile.get('last_name', '---')}")
    print(f"📧 Email: {profile.get('email', '---')}")
    print(f"📞 Téléphone: {profile.get('phone', '---')}")
    print(f"🏠 Adresse: {profile.get('address', '---')}")
    print(f"🏙️  Ville: {profile.get('city', '---')}")
    print(f"📮 Code Postal: {profile.get('zip', '---')}")
    print(f"🌍 Pays: {profile.get('country', '---')}")
    print(f"🎂 Date de naissance: {profile.get('date_of_birth', '---')}")

def main():
    parser = argparse.ArgumentParser(
        description="Remplissage automatique de formulaires web",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python autofill_cli.py
  python autofill_cli.py --profile profile1 --url https://example.com
  python autofill_cli.py --list
        """
    )
    
    parser.add_argument('--profile', type=str, help='ID du profil à utiliser (profile1, profile2, profile3)')
    parser.add_argument('--url', type=str, help='URL du site à visiter')
    parser.add_argument('--list', action='store_true', help='Afficher la liste des profils disponibles')
    parser.add_argument('--detect-only', action='store_true', help='Seulement détecter les champs sans les remplir')
    
    args = parser.parse_args()
    
    # Afficher la liste des profils si demandé
    if args.list:
        print_profiles()
        return
    
    # Logo et bienvenue
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║          🤖 FORM AUTOFILL - Remplissage Automatique              ║")
    print("║                  Version 5.0 avec Support Profils                ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Sélectionner le profil
    if args.profile and args.profile in GENERIC_PROFILES:
        profile_id = args.profile
        print(f"\n✅ Profil sélectionné: {profile_id}")
    else:
        if args.profile:
            print(f"\n⚠️  Profil '{args.profile}' non trouvé!")
        print_profiles()
        profile_id = get_profile_interactive()
    
    # Afficher les infos du profil
    display_profile_info(profile_id)
    profile_data = GENERIC_PROFILES[profile_id]
    
    # Récupérer l'URL
    if args.url:
        url = args.url
    else:
        print_header("🌐 SAISIE DE L'URL")
        url = input("Entrez l'URL du site à visiter: ").strip()
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Afficher le résumé
    print_header("📋 RÉSUMÉ DE LA SESSION")
    print(f"🎯 Profil: {profile_id}")
    print(f"🌐 URL: {url}")
    print(f"👤 Nom: {profile_data.get('first_name')} {profile_data.get('last_name')}")
    print(f"📧 Email: {profile_data.get('email')}")
    
    # Demander confirmation
    confirm = input("\n✅ Procéder avec cette configuration? (oui/non): ").strip().lower()
    if confirm not in ['oui', 'yes', 'o', 'y']:
        print("❌ Opération annulée.")
        return
    
    # Lancer la session
    print_header("🚀 DÉMARRAGE DE LA SESSION")
    
    try:
        print(f"📌 Création du driver Edge...")
        driver = create_driver()
        
        print(f"📌 Navigation vers: {url}")
        driver.get(url)
        time.sleep(3)
        
        print(f"✅ Page chargée: {driver.title}")
        
        # Détecter les champs
        print_header("🔍 DÉTECTION DES CHAMPS")
        detected = detect_fields(driver, use_levenshtein=True, threshold=0.5)
        
        if args.detect_only:
            print("\n✅ Détection terminée. (Mode détection seulement)")
            input("\nAppuyez sur Entrée pour fermer le navigateur...")
            driver.quit()
            return
        
        # Remplir les formulaires
        print_header("📝 REMPLISSAGE DES FORMULAIRES")
        filled = fill_forms(driver, provided_values=profile_data, use_levenshtein=True, threshold=0.5)
        
        print_header("✅ RÉSUMÉ DU REMPLISSAGE")
        print(f"📊 Champs détectés: {len(detected)}")
        print(f"✏️  Champs remplis: {len(filled)}")
        
        if filled:
            print("\n📋 Champs remplis:")
            for field in filled[:10]:  # Afficher les 10 premiers
                print(f"  • {field['name']}: {field['value']}")
            if len(filled) > 10:
                print(f"  ... et {len(filled) - 10} autres")
        
        print("\n" + "=" * 70)
        print("  ✅ REMPLISSAGE TERMINÉ")
        print("  Vous pouvez maintenant vérifier/soumettre le formulaire")
        print("=" * 70)
        
        # Garder le navigateur ouvert
        input("\n🛑 Appuyez sur Entrée pour fermer le navigateur et terminer...")
        driver.quit()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        try:
            driver.quit()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
