
"""
API Form Autofill - Version 5.0 (Corrections Basic-Fit)
=======================================================

CORRECTIONS v5 :
- ✅ Basic-Fit : Champs d'adresse séparés (rue ≠ numéro ≠ complément ≠ ville)
- ✅ Basic-Fit : Radio genre avec détection par label (Homme/Femme/Autre)
- ✅ Basic-Fit : Checkboxes communication avec détection par texte
- ✅ Meilleure priorité : nom exact > Levenshtein
- ✅ Détection par texte du label parent

Distance de Levenshtein : OUI, utilisée pour la détection flexible des champs.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import time
import os
import Levenshtein
import re

# ===============================================
# 📅 FONCTIONS DE DATE
# ===============================================

def parse_date_components(date_str):
    """
    Parse une date en formats YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY, DD-MM-YYYY
    Retourne jour, mois, année au format YYYY-MM-DD
    Exemple: '1990-01-15' -> {'day': '15', 'month': '01', 'year': '1990'}
    """
    try:
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Essayer YYYY-MM-DD ou YYYY/MM/DD
        if '-' in date_str:
            parts = date_str.split('-')
        elif '/' in date_str:
            parts = date_str.split('/')
        else:
            return None
        
        if len(parts) != 3:
            return None
        
        # Déterminer le format
        # Si le premier élément a 4 chiffres, c'est YYYY-MM-DD ou YYYY/MM/DD
        if len(parts[0]) == 4:
            year, month, day = parts[0], parts[1], parts[2]
        # Si le dernier élément a 4 chiffres, c'est DD-MM-YYYY ou DD/MM/YYYY
        elif len(parts[2]) == 4:
            day, month, year = parts[0], parts[1], parts[2]
        else:
            # Format ambigu - assumer YYYY-MM-DD
            year, month, day = parts[0], parts[1], parts[2]
        
        # Formater avec padding zéro
        year = str(year).zfill(4)
        month = str(month).zfill(2)
        day = str(day).zfill(2)
        
        return {
            'day': day,
            'month': month,
            'year': year
        }
    except Exception:
        pass
    
    return None


def normalize_date_to_iso(date_str):
    """
    Convertit une date en format ISO 8601 (YYYY-MM-DD)
    Accepte: YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY, DD-MM-YYYY
    """
    if not date_str:
        return None
    
    parts = parse_date_components(str(date_str))
    if parts:
        return f"{parts['year']}-{parts['month']}-{parts['day']}"
    
    return None


def is_date_field(field_name):
    """Vérifie si un champ est un champ de date"""
    if not field_name:
        return False
    name_lower = field_name.lower()
    date_keywords = ['date', 'birth', 'birthdate', 'dob', 'jour', 'mois', 'annee', 'year', 'month', 'day', 'departure', 'return', 'depart', 'retour']
    return any(kw in name_lower for kw in date_keywords)


def is_day_field(field_name):
    """Vérifie si c'est un champ jour"""
    if not field_name:
        return False
    name_lower = field_name.lower()
    return any(kw in name_lower for kw in ['jour', 'day', 'dd', 'jour_naissance'])


def is_month_field(field_name):
    """Vérifie si c'est un champ mois"""
    if not field_name:
        return False
    name_lower = field_name.lower()
    return any(kw in name_lower for kw in ['mois', 'month', 'mm', 'mois_naissance'])


def is_year_field(field_name):
    """Vérifie si c'est un champ année"""
    if not field_name:
        return False
    name_lower = field_name.lower()
    return any(kw in name_lower for kw in ['annee', 'year', 'yyyy', 'yy', 'annee_naissance', 'année'])


def is_date_text_field(field_name):
    """Vérifie si c'est un champ texte de date (departure-date, return-date, etc)"""
    if not field_name:
        return False
    name_lower = field_name.lower()
    date_patterns = ['departure', 'return', 'depart', 'retour', 'outbound', 'inbound']
    return any(pattern in name_lower for pattern in date_patterns)


# ===============================================
# �🔧 CONFIGURATION
# ===============================================

app = FastAPI(
    title="Form Autofill API v5",
    version="5.0.0",
    description="API avec corrections Basic-Fit"
)

active_sessions: Dict[str, Any] = {}
DRIVER_PATH = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")

# ===============================================
# 📚 MAPPING DES CHAMPS - PLUS PRÉCIS
# ===============================================

# Mots-clés pour détecter les types de champs
FIELD_KEYWORDS = {
    # Identité
    'first_name': ['firstname', 'first_name', 'prenom', 'prénom', 'given', 'fname', 'vorname'],
    'last_name': ['lastname', 'last_name', 'nom', 'surname', 'family', 'lname', 'nachname'],
    'full_name': ['fullname', 'full_name', 'name', 'custname'],
    'gender': ['gender', 'sexe', 'sex', 'genre'],
    'title': ['title', 'civilité', 'civility', 'salutation'],
    
    # Contact
    'email': ['email', 'mail', 'courriel', 'e-mail'],
    'email_confirm': ['confirm', 'confirmez', 'verify', 'email2', 'emailconfirm'],
    'phone': ['phone', 'tel', 'telephone', 'mobile', 'gsm', 'portable'],
    
    # Adresse - SÉPARÉS pour Basic-Fit
    'zip': ['zip', 'postal', 'postcode', 'plz', 'code_postal', 'codepostal','zipcode'],
    'street_number': ['numero', 'numéro', 'number', 'housenumber', 'streetnumber', 'no'],
    'street': ['rue', 'street', 'strasse', 'adresse', 'address'],
    'street_extra': ['complement', 'complément', 'extra', 'additional', 'zusatz', 'optionnel'],
    'city': ['city', 'ville', 'Ville', 'town', 'stadt', 'ort', 'locality'],
    'country': ['country', 'pays', 'land', 'nation'],

      
    # === DOCUMENTS ===
    'passport': ['passport', 'passeport', 'passport_number', 'passport_no'],
    
    # === DATES ===
    'date_of_birth': ['birthdate', 'dob', 'date_of_birth', 'dateofbirth', 'date_naissance','Anniversaire'],
    'birth_day': ['day', 'jour', 'tag', 'birth_day', 'birthdate_day', 'day_of_birth'],
    'birth_month': ['month', 'mois', 'monat', 'birth_month', 'birthdate_month', 'month_of_birth'],
    'birth_year': ['year', 'année', 'an', 'jahr', 'birth_year', 'birthdate_year', 'year_of_birth'],
    'departure_date': ['departure', 'depart', 'outbound', 'aller', 'date_depart'],
    'return_date': ['return', 'retour', 'inbound', 'date_retour'],
    'arrival_time': ['arrival', 'arrivee', 'heure_arrivee', 'checkin', 'check-in'],
    
    # Auth
    'password': ['password', 'pwd', 'pass', 'mot_de_passe', 'mdp'],
    'password_confirm': ['confirm_password', 'password_confirm', 'repeat', 'password2'],

     # === AUTHENTIFICATION ===
    'username': ['username', 'user', 'login', 'identifiant', 'pseudo', 'nickname'],
    'password': ['password', 'pwd', 'pass', 'mot_de_passe', 'mdp', 'secret'],
    'confirm_password': ['confirm', 'confirm_password', 'password_confirm', 'repeat_password'],
    
    # Options
    'remember': ['remember', 'souvenir', 'stay', 'keep', 'rester'],
    'newsletter': ['newsletter', 'news', 'offres', 'promo', 'marketing'],
    'terms': ['terms', 'conditions', 'cgu', 'accept', 'agree', 'consent'],
    'loyalty': ['loyalty', 'fidel', 'programme', 'rewards'],
    
    # Communication Basic-Fit
    'partner_promo': ['partenaire', 'partner', 'tiers', 'third'],
    'data_consent': ['assistance', 'profil', 'données', 'data', 'contacter', 'contact'],
    
    # === OPTIONS BOOKING ===
    'booking_for': ['booking_for', 'reserve_for', 'pour_qui', 'who_booking', 'client_type'],
    'work_travel': ['work', 'business', 'travail', 'professionnel', 'work_travel'],
    'car_rental': ['car', 'voiture', 'location', 'rental', 'vehicle'],
    'airport_transfer': ['transfer', 'transfert', 'navette', 'shuttle', 'airport'],

    # CGU / Terms (pour Domino's)
    'terms': ['terms', 'conditions', 'cgu', 'accept', 'agree', 'consent', 'checking', 'acknowledge', 'personal_data', 'terms_of_use', 'notice'],
    
    # Booking - Work travel
    'work_travel': ['work', 'business', 'travail', 'travelling_for_work', 'traveling_for_work', 'professionnel'],
    
    # Booking - Options
    'shuttle': ['shuttle', 'navette', 'airport_shuttle', 'transfer', 'transfert'],
    'car_rental': ['car', 'rental', 'voiture', 'location', 'rental_car', 'renting'],
    'insurance': ['insurance', 'assurance', 'cancellation', 'annulation'],
    
    # Booking - Arrival
    'arrival_time': ['arrival', 'arrivee', 'estimated', 'check-in', 'checkin', 'time'],
    
    # === OPTIONS GÉNÉRALES ===
    'remember_me': ['remember', 'souvenir', 'stay_logged', 'keep_logged', 'rester_connecte'],
    'newsletter': ['newsletter', 'news', 'subscribe', 'inscription', 'abonnement'],
    'terms': ['terms', 'conditions', 'cgu', 'accept', 'agree', 'consent'],
    'privacy': ['privacy', 'confidentialite', 'rgpd', 'gdpr', 'donnees'],
    
    # === PIZZA (httpbin) ===
    'size': ['size', 'taille', 'pizza_size', 'format'],
    'topping': ['topping', 'garniture', 'ingredient', 'extra'],
    'comments': ['comments', 'comment', 'remarque', 'note', 'message', 'textarea'],
    # Pizza / Livraison
    'delivery': ['delivery', 'livraison', 'heure', 'time', 'horaire'],
}


# ===============================================
# 👥 PROFILS GÉNÉRIQUES PAR DÉFAUT
# ===============================================
GENERIC_PROFILES = {
    'profile1': {
        'name': 'Profil 1 - Voyageur Standard',
        'first_name': 'Jean',
        'last_name': 'Dupont',
        'full_name': 'Jean Dupont',
        'title': 'Mr',
        'gender': 'Male',
        'email': 'jean.dupont@example.com',
        'phone': '+33612345678',
        'address': '15 Rue de la Paix',
        'street': 'Rue de la Paix',
        'numero': '15',
        'city': 'Paris',
        'zip': '75001',
        'country': 'France',
        'state': 'Île-de-France',
        'date_of_birth': '1990-01-15',
        'birth_day': '15',
        'birth_month': '01',
        'birth_year': '1990',
        'username': 'jean.dupont',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
    },
    
    'profile2': {
        'name': 'Profil 2 - Client Affaires',
        'first_name': 'Marie',
        'last_name': 'Martin',
        'full_name': 'Marie Martin',
        'title': 'Ms',
        'gender': 'Female',
        'email': 'marie.martin@example.com',
        'phone': '+33687654321',
        'address': '42 Avenue des Champs',
        'street': 'Avenue des Champs',
        'numero': '42',
        'city': 'Lyon',
        'zip': '69000',
        'passport': 'AB1234567',
        'country': 'France',
        'state': 'Auvergne-Rhône-Alpes',
        'date_of_birth': '1985-06-22',
        'birth_day': '22',
        'birth_month': '06',
        'birth_year': '1985',
        'username': 'marie.martin',
        'password': 'ProPass456!',
        'confirm_password': 'ProPass456!',
    },
    
    'profile3': {
        'name': 'Profil 3 - Touriste International',
        'first_name': 'Anna',
        'last_name': 'Schmidt',
        'full_name': 'Anna Schmidt',
        'title': 'Ms',
        'gender': 'Female',
        'email': 'anna.schmidt@gmail.com',
        'phone': '+49301234567',
        'address': '8 Boulevard Saint-Germain',
        'street': 'Boulevard Saint-Germain',
        'numero': '8',
        'city': 'Paris',
        'zip': '75005',
        'country': 'Germany',
        'state': 'Berlin',
        'date_of_birth': '1992-03-10',
        'birth_day': '10',
        'birth_month': '03',
        'birth_year': '1992',
        'username': 'anna.schmidt',
        'password': 'Travel789!@',
        'confirm_password': 'Travel789!@',
    },
}


# Synonymes pour les radios (genre, yes/no)
RADIO_VALUES = {
    # Genre
    'homme': ['homme', 'male', 'man', 'm', 'masculin', 'herr', 'männlich'],
    'femme': ['femme', 'female', 'woman', 'f', 'féminin', 'frau', 'weiblich'],
    'autre': ['autre', 'other', 'divers', 'non-binary', 'nonbinary'],
    
    # Yes/No
    'oui': ['oui', 'yes', 'true', '1', 'on', 'ja', 'si'],
    'non': ['non', 'no', 'false', '0', 'off', 'nein'],
    'yes': ['yes', 'oui', 'true', '1', 'on'],  # Ajout
    'no': ['no', 'non', 'false', '0', 'off'],   # Ajout
}

# ===============================================
# 📋 MODÈLES PYDANTIC
# ===============================================

class SessionCreateRequest(BaseModel):
    session_id: str
    url: Optional[str] = ''
    maximize: Optional[bool] = True


class FillFormRequest(BaseModel):
    session_id: str
    values: Optional[Dict[str, Any]] = {}
    use_levenshtein: Optional[bool] = True
    levenshtein_threshold: Optional[float] = 0.5
    form_id: Optional[str] = None  # NOUVEAU: formulaire cible


class DetectFieldsRequest(BaseModel):
    session_id: str
    use_levenshtein: Optional[bool] = True
    levenshtein_threshold: Optional[float] = 0.5


class SessionResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


class FormFillResponse(BaseModel):
    success: bool
    message: str
    filled_fields: Optional[list] = []


class DetectFieldsResponse(BaseModel):
    success: bool
    message: str
    fields: Optional[list] = []
    total: Optional[int] = 0


# ===============================================
# 🔍 FONCTIONS DE DÉTECTION
# ===============================================

def get_value_with_fallback(detected_field_type: str, values_lower: dict) -> Optional[Any]:
    """
    Récupère la valeur du profil pour un type de champ détecté.
    Supporte les fallbacks intelligents (ex: email_confirm → email)
    """
    # Première tentative: la clé exacte du type détecté
    if detected_field_type in values_lower:
        return values_lower[detected_field_type]
    
    # Fallbacks intelligents
    fallbacks = {
        'email_confirm': ['email'],  # Si email_confirm pas trouvé, utiliser email
        'confirm_password': ['password'],  # Si confirm_password pas trouvé, utiliser password
        'password_confirm': ['password'],
        'password2': ['password'],
        'birth_day': ['date_of_birth'],
        'birth_month': ['date_of_birth'],
        'birth_year': ['date_of_birth'],
    }
    
    if detected_field_type in fallbacks:
        for fallback_key in fallbacks[detected_field_type]:
            if fallback_key in values_lower:
                return values_lower[fallback_key]
    
    return None
    """
    Détecte le type de champ en utilisant Levenshtein.
    Retourne le type de champ ou None.
    
    Stratégie:
    1. Chercher si le type de champ lui-même est dans le nom
    2. Chercher les matchs exacts (substring) de mots-clés
    3. Favoriser les mots-clés plus longs (pour éviter les faux positifs)
    4. Utiliser Levenshtein comme fallback
    """
    if not field_name:
        return None
    
    name_lower = field_name.lower().replace('-', '_').replace(' ', '_')
    best_type = None
    best_score = 0.0
    best_match_length = 0  # Longueur du mot-clé matché
    
    for field_type, keywords in FIELD_KEYWORDS.items():
        type_name = field_type.lower()
        type_best_score = 0.0
        type_match_length = 0
        
        # BONUS: Si le type de champ lui-même est dans le nom du champ
        if type_name in name_lower:
            type_best_score = 0.99
            type_match_length = len(type_name)
        else:
            # Chercher les mots-clés, en privilégiant les plus longs
            # Trier les mots-clés par longueur décroissante
            sorted_keywords = sorted(keywords, key=len, reverse=True)
            
            for kw in sorted_keywords:
                if kw in name_lower:
                    # Score basé sur la longueur du mot-clé (plus long = plus spécifique)
                    score = 0.85 + min(0.14, len(kw) / 100.0)
                    if len(kw) > type_match_length:
                        type_best_score = score
                        type_match_length = len(kw)
                else:
                    # Sinon utiliser Levenshtein uniquement pour les courtes distances
                    score = Levenshtein.ratio(name_lower, kw)
                    if score > type_best_score and score >= 0.8:  # Au moins 80% de similarité
                        type_best_score = score
                        type_match_length = len(kw)
        
        # Comparer avec le meilleur trouvé:
        # 1. Priorité à la longueur du match (plus long = plus spécifique)
        # 2. Puis au score
        should_update = False
        
        if type_match_length > best_match_length:
            should_update = True
        elif type_match_length == best_match_length and type_best_score > best_score:
            should_update = True
        
        if should_update:
            best_score = type_best_score
            best_type = field_type
            best_match_length = type_match_length
    
    return best_type if best_score >= threshold else None


def get_element_label(element, driver) -> str:
    """Récupère le texte du label associé à un élément"""
    label_text = ""
    
    try:
        # Par l'attribut for
        elem_id = element.get_attribute('id')
        if elem_id:
            try:
                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{elem_id}']")
                label_text = label.text.lower()
            except:
                pass
        
        # Par le label parent
        if not label_text:
            try:
                parent = element.find_element(By.XPATH, "./ancestor::label")
                label_text = parent.text.lower()
            except:
                pass
        
        # Par le texte du parent direct
        if not label_text:
            try:
                parent = element.find_element(By.XPATH, "./..")
                text = parent.text.lower()
                if len(text) < 200:
                    label_text = text
            except:
                pass
    except:
        pass
    
    return label_text


def match_radio_value(target: str, input_value: str, label_text: str = "") -> bool:
    """
    Vérifie si une valeur de radio correspond à la cible.
    Utilise les synonymes pour matcher.
    """
    target_lower = str(target).lower().strip()
    input_lower = str(input_value).lower().strip()
    label_lower = label_text.lower() if label_text else ""
    
    # Match exact
    if target_lower == input_lower:
        return True
    
    # Chercher dans les synonymes
    for key, synonyms in RADIO_VALUES.items():
        if target_lower in synonyms or target_lower == key:
            # Vérifier si input ou label contient un synonyme
            for syn in synonyms:
                if syn == input_lower or syn in input_lower:
                    return True
                if syn in label_lower:
                    return True
    
    # Match partiel
    if target_lower in input_lower or input_lower in target_lower:
        return True
    if target_lower in label_lower:
        return True
    
    return False


def should_check_checkbox(element, provided_values: Dict, driver) -> tuple:
    """
    Détermine si une checkbox doit être cochée.
    Retourne (should_check: bool, matched_key: str)
    """
    input_value = (element.get_attribute('value') or '').lower()
    input_name = (element.get_attribute('name') or '').lower()
    input_id = (element.get_attribute('id') or '').lower()
    label_text = get_element_label(element, driver)
    
    # 1. Chercher par nom/id/value exact dans provided_values
    for key in [input_name, input_id, input_value]:
        if key and key in provided_values:
            val = provided_values[key]
            if isinstance(val, bool):
                return (val, key)
            if isinstance(val, str) and val.lower() in ['yes', 'true', 'on', '1', 'oui']:
                return (True, key)
    
    # 2. Chercher par type de champ détecté
    field_type = get_field_type(input_name or input_id)
    if field_type and field_type in provided_values:
        val = provided_values[field_type]
        if isinstance(val, bool):
            return (val, field_type)
    
    # 3. Chercher dans le label (pour Basic-Fit communication)
    if label_text:
        # Partenaires
        if any(kw in label_text for kw in ['partenaire', 'partner', 'promotions']):
            for key in ['partner_promo', 'partenaires', 'partner', 'promotions']:
                if key in provided_values:
                    val = provided_values[key]
                    if isinstance(val, bool):
                        return (val, key)
        
        # Assistance/Profil
        if any(kw in label_text for kw in ['assistance', 'profil', 'contacter', 'données']):
            for key in ['data_consent', 'assistance', 'profil', 'communication', 'contact']:
                if key in provided_values:
                    val = provided_values[key]
                    if isinstance(val, bool):
                        return (val, key)
        
        # Fidélité
        if any(kw in label_text for kw in ['fidélité', 'fidelite', 'programme']):
            for key in ['loyalty', 'fidelite', 'fidélité']:
                if key in provided_values:
                    val = provided_values[key]
                    if isinstance(val, bool):
                        return (val, key)
        
        # Newsletter
        if any(kw in label_text for kw in ['newsletter', 'offres', 'informations', 'email']):
            if 'newsletter' in provided_values:
                val = provided_values['newsletter']
                if isinstance(val, bool):
                    return (val, 'newsletter')
        
        # CGU
        # CGU / Terms of Use (Domino's)
        if any(kw in label_text for kw in ['terms', 'conditions', 'accept', 'acknowledge', 'checking', 'personal data', 'notice']):
            for key in ['terms', 'accept', 'terms_of_use', 'personal_data', 'checking']:
                if key in provided_values:
                    val = provided_values[key]
                    if isinstance(val, bool):
                        return (val, key)
        
        # Shuttle / Transfer (Booking)
        if any(kw in label_text for kw in ['shuttle', 'transfer', 'navette', 'airport']):
            for key in ['shuttle', 'airport_shuttle', 'transfer']:
                if key in provided_values:
                    val = provided_values[key]
                    if isinstance(val, bool):
                        return (val, key)
        
        # Car rental (Booking)
        if any(kw in label_text for kw in ['car', 'rental', 'voiture', 'renting']):
            for key in ['car_rental', 'rental_car']:
                if key in provided_values:
                    val = provided_values[key]
                    if isinstance(val, bool):
                        return (val, key)
        
        # Insurance (Booking)
        if any(kw in label_text for kw in ['insurance', 'assurance', 'cancellation']):
            for key in ['insurance', 'cancellation', 'room_insurance']:
                if key in provided_values:
                    val = provided_values[key]
                    if isinstance(val, bool):
                        return (val, key)
    
    # 4. Checkbox dans une liste (pizza toppings)
    for key, val in provided_values.items():
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str) and item.lower() == input_value:
                    return (True, key)
    
    return (False, None)


# ===============================================
# 🌐 DRIVER SELENIUM
# ===============================================

def create_driver():
    service = Service(DRIVER_PATH)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Edge(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


# ===============================================
# � FONCTION DE DÉTECTION DES CHAMPS
# ===============================================

def get_form_id_for_element(driver, element):
    """
    Retourne un form_id unique pour l'élément.
    Cherche le formulaire parent ou génère un ID basé sur la position
    """
    try:
        # Chercher le formulaire parent
        form = element.find_element(By.XPATH, "ancestor::form[1]")
        form_id = form.get_attribute('id')
        if form_id:
            return form_id
        form_name = form.get_attribute('name')
        if form_name:
            return form_name
        # Si pas d'ID/name, utiliser l'index du formulaire
        form_index = driver.execute_script("""
            return Array.from(document.querySelectorAll('form')).indexOf(arguments[0])
        """, form)
        return f"form_{form_index}"
    except:
        # Pas de formulaire parent - chercher si c'est dans un fieldset/div conteneur
        try:
            container = element.find_element(By.XPATH, "ancestor::fieldset[1]")
            container_id = container.get_attribute('id')
            if container_id:
                return f"fieldset_{container_id}"
        except:
            pass
        
        # Pas de conteneur - retourner "standalone_form"
        return "standalone_form"


def detect_field_type_improved(field_id: str, use_levenshtein: bool = True, threshold: float = 0.5) -> List[Dict]:
    """
    Détecte le type de champ de manière améliorée.
    
    Stratégie:
    1. EXACT: Cherche correspondance exacte dans les mots-clés
    2. SUBSTRING: Cherche si un mot-clé est substring du field_id
    3. WORD MATCHING: Cherche si les mots du field_id matchent les mots-clés
    4. LEVENSHTEIN: Distance Levenshtein si seuil atteint
    """
    
    suggestions = []
    field_id_lower = field_id.lower()
    field_id_words = [w for w in field_id_lower.replace('_', ' ').replace('-', ' ').split() if w]
    
    for keyword_type, keywords in FIELD_KEYWORDS.items():
        best_score = 0.0
        best_method = "NONE"
        best_keyword = ""
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            keyword_words = [w for w in keyword_lower.replace('_', ' ').replace('-', ' ').split() if w]
            
            # 1. EXACT MATCH
            if field_id_lower == keyword_lower:
                best_score = 1.0
                best_method = "EXACT"
                best_keyword = keyword
                break
            
            # 2. SUBSTRING MATCH (keyword dans field_id)
            if keyword_lower in field_id_lower:
                score = 1.0 - (len(keyword_lower) / len(field_id_lower)) * 0.1  # Pénalité légère
                if score > best_score:
                    best_score = score
                    best_method = "SUBSTRING"
                    best_keyword = keyword
            
            # 3. WORD MATCHING (tous les mots du keyword dans field_id_words)
            words_matched = sum(1 for kw in keyword_words if any(kw in fw for fw in field_id_words))
            if keyword_words and words_matched > 0:
                word_score = words_matched / len(keyword_words)
                if word_score > best_score:
                    best_score = word_score
                    best_method = "WORD_MATCH"
                    best_keyword = keyword
            
            # 4. LEVENSHTEIN
            if use_levenshtein:
                lev_score = 1 - (Levenshtein.distance(field_id_lower, keyword_lower) / max(len(field_id_lower), len(keyword_lower)))
                if lev_score > best_score and lev_score >= threshold:
                    best_score = lev_score
                    best_method = "LEVENSHTEIN"
                    best_keyword = keyword
        
        # Ajouter si score >= threshold
        if best_score >= threshold:
            suggestions.append({
                'field_type': keyword_type,
                'keyword': best_keyword,
                'score': round(best_score, 2),
                'method': best_method
            })
    
    return sorted(suggestions, key=lambda x: x['score'], reverse=True)


def detect_fields(driver, use_levenshtein: bool = True, threshold: float = 0.5) -> List[Dict]:
    """
    Détecte tous les champs du formulaire et retourne une liste groupée par form_id.
    Format: {form_id: [fields]}
    """
    
    detected_fields_by_form = {}  # {form_id: [fields]}
    
    all_inputs = driver.find_elements(By.TAG_NAME, 'input')
    all_textareas = driver.find_elements(By.TAG_NAME, 'textarea')
    all_selects = driver.find_elements(By.TAG_NAME, 'select')
    
    print(f'\n🔍 DÉTECTION: {len(all_inputs)} inputs, {len(all_textareas)} textareas, {len(all_selects)} selects')
    print('-' * 70)
    
    # ============================================
    # 1. INPUTS
    # ============================================
    for idx, inp in enumerate(all_inputs):
        try:
            if not inp.is_displayed():
                continue
            
            itype = (inp.get_attribute('type') or 'text').lower()
            name = (inp.get_attribute('name') or '').lower()
            inp_id = (inp.get_attribute('id') or '').lower()
            placeholder = (inp.get_attribute('placeholder') or '').lower()
            
            if itype in ['submit', 'button', 'hidden', 'image', 'reset', 'file']:
                continue
            
            # Identifiant du champ
            field_id = name or inp_id or placeholder or f"input_{idx}"
            
            # NOUVEAU: Identifier le formulaire parent
            form_id = get_form_id_for_element(driver, inp)
            
            field_info = {
                'form_id': form_id,  # NOUVEAU
                'index': idx,
                'type': itype,
                'name': field_id,
                'html_name': name,
                'html_id': inp_id,
                'placeholder': placeholder,
                'value': inp.get_attribute('value') or '',
                'suggestions': []
            }
            
            # Utiliser la détection améliorée
            field_info['suggestions'] = detect_field_type_improved(field_id, use_levenshtein, threshold)
            
            # Ajouter aux champs du formulaire
            if form_id not in detected_fields_by_form:
                detected_fields_by_form[form_id] = []
            detected_fields_by_form[form_id].append(field_info)
            
            # Affichage avec détails de détection
            suggestion_str = ""
            if field_info['suggestions']:
                top = field_info['suggestions'][0]
                method = top.get('method', '?')
                suggestion_str = f" → {top['field_type']} ({top['score']}) [{method}]"
            else:
                suggestion_str = " → [NO MATCH]"
            
            print(f"  [{itype.upper():8}] {field_id:35} {suggestion_str} [FORM: {form_id}]")
            
        except Exception as e:
            pass
    
    # ============================================
    # 2. TEXTAREAS
    # ============================================
    for idx, ta in enumerate(all_textareas):
        try:
            if not (ta.is_displayed() and ta.is_enabled()):
                continue
            
            name = (ta.get_attribute('name') or ta.get_attribute('id') or '').lower()
            field_id = name or f"textarea_{idx}"
            
            # NOUVEAU: Identifier le formulaire parent
            form_id = get_form_id_for_element(driver, ta)
            
            field_info = {
                'form_id': form_id,  # NOUVEAU
                'index': idx,
                'type': 'textarea',
                'name': field_id,
                'html_name': name,
                'value': ta.text[:50] + '...' if len(ta.text) > 50 else ta.text,
                'suggestions': []
            }
            
            # Utiliser la détection améliorée
            field_info['suggestions'] = detect_field_type_improved(field_id, use_levenshtein, threshold)
            
            # Ajouter aux champs du formulaire
            if form_id not in detected_fields_by_form:
                detected_fields_by_form[form_id] = []
            detected_fields_by_form[form_id].append(field_info)
            
            # Affichage avec détails de détection
            suggestion_str = ""
            if field_info['suggestions']:
                top = field_info['suggestions'][0]
                method = top.get('method', '?')
                suggestion_str = f" → {top['field_type']} ({top['score']}) [{method}]"
            else:
                suggestion_str = " → [NO MATCH]"
            
            print(f"  [TEXTAREA ] {field_id:35} {suggestion_str} [FORM: {form_id}]")
            
        except:
            pass
    
    # ============================================
    # 3. SELECTS
    # ============================================
    for idx, sel_elem in enumerate(all_selects):
        try:
            if not (sel_elem.is_displayed() and sel_elem.is_enabled()):
                continue
            
            name = (sel_elem.get_attribute('name') or sel_elem.get_attribute('id') or '').lower()
            field_id = name or f"select_{idx}"
            
            # NOUVEAU: Identifier le formulaire parent
            form_id = get_form_id_for_element(driver, sel_elem)
            
            sel = Select(sel_elem)
            options = [opt.text for opt in sel.options]
            
            field_info = {
                'form_id': form_id,  # NOUVEAU
                'index': idx,
                'type': 'select',
                'name': field_id,
                'html_name': name,
                'options': options[:5],  # Les 5 premières options
                'total_options': len(options),
                'suggestions': []
            }
            
            # Utiliser la détection améliorée
            field_info['suggestions'] = detect_field_type_improved(field_id, use_levenshtein, threshold)
            
            # Ajouter aux champs du formulaire
            if form_id not in detected_fields_by_form:
                detected_fields_by_form[form_id] = []
            detected_fields_by_form[form_id].append(field_info)
            
            # Affichage avec détails de détection
            suggestion_str = ""
            if field_info['suggestions']:
                top = field_info['suggestions'][0]
                method = top.get('method', '?')
                suggestion_str = f" → {top['field_type']} ({top['score']}) [{method}]"
            else:
                suggestion_str = " → [NO MATCH]"
            
            print(f"  [SELECT   ] {field_id:35} ({len(options):2} opt) {suggestion_str} [FORM: {form_id}]")
            
        except:
            pass
    
    print('-' * 70)
    total_fields = sum(len(fields) for fields in detected_fields_by_form.values())
    print(f"✅ Total: {total_fields} champs détectés dans {len(detected_fields_by_form)} formulaire(s)\n")
    
    # NOUVEAU: Retourner en format aplati pour compatibilité avec la réponse API
    all_fields = []
    for form_id, fields in detected_fields_by_form.items():
        all_fields.extend(fields)
    
    # Stocker aussi la structure par formulaire dans la session pour plus tard
    return all_fields


# ===============================================
# �📝 FONCTION PRINCIPALE DE REMPLISSAGE
# ===============================================

def fill_forms(driver, provided_values: Dict = None, use_levenshtein: bool = True, threshold: float = 0.5, target_form_id: str = None) -> List[Dict]:
    """
    Remplit les formulaires avec les valeurs fournies.
    Si target_form_id est fourni, ne remplie QUE ce formulaire.
    """
    
    if provided_values is None:
        provided_values = {}
    
    # Convertir toutes les clés en minuscules pour la recherche
    values_lower = {k.lower(): v for k, v in provided_values.items()}
    
    filled_fields = []
    
    all_inputs = driver.find_elements(By.TAG_NAME, 'input')
    all_textareas = driver.find_elements(By.TAG_NAME, 'textarea')
    all_selects = driver.find_elements(By.TAG_NAME, 'select')
    
    if target_form_id:
        print(f'\n📋 Trouvés: {len(all_inputs)} inputs, {len(all_textareas)} textareas, {len(all_selects)} selects')
        print(f'🎯 Ciblage FORMULAIRE: {target_form_id}')
    else:
        print(f'\n📋 Trouvés: {len(all_inputs)} inputs, {len(all_textareas)} textareas, {len(all_selects)} selects')
    print('-' * 50)
    
    # ============================================
    # 1. INPUTS
    # ============================================
    for inp in all_inputs:
        try:
            if not inp.is_displayed():
                continue
            
            # NOUVEAU: Filtrer par form_id si fourni
            if target_form_id:
                element_form_id = get_form_id_for_element(driver, inp)
                if element_form_id != target_form_id:
                    continue  # Sauter cet élément - il n'appartient pas au bon formulaire
            
            itype = (inp.get_attribute('type') or 'text').lower()
            name = (inp.get_attribute('name') or '').lower()
            inp_id = (inp.get_attribute('id') or '').lower()
            placeholder = (inp.get_attribute('placeholder') or '').lower()
            
            if itype in ['submit', 'button', 'hidden', 'image', 'reset', 'file']:
                continue
            
            # Identifiant du champ
            field_id = name or inp_id or placeholder
            
            # ===== CHECKBOX =====
            if itype == 'checkbox':
                should_check, matched_key = should_check_checkbox(inp, values_lower, driver)
                
                if should_check and not inp.is_selected():
                    try:
                        inp.click()
                    except:
                        try:
                            driver.execute_script("arguments[0].click();", inp)
                        except:
                            pass
                    
                    if inp.is_selected():
                        filled_fields.append({
                            'type': 'checkbox',
                            'name': field_id,
                            'value': matched_key or 'checked'
                        })
                        print(f"  ☑️  Checkbox '{field_id}' coché ({matched_key})")
                continue
            
            # ===== RADIO =====
            if itype == 'radio':
                input_value = inp.get_attribute('value') or ''
                label_text = get_element_label(inp, driver)
                
                # DEBUG
                print(f"  🔍 Radio détecté: field_id='{field_id}', value='{input_value}', label='{label_text}'")
                
                # Chercher la valeur cible pour ce groupe de radios
                target = None
                
                # Par nom exact
                if name in values_lower:
                    target = values_lower[name]
                    print(f"      → Match par nom: target='{target}'")
                
                # Par type de champ
                if target is None:
                    field_type = get_field_type(name or inp_id)
                    if field_type and field_type in values_lower:
                        target = values_lower[field_type]
                        print(f"      → Match par type ({field_type}): target='{target}'")
                
                # Vérifier si ce radio correspond
                if target:
                    match = match_radio_value(str(target), input_value, label_text)
                    print(f"      → match_radio_value('{target}', '{input_value}', '{label_text}') = {match}")
                    if match:
                        if not inp.is_selected():
                            try:
                                inp.click()
                            except:
                                try:
                                    driver.execute_script("arguments[0].click();", inp)
                                except:
                                    pass
                            
                            if inp.is_selected():
                                filled_fields.append({
                                    'type': 'radio',
                                    'name': name or inp_id,
                                    'value': input_value
                                })
                                print(f"  🔘 Radio '{name}' = '{input_value}' (SÉLECTIONNÉ)")
                        else:
                            print(f"  🔘 Radio '{name}' = '{input_value}' (DÉJÀ SÉLECTIONNÉ)")
                continue
            
            # ===== DATE INPUT (HTML5) =====
            # Gestion spéciale pour <input type="date">
            if itype == 'date':
                value = None
                
                # Chercher la valeur par nom de champ
                if name in values_lower:
                    value = values_lower[name]
                
                # Chercher par label ou détection Levenshtein
                if value is None:
                    # Détection par keywords
                    if any(kw in field_id for kw in ['birthdate', 'birth', 'dob', 'date_naissance', 'anniversaire', 'naissance']):
                        value = values_lower.get('date_of_birth')
                    elif any(kw in field_id for kw in ['departure', 'depart']):
                        value = values_lower.get('departure_date')
                    elif any(kw in field_id for kw in ['return', 'retour']):
                        value = values_lower.get('return_date')
                
                # Remplir avec le format YYYY-MM-DD
                if value is not None:
                    try:
                        # Normaliser la date en format ISO 8601
                        date_value = normalize_date_to_iso(str(value))
                        
                        if date_value:
                            # Remplir le champ de date
                            inp.clear()
                            inp.send_keys(date_value)
                            
                            filled_fields.append({
                                'type': 'date',
                                'name': field_id,
                                'value': date_value
                            })
                            print(f"  📅 Input DATE '{field_id}' = '{date_value}'")
                        else:
                            print(f"  ⚠️  Impossible de parser la date '{field_id}': {value}")
                    except Exception as e:
                        print(f"  ⚠️  Erreur DATE '{field_id}': {e}")
                continue
            
            # ===== PASSWORD =====
            if itype == 'password':
                value = None
                # Confirmation de mot de passe
                if any(kw in field_id for kw in ['confirm', 'repeat', '2']):
                    value = values_lower.get('confirm_password') or values_lower.get('password')
                else:
                    value = values_lower.get('password')
                
                if value and inp.is_enabled():
                    try:
                        inp.clear()
                        inp.send_keys(str(value))
                        filled_fields.append({
                            'type': 'password',
                            'name': field_id,
                            'value': '********'
                        })
                        print(f"  🔒 Password '{field_id}'")
                    except:
                        pass
                continue
            
            # ===== TEXT et autres =====
            if not inp.is_enabled():
                continue
            
            value = None
            detected_field_type = None
            detection_method = "NONE"  # Pour tracker la méthode de détection
            confidence = 0.0  # Pour tracker la confiance
            
            # ============================================================
            # LOGIQUE AVEC PRIORITÉ AU LABEL
            # ============================================================
            
            # Récupérer le label du champ (TRÈS IMPORTANT!)
            label_text = get_element_label(inp, driver)
            
            # Créer une liste de candidats pour la détection (label EN PREMIER)
            candidates = []
            if label_text:
                candidates.append(label_text)
            candidates.append(field_id)  # Fallback sur le name/id du champ
            
            # ÉTAPE 1: Chercher correspondance EXACTE dans les keywords
            # IMPORTANT: Favoriser les keywords PLUS LONGS (plus spécifiques)
            for candidate in candidates:
                if not candidate:
                    continue
                
                # Créer une liste de tous les keywords avec leur type et longueur
                all_keywords = []
                for ftype, keywords in FIELD_KEYWORDS.items():
                    for kw in keywords:
                        all_keywords.append((kw, ftype, len(kw)))
                
                # Trier par longueur décroissante (les plus longs d'abord = plus spécifiques)
                all_keywords.sort(key=lambda x: x[2], reverse=True)
                
                # Chercher dans l'ordre
                for keyword, ftype, length in all_keywords:
                    if keyword in candidate:
                        detected_field_type = ftype
                        detection_method = "EXACT MATCH"
                        confidence = 1.0  # 100% de confiance pour un match exact
                        break
                
                if detected_field_type:
                    break
            
            # ÉTAPE 2: Si pas trouvé → utiliser Levenshtein (sur le label en priorité)
            if detected_field_type is None and use_levenshtein:
                for candidate in candidates:
                    if not candidate:
                        continue
                    
                    # Chercher avec Levenshtein et récupérer le score
                    best_type = None
                    best_score = 0.0
                    
                    name_lower = candidate.lower().replace('-', '_').replace(' ', '_')
                    for field_type, keywords in FIELD_KEYWORDS.items():
                        for keyword in keywords:
                            score = Levenshtein.ratio(name_lower, keyword)
                            if score > best_score and score >= threshold:
                                best_score = score
                                best_type = field_type
                    
                    if best_type:
                        detected_field_type = best_type
                        detection_method = "LEVENSHTEIN"
                        confidence = round(best_score * 100, 1)  # En pourcentage
                        break
            
            # ÉTAPE 3: Utiliser la valeur correspondante du profil
            # NOUVEAU: Utiliser le fallback intelligent
            if detected_field_type:
                value = get_value_with_fallback(detected_field_type, values_lower)
            
            # ÉTAPE 4: Fallback - chercher par nom exact du champ ou label
            if value is None:
                if field_id in values_lower:
                    value = values_lower[field_id]
                    if detection_method == "NONE":
                        detection_method = "DIRECT FIELD"
                        confidence = 1.0
                elif label_text and label_text in values_lower:
                    value = values_lower[label_text]
                    if detection_method == "NONE":
                        detection_method = "DIRECT LABEL"
                        confidence = 1.0
            
            # ÉTAPE 5: Gestion spéciale des champs de date
            # Remplissage jour/mois/année séparés
            if value is None and is_day_field(field_id):
                date_str = values_lower.get('date_of_birth')
                if date_str:
                    date_parts = parse_date_components(str(date_str))
                    if date_parts:
                        value = date_parts['day']
                        detection_method = "DATE_SPLIT"
                        confidence = 1.0
            
            if value is None and is_month_field(field_id):
                date_str = values_lower.get('date_of_birth')
                if date_str:
                    date_parts = parse_date_components(str(date_str))
                    if date_parts:
                        value = date_parts['month']
                        detection_method = "DATE_SPLIT"
                        confidence = 1.0
            
            if value is None and is_year_field(field_id):
                date_str = values_lower.get('date_of_birth')
                if date_str:
                    date_parts = parse_date_components(str(date_str))
                    if date_parts:
                        value = date_parts['year']
                        detection_method = "DATE_SPLIT"
                        confidence = 1.0
            
            # Remplissage des champs texte de date
            if value is None and is_date_text_field(field_id):
                # Essayer departure_date ou return_date
                if 'departure' in field_id or 'depart' in field_id:
                    value = values_lower.get('departure_date')
                    if value:
                        detection_method = "DATE_FIELD"
                        confidence = 1.0
                elif 'return' in field_id or 'retour' in field_id:
                    value = values_lower.get('return_date')
                    if value:
                        detection_method = "DATE_FIELD"
                        confidence = 1.0
            
            # Remplir
            if value is not None and not isinstance(value, (bool, list)):
                try:
                    inp.clear()
                    inp.send_keys(str(value))
                    filled_fields.append({
                        'type': itype,
                        'name': field_id,
                        'value': str(value)
                    })
                    # Affichage amélioré avec méthode de détection et confiance
                    confidence_str = ""
                    if detection_method != "NONE":
                        confidence_str = f" [{detection_method} - {confidence}%]"
                    print(f"  ✏️  Input '{field_id}' = '{value}'{confidence_str}")
                except Exception as e:
                    print(f"  ⚠️ Erreur '{field_id}': {e}")
        
        except Exception as e:
            pass
    
    # ============================================
    # 2. TEXTAREAS
    # ============================================
    for ta in all_textareas:
        try:
            if not (ta.is_displayed() and ta.is_enabled()):
                continue
            
            # NOUVEAU: Filtrer par form_id si fourni
            if target_form_id:
                element_form_id = get_form_id_for_element(driver, ta)
                if element_form_id != target_form_id:
                    continue  # Sauter cet élément
            
            name = (ta.get_attribute('name') or ta.get_attribute('id') or '').lower()
            
            value = values_lower.get(name)
            if value is None:
                field_type = get_field_type(name)
                if field_type:
                    value = values_lower.get(field_type)
            if value is None:
                value = values_lower.get('comments') or values_lower.get('message')
            
            if value and not isinstance(value, (bool, list)):
                try:
                    ta.clear()
                    ta.send_keys(str(value))
                    filled_fields.append({
                        'type': 'textarea',
                        'name': name,
                        'value': str(value)[:30] + '...'
                    })
                    print(f"  📝 Textarea '{name}'")
                except:
                    pass
        except:
            pass
    
    # ============================================
    # 3. SELECTS
    # ============================================
    for sel_elem in all_selects:
        try:
            if not (sel_elem.is_displayed() and sel_elem.is_enabled()):
                continue
            
            # NOUVEAU: Filtrer par form_id si fourni
            if target_form_id:
                element_form_id = get_form_id_for_element(driver, sel_elem)
                if element_form_id != target_form_id:
                    continue  # Sauter cet élément
            
            sel = Select(sel_elem)
            name = (sel_elem.get_attribute('name') or sel_elem.get_attribute('id') or '').lower()
            
            value = values_lower.get(name)
            if value is None:
                field_type = get_field_type(name)
                if field_type:
                    value = values_lower.get(field_type)
            
            if value and not isinstance(value, (bool, list)):
                try:
                    sel.select_by_visible_text(str(value))
                    filled_fields.append({
                        'type': 'select',
                        'name': name,
                        'value': str(value)
                    })
                    print(f"  🔽 Select '{name}' = '{value}'")
                except:
                    try:
                        sel.select_by_value(str(value))
                        filled_fields.append({
                            'type': 'select',
                            'name': name,
                            'value': str(value)
                        })
                        print(f"  🔽 Select '{name}' = '{value}'")
                    except:
                        pass
        except:
            pass
    
    return filled_fields


# ===============================================
# 🌐 ENDPOINTS API
# ===============================================

@app.get("/")
async def root():
    return {
        "message": "Form Autofill API v5",
        "version": "5.0.0",
        "levenshtein": "OUI - utilisé pour la détection flexible",
        "profils": list(GENERIC_PROFILES.keys()),
        "corrections": [
            "Basic-Fit: adresses séparées",
            "Basic-Fit: radio genre par label",
            "Basic-Fit: checkboxes communication"
        ]
    }


@app.get("/profiles")
async def get_profiles():
    """Retourne la liste des profils génériques disponibles"""
    return {
        "profiles": {
            profile_id: {
                "id": profile_id,
                "name": profile_data.get('name', profile_id),
                "email": profile_data.get('email'),
                "first_name": profile_data.get('first_name'),
                "last_name": profile_data.get('last_name'),
                "country": profile_data.get('country'),
            }
            for profile_id, profile_data in GENERIC_PROFILES.items()
        }
    }


@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Retourne les infos complètes d'un profil"""
    if profile_id not in GENERIC_PROFILES:
        raise HTTPException(status_code=404, detail=f"Profil '{profile_id}' non trouvé")
    
    return {
        "profile_id": profile_id,
        "data": GENERIC_PROFILES[profile_id]
    }


@app.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    if request.session_id in active_sessions:
        raise HTTPException(status_code=400, detail="Session existe déjà")
    
    try:
        driver = create_driver()
        if request.maximize:
            driver.maximize_window()
        driver.get(request.url)
        time.sleep(2)
        
        active_sessions[request.session_id] = {
            'driver': driver,
            'url': request.url,
            'created_at': time.time()
        }
        
        return SessionResponse(success=True, message="Session créée", session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    driver = active_sessions[session_id]['driver']
    return {
        "session_id": session_id,
        "current_url": driver.current_url,
        "title": driver.title,
        "created_at": active_sessions[session_id]['created_at']
    }


@app.post("/form/detect", response_model=DetectFieldsResponse)
async def detect_form_fields(request: DetectFieldsRequest):
    """Détecte tous les champs du formulaire"""
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    driver = active_sessions[request.session_id]['driver']
    
    try:
        # Attendre que le document soit complètement chargé
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        time.sleep(1)  # Délai supplémentaire pour les scripts JS
        
        fields = detect_fields(
            driver,
            use_levenshtein=request.use_levenshtein,
            threshold=request.levenshtein_threshold
        )
        return DetectFieldsResponse(success=True, message=f"{len(fields)} champ(s) détectés", fields=fields, total=len(fields))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/form/fill", response_model=FormFillResponse)
async def fill_form(request: FillFormRequest):
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    driver = active_sessions[request.session_id]['driver']
    
    try:
        # Attendre que le document soit complètement chargé
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        time.sleep(1)
        filled = fill_forms(
            driver,
            provided_values=request.values,
            use_levenshtein=request.use_levenshtein,
            threshold=request.levenshtein_threshold,
            target_form_id=request.form_id  # NOUVEAU: passer le form_id cible
        )
        return FormFillResponse(success=True, message=f"{len(filled)} champ(s)", filled_fields=filled)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/{session_id}/navigate")
async def navigate(session_id: str, url: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    driver = active_sessions[session_id]['driver']
    driver.get(url)
    time.sleep(2)
    return {"success": True, "current_url": driver.current_url}


@app.post("/session/{session_id}/click-next")
async def click_next_button(session_id: str):
    """
    Cherche et clique sur un bouton "Suivant", "Next", "Continue", etc.
    pour passer au formulaire suivant
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    driver = active_sessions[session_id]['driver']
    
    try:
        # Mots-clés pour chercher le bouton suivant
        next_keywords = ['suivant', 'next', 'continue', 'continuer', 'avancer', 'forward', 'submit', 'envoyer']
        
        # Chercher des boutons par texte
        for keyword in next_keywords:
            try:
                buttons = driver.find_elements(By.XPATH, f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                if buttons:
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(2)
                            return {
                                "success": True,
                                "message": f"Bouton '{keyword}' cliqué",
                                "current_url": driver.current_url
                            }
            except:
                pass
        
        # Chercher des inputs type submit
        try:
            submit_btn = driver.find_element(By.XPATH, "//input[@type='submit' or @type='button']")
            if submit_btn.is_displayed() and submit_btn.is_enabled():
                submit_btn.click()
                time.sleep(2)
                return {
                    "success": True,
                    "message": "Bouton submit cliqué",
                    "current_url": driver.current_url
                }
        except:
            pass
        
        return {
            "success": False,
            "message": "Aucun bouton suivant trouvé",
            "current_url": driver.current_url
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    return {
        "total": len(active_sessions),
        "sessions": [{"id": k, "url": v['driver'].current_url} for k, v in active_sessions.items()]
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 API Form Autofill v5")
    print("📚 http://localhost:8000/docs")
    print("✅ Levenshtein: OUI")
    uvicorn.run(app, host="0.0.0.0", port=8000)
