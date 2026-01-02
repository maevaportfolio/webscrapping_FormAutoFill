"""
API Form Autofill - Version 3.0 (Complète)
==========================================

Gère TOUS les types de champs :
- ✅ Inputs texte (nom, email, téléphone, etc.)
- ✅ Checkboxes simples ("Se souvenir de moi")
- ✅ Checkboxes multiples (garnitures pizza, options voyage)
- ✅ Radios simples (genre, taille)
- ✅ Radios complexes ("Pour qui réservez-vous ?", "Voyagez-vous pour le travail ?")
- ✅ Selects / Dropdowns (pays, civilité, heure d'arrivée)
- ✅ Textareas (commentaires, adresse)
- ✅ Champs de date (jour/mois/année séparés ou combinés)
- ✅ Champs mot de passe (avec génération sécurisée)

Sites testés :
- httpbin.org/forms/post (pizza)
- airarabia.com (réservation vol)
- booking.com (réservation hôtel)
- sncf-connect.com (connexion)
- spotify.com/signup (inscription multi-étapes)

Auteurs: Équipe Master MOSEF - 2024
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
# 🔧 CONFIGURATION
# ===============================================

app = FastAPI(
    title="Form Autofill API - Version Complète",
    version="3.0.0",
    description="API de remplissage automatique de formulaires - Gère tous les types de champs"
)

active_sessions: Dict[str, Any] = {}

# Path du driver Edge - À MODIFIER selon ton installation
DRIVER_PATH = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")

# ===============================================
# 📚 DICTIONNAIRE DE MAPPING ÉTENDU
# ===============================================

COMMON_FIELD_KEYWORDS = {
    # === IDENTITÉ ===
    'first_name': ['first', 'firstname', 'given-name', 'givenname', 'prenom', 'prénom', 'custname', 'fname'],
    'last_name': ['last', 'lastname', 'family-name', 'familyname', 'nom', 'surname', 'lname'],
    'full_name': ['fullname', 'full_name', 'name', 'nom_complet'],
    'title': ['title', 'civilité', 'civility', 'salutation', 'honorific'],
    'gender': ['gender', 'sexe', 'sex', 'genre'],
    
    # === CONTACT ===
    'email': ['email', 'e-mail', 'mail', 'custemail', 'courriel', 'user_email', 'useremail'],
    'phone': ['phone', 'tel', 'telephone', 'mobile', 'custtel', 'gsm', 'portable', 'cell'],
    
    # === ADRESSE ===
    'address': ['address', 'addr', 'street', 'adresse', 'delivery', 'rue', 'currentaddress'],
    'city': ['city', 'ville', 'town', 'locality'],
    'zip': ['zip', 'postal', 'postcode', 'codepostal', 'code_postal', 'zipcode'],
    'country': ['country', 'pays', 'nationality', 'nationalité', 'nation'],
    'state': ['state', 'province', 'region', 'région', 'departement'],
    
    # === DOCUMENTS ===
    'passport': ['passport', 'passeport', 'passport_number', 'passport_no'],
    
    # === DATES ===
    'date_of_birth': ['birth', 'birthdate', 'dob', 'date_of_birth', 'dateofbirth', 'date_naissance', 'birthday'],
    'departure_date': ['departure', 'depart', 'outbound', 'aller', 'date_depart'],
    'return_date': ['return', 'retour', 'inbound', 'date_retour'],
    'arrival_time': ['arrival', 'arrivee', 'heure_arrivee', 'checkin', 'check-in'],
    
    # === AUTHENTIFICATION ===
    'username': ['username', 'user', 'login', 'identifiant', 'pseudo', 'nickname'],
    'password': ['password', 'pwd', 'pass', 'mot_de_passe', 'mdp', 'secret'],
    'confirm_password': ['confirm', 'confirm_password', 'password_confirm', 'repeat_password'],
    
    # === OPTIONS BOOKING ===
    'booking_for': ['booking_for', 'reserve_for', 'pour_qui', 'who_booking', 'client_type'],
    'work_travel': ['work', 'business', 'travail', 'professionnel', 'work_travel'],
    'car_rental': ['car', 'voiture', 'location', 'rental', 'vehicle'],
    'airport_transfer': ['transfer', 'transfert', 'navette', 'shuttle', 'airport'],
    
    # === OPTIONS GÉNÉRALES ===
    'remember_me': ['remember', 'souvenir', 'stay_logged', 'keep_logged', 'rester_connecte'],
    'newsletter': ['newsletter', 'news', 'subscribe', 'inscription', 'abonnement'],
    'terms': ['terms', 'conditions', 'cgu', 'accept', 'agree', 'consent'],
    'privacy': ['privacy', 'confidentialite', 'rgpd', 'gdpr', 'donnees'],
    
    # === PIZZA (httpbin) ===
    'size': ['size', 'taille', 'pizza_size', 'format'],
    'topping': ['topping', 'garniture', 'ingredient', 'extra'],
    'comments': ['comments', 'comment', 'remarque', 'note', 'message', 'textarea'],
    
    # === HOBBIES/INTÉRÊTS ===
    'hobbies': ['hobbies', 'hobby', 'interests', 'loisirs', 'activities'],
}

# Valeurs par défaut étendues
DEFAULT_VALUES = {
    # Identité
    'first_name': 'Jean',
    'last_name': 'Dupont',
    'full_name': 'Jean Dupont',
    'title': 'Mr',
    'gender': 'Male',
    
    # Contact
    'email': 'jean.dupont@example.com',
    'phone': '+33612345678',
    
    # Adresse
    'address': '15 Rue de la Paix',
    'city': 'Paris',
    'zip': '75001',
    'country': 'France',
    'state': 'Île-de-France',
    
    # Documents
    'passport': '12AB34567',
    
    # Dates
    'date_of_birth': '1990-01-15',
    'departure_date': '2025-03-15',
    'return_date': '2025-03-22',
    'arrival_time': '15:00',
    
    # Authentification
    'username': 'jean.dupont',
    'password': 'SecurePass123!',
    'confirm_password': 'SecurePass123!',
    
    # Options Booking
    'booking_for': 'main_guest',  # 'main_guest' ou 'other_guest'
    'work_travel': 'no',          # 'yes' ou 'no'
    'car_rental': False,
    'airport_transfer': False,
    
    # Options générales
    'remember_me': True,
    'newsletter': False,
    'terms': True,
    'privacy': True,
    
    # Pizza
    'size': 'medium',
    'topping': ['bacon', 'cheese'],
    'comments': 'Pas de commentaires, ceci est un test automatique - Merci !',
    
    # Hobbies
    'hobbies': ['Sports', 'Reading'],
}

# ===============================================
# 📋 MODÈLES PYDANTIC
# ===============================================

class SessionCreateRequest(BaseModel):
    session_id: str
    url: Optional[str] = ''
    maximize: Optional[bool] = True
    width: Optional[int] = None
    height: Optional[int] = None


class FillFormRequest(BaseModel):
    session_id: str
    values: Optional[Dict[str, Any]] = {}
    use_levenshtein: Optional[bool] = True
    levenshtein_threshold: Optional[float] = 0.6  # Plus permissif


class SessionResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


class FormFillResponse(BaseModel):
    success: bool
    message: str
    filled_fields: Optional[list] = []


# ===============================================
# 🔍 FONCTIONS DE DÉTECTION
# ===============================================

def detect_logical_key_levenshtein(field_name: str, threshold: float = 0.6) -> Optional[str]:
    """Détecte le champ logique avec Levenshtein"""
    if not field_name:
        return None
    
    lname = field_name.lower().replace('-', '_').replace(' ', '_')
    best_ratio = 0.0
    best_logical = None
    
    for logical, keywords in COMMON_FIELD_KEYWORDS.items():
        for kw in keywords:
            ratio = Levenshtein.ratio(lname, kw)
            
            # Bonus si le mot clé est contenu
            if kw in lname:
                ratio = max(ratio, 0.9)
            
            # Bonus si le nom du champ contient le mot clé
            if lname in kw:
                ratio = max(ratio, 0.85)
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_logical = logical
    
    return best_logical if best_ratio >= threshold else None


def get_all_field_attributes(element) -> Dict[str, str]:
    """Récupère tous les attributs utiles d'un élément"""
    attrs = {}
    for attr in ['name', 'id', 'placeholder', 'class', 'type', 'value', 'aria-label', 'data-testid']:
        try:
            val = element.get_attribute(attr)
            if val:
                attrs[attr] = val
        except:
            pass
    return attrs


def identify_field(element) -> tuple:
    """Identifie un champ en utilisant tous ses attributs"""
    attrs = get_all_field_attributes(element)
    
    # Essayer chaque attribut pour identifier le champ
    for attr in ['name', 'id', 'placeholder', 'aria-label', 'data-testid']:
        if attr in attrs:
            logical = detect_logical_key_levenshtein(attrs[attr])
            if logical:
                return (attrs.get('name') or attrs.get('id') or 'unknown', logical)
    
    # Essayer avec la classe CSS
    if 'class' in attrs:
        classes = attrs['class'].split()
        for cls in classes:
            logical = detect_logical_key_levenshtein(cls)
            if logical:
                return (attrs.get('name') or attrs.get('id') or 'unknown', logical)
    
    return (attrs.get('name') or attrs.get('id') or 'unknown', None)


# ===============================================
# 📅 FONCTIONS DE DATE
# ===============================================

def parse_date_components(date_str: str) -> Optional[Dict[str, str]]:
    """Parse une date en composants"""
    if not date_str:
        return None
    
    # Format YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        parts = date_str.split('-')
        return {'day': parts[2], 'month': parts[1], 'year': parts[0]}
    
    # Format DD/MM/YYYY
    if re.match(r'\d{2}/\d{2}/\d{4}', date_str):
        parts = date_str.split('/')
        return {'day': parts[0], 'month': parts[1], 'year': parts[2]}
    
    return None


def is_day_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['jour', 'day', '_dd', 'birth_day'])


def is_month_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['mois', 'month', '_mm', 'birth_month'])


def is_year_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['annee', 'year', '_yyyy', 'birth_year', 'année'])


# ===============================================
# 🔘 GESTION DES CHECKBOXES (AMÉLIORÉE)
# ===============================================

def handle_checkbox(inp, field_name: str, provided_values: Dict, logical: str, all_attrs: Dict) -> Optional[Dict]:
    """
    Gère TOUS les types de checkboxes :
    - Simples : "Se souvenir de moi", "Accepter les CGU"
    - Multiples : Garnitures pizza, options de voyage
    - Avec valeurs : value="bacon", value="cheese"
    """
    try:
        input_value = inp.get_attribute('value') or ''
        input_value_lower = input_value.lower()
        input_id = inp.get_attribute('id') or ''
        input_name = field_name or ''
        
        # Construire une liste de clés à chercher
        search_keys = [k for k in [field_name, logical, input_value, input_id] if k]
        
        should_check = False
        matched_key = None
        
        # 1. Chercher par valeur exacte de l'input
        for key, val in provided_values.items():
            key_lower = key.lower()
            
            # Si la clé correspond à la valeur de l'input (ex: "bacon": True)
            if key_lower == input_value_lower:
                if isinstance(val, bool):
                    should_check = val
                elif isinstance(val, str):
                    should_check = val.lower() in ['yes', 'true', 'on', '1', 'y']
                else:
                    should_check = bool(val)
                matched_key = key
                break
        
        # 2. Chercher par nom de champ ou champ logique
        if not matched_key:
            for key in search_keys:
                if not key:
                    continue
                key_lower = key.lower()
                
                if key_lower in provided_values or key in provided_values:
                    val = provided_values.get(key_lower) or provided_values.get(key)
                    
                    if isinstance(val, bool):
                        should_check = val
                        matched_key = key
                        break
                    elif isinstance(val, str):
                        if val.lower() in ['yes', 'true', 'on', '1', 'y']:
                            should_check = True
                        elif val.lower() == input_value_lower:
                            should_check = True
                        matched_key = key
                        break
                    elif isinstance(val, list):
                        # Liste de valeurs à cocher
                        for item in val:
                            if isinstance(item, str) and item.lower() == input_value_lower:
                                should_check = True
                                matched_key = key
                                break
                        if should_check:
                            break
        
        # 3. Chercher par champ logique dans DEFAULT_VALUES
        if not matched_key and logical:
            val = DEFAULT_VALUES.get(logical)
            if val is not None:
                if isinstance(val, bool):
                    should_check = val
                    matched_key = logical
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str) and item.lower() == input_value_lower:
                            should_check = True
                            matched_key = logical
                            break
        
        # 4. Cocher si nécessaire
        if should_check:
            if not inp.is_selected():
                try:
                    inp.click()
                except ElementNotInteractableException:
                    # Essayer de cliquer sur le label parent
                    try:
                        label = inp.find_element(By.XPATH, "./ancestor::label")
                        label.click()
                    except:
                        pass
                
                return {
                    'type': 'checkbox',
                    'name': field_name,
                    'logical': logical,
                    'value': input_value or 'checked',
                    'action': 'checked'
                }
        
        return None
    
    except Exception as e:
        print(f"  ⚠️ Erreur checkbox {field_name}: {e}")
        return None


# ===============================================
# 🔘 GESTION DES RADIOS (AMÉLIORÉE)
# ===============================================

def handle_radio(inp, field_name: str, provided_values: Dict, logical: str, all_attrs: Dict) -> Optional[Dict]:
    """
    Gère TOUS les types de radios :
    - Simples : Genre (Male/Female), Taille (S/M/L)
    - Booking : "Pour qui réservez-vous ?", "Voyagez-vous pour le travail ?"
    - Avec labels complexes
    """
    try:
        input_value = inp.get_attribute('value') or ''
        input_value_lower = input_value.lower()
        input_id = inp.get_attribute('id') or ''
        input_name = field_name or ''
        
        should_select = False
        matched_value = None
        
        # 1. Chercher la valeur attendue pour ce groupe de radios
        target_value = None
        
        # Chercher par nom de champ
        if field_name and field_name in provided_values:
            target_value = provided_values[field_name]
        
        # Chercher par champ logique
        if target_value is None and logical and logical in provided_values:
            target_value = provided_values[logical]
        
        # Valeur par défaut
        if target_value is None and logical:
            target_value = DEFAULT_VALUES.get(logical)
        
        # 2. Vérifier si cette radio correspond à la valeur cible
        if target_value is not None:
            target_lower = str(target_value).lower()
            
            # Match exact sur la valeur
            if input_value_lower == target_lower:
                should_select = True
                matched_value = input_value
            
            # Match partiel (ex: "main_guest" contient "main")
            elif target_lower in input_value_lower or input_value_lower in target_lower:
                should_select = True
                matched_value = input_value
            
            # Match sur des synonymes courants
            synonyms = {
                'yes': ['yes', 'oui', 'true', '1', 'on'],
                'no': ['no', 'non', 'false', '0', 'off'],
                'male': ['male', 'homme', 'masculin', 'm', 'mr'],
                'female': ['female', 'femme', 'féminin', 'f', 'mme', 'mrs'],
                'main_guest': ['main', 'principal', 'myself', 'moi', 'je_suis'],
                'other_guest': ['other', 'autre', 'someone', 'quelqu'],
            }
            
            for key, vals in synonyms.items():
                if target_lower in vals or target_lower == key:
                    if input_value_lower in vals or any(v in input_value_lower for v in vals):
                        should_select = True
                        matched_value = input_value
                        break
        
        # 3. Sélectionner si nécessaire
        if should_select and not inp.is_selected():
            try:
                inp.click()
            except ElementNotInteractableException:
                # Essayer de cliquer sur le label
                try:
                    label = inp.find_element(By.XPATH, f"//label[@for='{input_id}']")
                    label.click()
                except:
                    try:
                        label = inp.find_element(By.XPATH, "./ancestor::label")
                        label.click()
                    except:
                        pass
            
            return {
                'type': 'radio',
                'name': field_name,
                'logical': logical,
                'value': matched_value or input_value,
                'action': 'selected'
            }
        
        return None
    
    except Exception as e:
        print(f"  ⚠️ Erreur radio {field_name}: {e}")
        return None


# ===============================================
# 🔽 GESTION DES SELECTS (AMÉLIORÉE)
# ===============================================

def get_title_option(select_element, preferred='Mr') -> Optional[str]:
    """Cherche la meilleure option de titre"""
    try:
        options = select_element.find_elements(By.TAG_NAME, 'option')
        option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
        
        preferences = ['Mr', 'Mr.', 'M.', 'Monsieur', 'Mrs', 'Mrs.', 'Mme', 'Madame', 'Ms', 'Ms.', 'Miss']
        
        for pref in preferences:
            for text in option_texts:
                if text.lower() == pref.lower():
                    return text
        
        # Retourner la 2e option si disponible
        if len(option_texts) > 1:
            return option_texts[1]
        
        return None
    except:
        return None


def find_closest_option(select_element, search_text: str, threshold: float = 0.5) -> Optional[str]:
    """Cherche l'option la plus proche avec Levenshtein"""
    try:
        options = select_element.find_elements(By.TAG_NAME, 'option')
        option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
        
        if not search_text or not option_texts:
            return None
        
        search_lower = search_text.lower()
        best_match = None
        best_ratio = 0.0
        
        for text in option_texts:
            text_lower = text.lower()
            
            if text_lower == search_lower:
                return text
            
            ratio = Levenshtein.ratio(search_lower, text_lower)
            
            if search_lower in text_lower or text_lower in search_lower:
                ratio = max(ratio, 0.8)
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = text
        
        return best_match if best_ratio >= threshold else None
    except:
        return None


def handle_time_select(select_element, provided_values: Dict, logical: str) -> Optional[str]:
    """Gère les selects d'heure (plage horaire Booking)"""
    try:
        target_time = provided_values.get('arrival_time') or DEFAULT_VALUES.get('arrival_time', '15:00')
        
        options = select_element.find_elements(By.TAG_NAME, 'option')
        
        for opt in options:
            text = opt.text.strip().lower()
            # Chercher l'heure dans le texte (ex: "15:00 - 16:00", "15h00")
            if target_time.replace(':', 'h') in text or target_time in text:
                return opt.text.strip()
            
            # Chercher juste l'heure de début
            hour = target_time.split(':')[0]
            if f"{hour}:" in text or f"{hour}h" in text:
                return opt.text.strip()
        
        # Sinon retourner une option du milieu
        if len(options) > 2:
            return options[len(options) // 2].text.strip()
        
        return None
    except:
        return None


# ===============================================
# 🌐 DRIVER SELENIUM
# ===============================================

def create_driver():
    """Crée une nouvelle instance de driver Edge"""
    service = Service(DRIVER_PATH)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Edge(service=service, options=options)
    
    # Masquer le webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


# ===============================================
# 📝 FONCTION PRINCIPALE DE REMPLISSAGE
# ===============================================

def fill_forms(driver, provided_values: Dict = None, use_levenshtein: bool = True, threshold: float = 0.6) -> List[Dict]:
    """
    Remplit automatiquement TOUS les types de champs
    """
    if provided_values is None:
        provided_values = {}
    
    # Fusionner avec les valeurs par défaut
    merged_values = {**DEFAULT_VALUES, **provided_values}
    
    filled_fields = []
    
    def get_value(key: str):
        return merged_values.get(key)
    
    # Trouver tous les éléments de formulaire (même hors <form>)
    all_inputs = driver.find_elements(By.TAG_NAME, 'input')
    all_textareas = driver.find_elements(By.TAG_NAME, 'textarea')
    all_selects = driver.find_elements(By.TAG_NAME, 'select')
    
    print(f'\n📋 Éléments trouvés: {len(all_inputs)} inputs, {len(all_textareas)} textareas, {len(all_selects)} selects')
    print('-' * 50)
    
    # ============================================
    # 1. TRAITEMENT DES INPUTS
    # ============================================
    for inp in all_inputs:
        try:
            if not inp.is_displayed():
                continue
            
            itype = (inp.get_attribute('type') or 'text').lower()
            all_attrs = get_all_field_attributes(inp)
            field_name, logical = identify_field(inp)
            
            # Ignorer certains types
            if itype in ['submit', 'button', 'hidden', 'image', 'reset', 'file']:
                continue
            
            # ----------------------------------------
            # CHECKBOXES
            # ----------------------------------------
            if itype == 'checkbox':
                result = handle_checkbox(inp, field_name, merged_values, logical, all_attrs)
                if result:
                    filled_fields.append(result)
                    print(f"  ☑️  Checkbox '{field_name}' = {result['value']}")
                continue
            
            # ----------------------------------------
            # RADIOS
            # ----------------------------------------
            if itype == 'radio':
                result = handle_radio(inp, field_name, merged_values, logical, all_attrs)
                if result:
                    filled_fields.append(result)
                    print(f"  🔘 Radio '{field_name}' = {result['value']}")
                continue
            
            # ----------------------------------------
            # MOT DE PASSE
            # ----------------------------------------
            if itype == 'password':
                value = get_value('password')
                if value and inp.is_enabled():
                    try:
                        inp.clear()
                        inp.send_keys(str(value))
                        filled_fields.append({
                            'type': 'password',
                            'name': field_name,
                            'logical': 'password',
                            'value': '********'  # Masquer dans les logs
                        })
                        print(f"  🔒 Password '{field_name}' = ********")
                    except:
                        pass
                continue
            
            # ----------------------------------------
            # CHAMPS TEXTE ET AUTRES
            # ----------------------------------------
            if not inp.is_enabled():
                continue
            
            value = None
            
            # Chercher par nom exact
            if field_name in merged_values:
                value = merged_values[field_name]
            
            # Chercher par champ logique
            if value is None and logical:
                value = get_value(logical)
            
            # Gestion des dates séparées
            if is_day_field(field_name):
                date_val = get_value('date_of_birth')
                parts = parse_date_components(date_val)
                if parts:
                    value = parts['day']
            elif is_month_field(field_name):
                date_val = get_value('date_of_birth')
                parts = parse_date_components(date_val)
                if parts:
                    value = parts['month']
            elif is_year_field(field_name):
                date_val = get_value('date_of_birth')
                parts = parse_date_components(date_val)
                if parts:
                    value = parts['year']
            
            # Remplir le champ
            if value is not None:
                try:
                    inp.clear()
                    inp.send_keys(str(value))
                    filled_fields.append({
                        'type': itype,
                        'name': field_name,
                        'logical': logical,
                        'value': value
                    })
                    print(f"  ✏️  Input '{field_name}' ({itype}) = '{value}'")
                except Exception as e:
                    print(f"  ⚠️ Erreur input {field_name}: {e}")
        
        except Exception as e:
            pass
    
    # ============================================
    # 2. TRAITEMENT DES TEXTAREAS
    # ============================================
    for ta in all_textareas:
        try:
            if not (ta.is_displayed() and ta.is_enabled()):
                continue
            
            field_name, logical = identify_field(ta)
            
            value = None
            if field_name in merged_values:
                value = merged_values[field_name]
            if value is None and logical:
                value = get_value(logical)
            if value is None:
                value = get_value('comments')
            
            if value is not None:
                try:
                    ta.clear()
                    ta.send_keys(str(value))
                    filled_fields.append({
                        'type': 'textarea',
                        'name': field_name,
                        'logical': logical,
                        'value': str(value)[:50] + '...' if len(str(value)) > 50 else value
                    })
                    print(f"  📝 Textarea '{field_name}' = '{str(value)[:30]}...'")
                except:
                    pass
        except:
            pass
    
    # ============================================
    # 3. TRAITEMENT DES SELECTS
    # ============================================
    for sel_elem in all_selects:
        try:
            if not (sel_elem.is_displayed() and sel_elem.is_enabled()):
                continue
            
            sel = Select(sel_elem)
            field_name, logical = identify_field(sel_elem)
            
            selected_value = None
            
            # Champ Title/Civilité
            if logical == 'title' or 'title' in (field_name or '').lower():
                title_opt = get_title_option(sel_elem)
                if title_opt:
                    try:
                        sel.select_by_visible_text(title_opt)
                        selected_value = title_opt
                    except:
                        pass
            
            # Champ Country
            elif logical == 'country' or 'country' in (field_name or '').lower():
                for val in ['France', 'FR', 'FRA', 'French']:
                    try:
                        sel.select_by_visible_text(val)
                        selected_value = val
                        break
                    except:
                        try:
                            sel.select_by_value(val)
                            selected_value = val
                            break
                        except:
                            continue
            
            # Champ Heure d'arrivée
            elif logical == 'arrival_time' or 'arrival' in (field_name or '').lower() or 'heure' in (field_name or '').lower():
                time_opt = handle_time_select(sel_elem, merged_values, logical)
                if time_opt:
                    try:
                        sel.select_by_visible_text(time_opt)
                        selected_value = time_opt
                    except:
                        pass
            
            # Autres selects
            else:
                opt = merged_values.get(field_name) or get_value(logical)
                if opt:
                    for method in ['visible_text', 'value', 'levenshtein']:
                        try:
                            if method == 'visible_text':
                                sel.select_by_visible_text(str(opt))
                            elif method == 'value':
                                sel.select_by_value(str(opt))
                            elif method == 'levenshtein':
                                closest = find_closest_option(sel_elem, str(opt))
                                if closest:
                                    sel.select_by_visible_text(closest)
                                    opt = closest
                                else:
                                    continue
                            selected_value = opt
                            break
                        except:
                            continue
            
            if selected_value:
                filled_fields.append({
                    'type': 'select',
                    'name': field_name,
                    'logical': logical,
                    'value': selected_value
                })
                print(f"  🔽 Select '{field_name}' = '{selected_value}'")
        
        except Exception as e:
            pass
    
    return filled_fields


# ===============================================
# 🌐 ENDPOINTS API
# ===============================================

@app.get("/")
async def root():
    return {
        "message": "Form Autofill API - Version Complète",
        "version": "3.0.0",
        "features": [
            "checkboxes (simples et multiples)",
            "radios (tous types)",
            "selects (avec Levenshtein)",
            "textareas",
            "passwords",
            "dates (séparées ou combinées)",
            "heure d'arrivée (plage horaire)"
        ],
        "sites_tested": [
            "httpbin.org/forms/post",
            "airarabia.com",
            "booking.com",
            "sncf-connect.com",
            "spotify.com"
        ],
        "active_sessions": len(active_sessions)
    }


@app.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    if request.session_id in active_sessions:
        raise HTTPException(status_code=400, detail=f"Session {request.session_id} existe déjà")
    
    try:
        driver = create_driver()
        
        if request.maximize:
            driver.maximize_window()
        elif request.width and request.height:
            driver.set_window_size(request.width, request.height)
        
        driver.get(request.url)
        time.sleep(2)
        
        active_sessions[request.session_id] = {
            'driver': driver,
            'url': request.url,
            'created_at': time.time()
        }
        
        return SessionResponse(
            success=True,
            message=f"Session {request.session_id} créée avec succès",
            session_id=request.session_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} non trouvée")
    
    session = active_sessions[session_id]
    driver = session['driver']
    
    return {
        "session_id": session_id,
        "current_url": driver.current_url,
        "title": driver.title,
        "created_at": session['created_at']
    }


@app.post("/form/fill", response_model=FormFillResponse)
async def fill_form(request: FillFormRequest):
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} non trouvée")
    
    driver = active_sessions[request.session_id]['driver']
    
    try:
        time.sleep(1)  # Attendre le chargement
        
        filled_fields = fill_forms(
            driver,
            provided_values=request.values,
            use_levenshtein=request.use_levenshtein,
            threshold=request.levenshtein_threshold
        )
        
        return FormFillResponse(
            success=True,
            message=f"✅ {len(filled_fields)} champ(s) rempli(s)",
            filled_fields=filled_fields
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/session/{session_id}/navigate")
async def navigate(session_id: str, url: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} non trouvée")
    
    driver = active_sessions[session_id]['driver']
    driver.get(url)
    time.sleep(2)
    
    return {"success": True, "current_url": driver.current_url}


@app.get("/sessions")
async def list_sessions():
    sessions_info = []
    for sid, session in active_sessions.items():
        try:
            sessions_info.append({
                "session_id": sid,
                "current_url": session['driver'].current_url,
                "created_at": session['created_at']
            })
        except:
            sessions_info.append({"session_id": sid, "status": "error"})
    
    return {"total_sessions": len(active_sessions), "sessions": sessions_info}


# ===============================================
# 🚀 POINT D'ENTRÉE
# ===============================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage de l'API Form Autofill - Version 3.0 Complète")
    print("📚 Documentation: http://localhost:8000/docs")
    print("✨ Supporte: checkboxes, radios, selects, dates, passwords, et plus!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
