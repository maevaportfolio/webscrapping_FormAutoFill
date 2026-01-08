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
# 🔧 CONFIGURATION
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
    'zip': ['zip', 'postal', 'postcode', 'plz', 'code_postal', 'codepostal'],
    'street_number': ['numero', 'numéro', 'number', 'housenumber', 'streetnumber', 'no'],
    'street': ['rue', 'street', 'strasse', 'adresse', 'address'],
    'street_extra': ['complement', 'complément', 'extra', 'additional', 'zusatz', 'optionnel'],
    'city': ['city', 'ville', 'town', 'stadt', 'ort', 'locality'],
    'country': ['country', 'pays', 'land', 'nation'],

      
    # === DOCUMENTS ===
    'passport': ['passport', 'passeport', 'passport_number', 'passport_no'],
    
    # === DATES ===
    'date_of_birth': ['birth', 'birthdate', 'dob', 'date_of_birth', 'dateofbirth', 'date_naissance', 'birthday'],
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
    'departure_date': '2025-11-15',
    'return_date': '2025-11-22',
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

def get_field_type(field_name: str, threshold: float = 0.5) -> Optional[str]:
    """
    Détecte le type de champ en utilisant Levenshtein.
    Retourne le type de champ ou None.
    """
    if not field_name:
        return None
    
    name_lower = field_name.lower().replace('-', '_').replace(' ', '_')
    best_type = None
    best_score = 0.0
    
    for field_type, keywords in FIELD_KEYWORDS.items():
        for kw in keywords:
            # Score exact si le mot-clé est dans le nom
            if kw in name_lower:
                score = 0.95
            else:
                # Sinon utiliser Levenshtein
                score = Levenshtein.ratio(name_lower, kw)
            
            if score > best_score:
                best_score = score
                best_type = field_type
    
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
# 📝 FONCTION PRINCIPALE DE REMPLISSAGE
# ===============================================

def fill_forms(driver, provided_values: Dict = None, use_levenshtein: bool = True, threshold: float = 0.5) -> List[Dict]:
    """Remplit les formulaires avec les valeurs fournies"""
    
    if provided_values is None:
        provided_values = {}
    
    # Convertir toutes les clés en minuscules pour la recherche
    values_lower = {k.lower(): v for k, v in provided_values.items()}
    
    filled_fields = []
    
    all_inputs = driver.find_elements(By.TAG_NAME, 'input')
    all_textareas = driver.find_elements(By.TAG_NAME, 'textarea')
    all_selects = driver.find_elements(By.TAG_NAME, 'select')
    
    print(f'\n📋 Trouvés: {len(all_inputs)} inputs, {len(all_textareas)} textareas, {len(all_selects)} selects')
    print('-' * 50)
    
    # ============================================
    # 1. INPUTS
    # ============================================
    for inp in all_inputs:
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
                
                # Chercher la valeur cible pour ce groupe de radios
                target = None
                
                # Par nom exact
                if name in values_lower:
                    target = values_lower[name]
                
                # Par type de champ
                if target is None:
                    field_type = get_field_type(name or inp_id)
                    if field_type and field_type in values_lower:
                        target = values_lower[field_type]
                
                # Vérifier si ce radio correspond
                if target and match_radio_value(str(target), input_value, label_text):
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
                            print(f"  🔘 Radio '{name}' = '{input_value}'")
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
            
            # 1. Chercher par nom exact
            if field_id in values_lower:
                value = values_lower[field_id]
            
            # 2. Chercher par type de champ détecté (Levenshtein)
            if value is None and use_levenshtein:
                field_type = get_field_type(field_id, threshold)
                if field_type and field_type in values_lower:
                    value = values_lower[field_type]
            
            # 3. Cas spéciaux pour l'adresse (éviter de tout mettre "Rue de la Paix")
            # Numéro
            if value is None and any(kw in field_id for kw in ['numero', 'number', 'numéro', 'housenumber']):
                value = values_lower.get('numero') or values_lower.get('number') or values_lower.get('street_number')
            
            # Rue
            if value is None and any(kw in field_id for kw in ['rue', 'street']) and 'number' not in field_id:
                value = values_lower.get('rue') or values_lower.get('street')
            
            # Complément
            if value is None and any(kw in field_id for kw in ['complement', 'extra', 'additional', 'optionnel']):
                value = values_lower.get('complement') or values_lower.get('extra') or values_lower.get('street_extra')
            
            # Email confirmation
            if value is None and 'confirm' in field_id and 'email' in field_id:
                value = values_lower.get('email_confirm') or values_lower.get('email')
            
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
                    print(f"  ✏️  Input '{field_id}' = '{value}'")
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
        "corrections": [
            "Basic-Fit: adresses séparées",
            "Basic-Fit: radio genre par label",
            "Basic-Fit: checkboxes communication"
        ]
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


@app.post("/form/fill", response_model=FormFillResponse)
async def fill_form(request: FillFormRequest):
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    driver = active_sessions[request.session_id]['driver']
    
    try:
        time.sleep(1)
        filled = fill_forms(
            driver,
            provided_values=request.values,
            use_levenshtein=request.use_levenshtein,
            threshold=request.levenshtein_threshold
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
