"""
Script de test pour l'API Form Autofill - Recherche Google
===========================================================

VERSION GOOGLE SEARCH:
- ✅ Ouvre Google automatiquement
- ✅ Permet des recherches normales
- ✅ Détecte les formulaires sur les pages cliquées
- ✅ Remplit automatiquement SANS changer de page
- ✅ Interface esthétique pour choisir le profil

Usage:
    python test_recherche_google.py
"""
import requests
import time
import sys
import json
import tkinter as tk
from tkinter import messagebox

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

def show_profile_picker_gui():
    """Interface graphique esthétique et professionnelle pour choisir le profil"""
    root = tk.Tk()
    root.title("Form Autofill - Profile Selector")
    root.geometry("800x550")
    root.configure(bg='#ffffff')
    root.resizable(False, False)
    
    # Style général
    root.option_add('*Font', ('Segoe UI', 11))
    
    selected_profile = [None]
    
    def select_profile(profile_id):
        selected_profile[0] = profile_id
        root.quit()
        root.destroy()
    
    # ===== HEADER =====
    header_frame = tk.Frame(root, bg='#1a1a2e', height=120)
    header_frame.pack(fill=tk.X, padx=0, pady=0)
    header_frame.pack_propagate(False)
    
    # Logo/Title
    title_label = tk.Label(
        header_frame,
        text="📋 Sélectionnez votre profil",
        font=('Segoe UI', 28, 'bold'),
        bg='#1a1a2e',
        fg='#ffffff'
    )
    title_label.pack(pady=25)
    
    subtitle_label = tk.Label(
        header_frame,
        text="Choisissez le profil à utiliser pour le remplissage automatique",
        font=('Segoe UI', 11),
        bg='#1a1a2e',
        fg='#b0b0b0'
    )
    subtitle_label.pack(pady=(0, 15))
    
    # ===== CONTENT FRAME =====
    content_frame = tk.Frame(root, bg='#ffffff')
    content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=35)
    
    # Profile info data
    profiles_info = {
        'profile1': {
            'name': 'Voyageur Standard',
            'emoji': '✈️',
            'desc': 'Jean Dupont',
            'extra': 'Voyageur régulier • Europe',
            'color': '#3498db',
            'dark_color': '#2980b9'
        },
        'profile2': {
            'name': 'Client Affaires',
            'emoji': '💼',
            'desc': 'Marie Martin',
            'extra': 'Professionnel • France',
            'color': '#e74c3c',
            'dark_color': '#c0392b'
        },
        'profile3': {
            'name': 'Touriste International',
            'emoji': '🌍',
            'desc': 'Anna Schmidt',
            'extra': 'Explorateur • Monde',
            'color': '#27ae60',
            'dark_color': '#229954'
        },
    }
    
    def create_profile_button(parent, profile_id, info):
        """Crée un bouton profil stylisé avec effet de survol"""
        
        # Container pour le bouton
        btn_container = tk.Frame(parent, bg='#ffffff')
        btn_container.pack(fill=tk.X, pady=12)
        
        # Frame du bouton avec couleur
        btn_frame = tk.Frame(
            btn_container,
            bg=info['color'],
            highlightthickness=0,
            relief=tk.FLAT,
            height=90
        )
        btn_frame.pack(fill=tk.BOTH, expand=True)
        btn_frame.pack_propagate(False)
        
        # État du bouton
        button_state = {'hover': False}
        
        def on_enter(e):
            button_state['hover'] = True
            btn_frame.config(bg=info['dark_color'])
            # Ajouter un léger effet d'élévation
            inner_frame.config(bg=info['dark_color'])
        
        def on_leave(e):
            button_state['hover'] = False
            btn_frame.config(bg=info['color'])
            inner_frame.config(bg=info['color'])
        
        def on_click(e):
            select_profile(profile_id)
        
        # Frame interne pour le padding
        inner_frame = tk.Frame(
            btn_frame,
            bg=info['color'],
            highlightthickness=0
        )
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Gauche: Emoji + Infos
        left_frame = tk.Frame(inner_frame, bg=info['color'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Emoji
        emoji_label = tk.Label(
            left_frame,
            text=info['emoji'],
            font=('Segoe UI', 32),
            bg=info['color'],
            fg='#ffffff'
        )
        emoji_label.pack(side=tk.LEFT, padx=(0, 20), pady=0)
        
        # Texte (nom + description)
        text_frame = tk.Frame(left_frame, bg=info['color'])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        name_label = tk.Label(
            text_frame,
            text=info['name'],
            font=('Segoe UI', 16, 'bold'),
            bg=info['color'],
            fg='#ffffff',
            justify=tk.LEFT
        )
        name_label.pack(anchor=tk.W)
        
        desc_label = tk.Label(
            text_frame,
            text=info['desc'],
            font=('Segoe UI', 12),
            bg=info['color'],
            fg='#ffffff',
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W, pady=(2, 0))
        
        extra_label = tk.Label(
            text_frame,
            text=info['extra'],
            font=('Segoe UI', 10),
            bg=info['color'],
            fg='#e0e0e0',
            justify=tk.LEFT
        )
        extra_label.pack(anchor=tk.W, pady=(4, 0))
        
        # Droite: Flèche
        arrow_label = tk.Label(
            inner_frame,
            text="→",
            font=('Segoe UI', 24, 'bold'),
            bg=info['color'],
            fg='#ffffff'
        )
        arrow_label.pack(side=tk.RIGHT, padx=(20, 0))
        
        # Bind events
        for widget in [btn_frame, inner_frame, left_frame, text_frame, 
                      emoji_label, name_label, desc_label, extra_label, arrow_label]:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
            widget.bind('<Button-1>', on_click)
        
        # Make cursor change on hover
        btn_frame.bind('<Enter>', lambda e: root.config(cursor='hand2'))
        btn_frame.bind('<Leave>', lambda e: root.config(cursor='arrow'))
        
        # Cursor pour tous les widgets
        for widget in [inner_frame, left_frame, text_frame, 
                      emoji_label, name_label, desc_label, extra_label, arrow_label]:
            widget.bind('<Enter>', lambda e: root.config(cursor='hand2'))
            widget.bind('<Leave>', lambda e: root.config(cursor='arrow'))
    
    # Créer les boutons de profil
    for profile_id, info in profiles_info.items():
        create_profile_button(content_frame, profile_id, info)
    
    # ===== FOOTER =====
    footer_frame = tk.Frame(root, bg='#f8f8f8', height=50)
    footer_frame.pack(fill=tk.X, padx=0, pady=0)
    footer_frame.pack_propagate(False)
    
    footer_label = tk.Label(
        footer_frame,
        text="💡 Sélectionnez un profil pour démarrer le remplissage automatique",
        font=('Segoe UI', 10),
        bg='#f8f8f8',
        fg='#7f8c8d'
    )
    footer_label.pack(pady=12)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()
    
    return selected_profile[0]

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
    """Demande le choix du profil via GUI esthétique"""
    profile_id = show_profile_picker_gui()
    if profile_id:
        return profile_id
    else:
        print("❌ Aucun profil sélectionné")
        return None

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
    """Exécute le monitoring CONTINU avec Google Search"""
    
    print()
    print("=" * 70)
    print(f"🔗 Page initiale: {url}")
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
    print("   • Vous pouvez faire des recherches normales")
    print("   • Au clic sur une URL: détection du formulaire")
    print("   • Si formulaire trouvé: REMPLISSAGE AUTOMATIQUE")
    print("   • SANS CHANGER DE PAGE - vous restez sur la page")
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
                time.sleep(2)  # Attendre le chargement
            
            # Vérifier si cette URL a déjà été remplie
            if current_url in filled_urls:
                if current_url == last_filled_url:
                    # Même URL, même formulaire - éviter la boucle infinie
                    no_form_count += 1
                    if no_form_count >= max_no_form_attempts:
                        print(f"\n⏸️  Trop de tentatives sur la même page")
                        print(f"   URL: {current_url}")
                        print(f"   (Continuez votre navigation)")
                        time.sleep(2)
                        continue
                else:
                    # URL différente mais déjà traitée
                    print(f"\n✅ Cette page a déjà été remplie")
                    print(f"   (Continuez votre navigation)")
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
                print(f"\n✅ Formulaire #{form_number-1} rempli automatiquement")
                print(f"⏳ Vous restez sur la même page")
                print(f"   (Continuez votre navigation ou appuyez sur Ctrl+C)")
                time.sleep(3)  # Attendre avant la prochaine tentative
            else:
                # Aucun formulaire trouvé
                no_form_count += 1
                if no_form_count == 1:
                    print(f"\n⏳ Aucun formulaire détecté sur cette page")
                    print(f"   Naviguez vers une autre page...")
                
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
    """Fonction principale - Lance la recherche Google avec formulaire autofill"""
    print_header()
    
    # URL de Google (toujours la même)
    google_url = "https://www.google.com"
    
    print(f"🌐 Ouverture de Google...")
    
    # Mode interactif - Afficher le sélecteur de profil
    print("\n📋 Sélection du profil...")
    
    profile_id = ask_for_profile()
    if not profile_id:
        print("\n👋 Au revoir!")
        return
    
    # Exécuter le test avec Google
    run_test(google_url, profile_id, threshold=0.5)

if __name__ == "__main__":
    main()
