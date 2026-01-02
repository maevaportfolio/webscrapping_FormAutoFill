"""
API Form Autofill - Version Améliorée
=====================================

Améliorations par rapport à la version originale:
- ✅ Meilleure gestion des checkboxes (sélection multiple)
- ✅ Meilleure gestion des radios (sélection par valeur/label)
- ✅ Correction du champ Title
- ✅ Support du formulaire httpbin.org/forms/post (pizza)
- ✅ Architecture mieux structurée

Auteurs: Équipe Master MOSEF
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
import time
import os
import Levenshtein

# ===============================================
# 🔧 CONFIGURATION
# ===============================================

app = FastAPI(
    title="Form Autofill API - Version Améliorée",
    version="2.0.0",
    description="API de remplissage automatique de formulaires avec support checkbox/radio"
)

# Storage for active sessions
active_sessions: Dict[str, Any] = {}

# Path du driver Edge - À MODIFIER selon ton installation
DRIVER_PATH = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")

# ===============================================
# 📚 DICTIONNAIRE DE MAPPING
# ===============================================

COMMON_FIELD_KEYWORDS = {
    # Identité
    'first_name': ['first', 'firstname', 'given-name', 'givenname', 'prenom', 'prénom', 'custname'],
    'last_name': ['last', 'lastname', 'family-name', 'familyname', 'nom', 'surname'],
    'title': ['title', 'civilité', 'civility', 'salutation'],
    
    # Contact
    'email': ['email', 'e-mail', 'mail', 'custemail'],
    'phone': ['phone', 'tel', 'telephone', 'mobile', 'custtel'],
    
    # Adresse
    'address': ['address', 'addr', 'street', 'adresse', 'delivery'],
    'city': ['city', 'ville', 'town'],
    'zip': ['zip', 'postal', 'postcode', 'codepostal'],
    'country': ['country', 'pays', 'nationality', 'nationalité'],
    
    # Documents
    'passport': ['passport', 'passeport', 'passport_number', 'passport_no'],
    
    # Dates
    'date_of_birth': ['birth', 'birthdate', 'dob', 'date_of_birth', 'dateofbirth', 'date_naissance'],
    
    # Formulaire Pizza (httpbin)
    'size': ['size', 'taille', 'pizza_size'],
    'topping': ['topping', 'garniture', 'ingredient'],
    'comments': ['comments', 'comment', 'remarque', 'note', 'message'],
}

# Valeurs par défaut
DEFAULT_VALUES = {
    # Identité
    'first_name': 'Jean',
    'last_name': 'Dupont',
    'title': 'Mrs.',
    
    # Contact
    'email': 'jean.dupont@example.com',
    'phone': '+33123456789',
    
    # Adresse
    'address': '1 Rue Exemple',
    'city': 'Paris',
    'zip': '75001',
    'country': 'France',
    
    # Documents
    'passport': '12345678',
    
    # Dates
    'date_of_birth': '1990-01-15',
    
    # Pizza (httpbin)
    'size': 'medium',
    'topping': ['bacon', 'cheese'],  # Liste pour les checkboxes
    'comments': 'Test automatique',
}

# ===============================================
# 📋 MODÈLES PYDANTIC
# ===============================================

class SessionCreateRequest(BaseModel):
    session_id: str
    url: Optional[str] = 'https://httpbin.org/forms/post'
    maximize: Optional[bool] = True
    width: Optional[int] = None
    height: Optional[int] = None


class FillFormRequest(BaseModel):
    session_id: str
    values: Optional[Dict[str, Any]] = {}
    use_levenshtein: Optional[bool] = True
    levenshtein_threshold: Optional[float] = 0.7


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

def detect_logical_key_levenshtein(field_name: str, threshold: float = 0.7) -> Optional[str]:
    """
    Détecte le champ logique en utilisant la distance de Levenshtein.
    
    Args:
        field_name: Nom du champ HTML
        threshold: Seuil de similarité (0.0 - 1.0)
    
    Returns:
        Le champ logique détecté ou None
    """
    if not field_name:
        return None
    
    lname = field_name.lower()
    best_ratio = 0.0
    best_logical = None
    
    for logical, keywords in COMMON_FIELD_KEYWORDS.items():
        for kw in keywords:
            # Calcul du ratio de similarité
            ratio = Levenshtein.ratio(lname, kw)
            
            # Bonus si le mot clé est contenu dans le nom du champ
            if kw in lname:
                ratio = max(ratio, 0.9)
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_logical = logical
    
    return best_logical if best_ratio >= threshold else None


def detect_logical_key(field_name: str) -> Optional[str]:
    """Version sans Levenshtein (fallback)"""
    if not field_name:
        return None
    lname = field_name.lower()
    for logical, keywords in COMMON_FIELD_KEYWORDS.items():
        for kw in keywords:
            if kw in lname:
                return logical
    return None


# ===============================================
# 📅 FONCTIONS DE DATE
# ===============================================

def parse_date_components(date_str: str) -> Optional[Dict[str, str]]:
    """Parse une date YYYY-MM-DD en composants"""
    try:
        if not date_str:
            return None
        parts = date_str.split('-')
        if len(parts) == 3:
            return {'day': parts[2], 'month': parts[1], 'year': parts[0]}
    except Exception:
        pass
    return None


def is_day_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['jour', 'day', 'dd'])


def is_month_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['mois', 'month', 'mm'])


def is_year_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['annee', 'year', 'yyyy', 'année'])


# ===============================================
# 🎯 FONCTIONS DE DÉTECTION DE TYPE
# ===============================================

def is_country_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['country', 'pays', 'nationality'])


def is_title_field(field_name: str) -> bool:
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['title', 'civilité', 'civility', 'salutation'])


def is_size_field(field_name: str) -> bool:
    """Détecte si c'est un champ de taille (pizza)"""
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['size', 'taille'])


def is_topping_field(field_name: str) -> bool:
    """Détecte si c'est un champ de garniture (pizza)"""
    if not field_name:
        return False
    return any(kw in field_name.lower() for kw in ['topping', 'garniture', 'ingredient'])


# ===============================================
# 🔘 GESTION DES CHECKBOXES ET RADIOS (AMÉLIORÉ)
# ===============================================

def handle_checkbox(inp, field_name: str, provided_values: Dict, logical: str) -> Optional[Dict]:
    """
    Gère le remplissage d'une checkbox.
    
    Supporte:
    - Valeur booléenne: True/False
    - Valeur string: 'yes', 'on', 'true', etc.
    - Liste de valeurs: ['bacon', 'cheese'] pour cocher plusieurs
    
    Returns:
        Dict avec les infos du champ rempli ou None
    """
    try:
        input_value = inp.get_attribute('value') or ''
        input_value_lower = input_value.lower()
        
        # 1. Chercher une valeur spécifique pour ce champ
        val = None
        
        # Chercher par nom exact du champ
        if field_name and field_name in provided_values:
            val = provided_values[field_name]
        
        # Chercher par champ logique
        if val is None and logical and logical in provided_values:
            val = provided_values[logical]
        
        # Chercher par valeur de l'input (ex: 'bacon' dans provided_values)
        if val is None and input_value_lower in [v.lower() for v in provided_values.keys() if isinstance(v, str)]:
            for k, v in provided_values.items():
                if isinstance(k, str) and k.lower() == input_value_lower:
                    val = v
                    break
        
        # 2. Déterminer si on doit cocher
        should_check = False
        
        if val is None:
            # Pas de valeur fournie, ne pas cocher
            return None
        
        elif isinstance(val, bool):
            # Booléen direct
            should_check = val
        
        elif isinstance(val, str):
            # String: 'yes', 'true', 'on', '1' = cocher
            # Ou si la valeur correspond à la value de l'input
            val_lower = val.lower()
            if val_lower in ['y', 'yes', '1', 'true', 'on']:
                should_check = True
            elif val_lower == input_value_lower:
                should_check = True
        
        elif isinstance(val, list):
            # Liste de valeurs à cocher (ex: ['bacon', 'cheese'])
            # Cocher si la value de l'input est dans la liste
            for item in val:
                if isinstance(item, str) and item.lower() == input_value_lower:
                    should_check = True
                    break
        
        # 3. Cocher si nécessaire
        if should_check and not inp.is_selected():
            inp.click()
            return {
                'type': 'checkbox',
                'name': field_name,
                'logical': logical,
                'value': input_value,
                'action': 'checked'
            }
        
        return None
    
    except Exception as e:
        print(f"  Erreur checkbox {field_name}: {e}")
        return None


def handle_radio(inp, field_name: str, provided_values: Dict, logical: str) -> Optional[Dict]:
    """
    Gère le remplissage d'un bouton radio.
    
    Supporte:
    - Valeur exacte: 'medium' pour sélectionner size=medium
    - Valeur par défaut du champ logique
    
    Returns:
        Dict avec les infos du champ rempli ou None
    """
    try:
        input_value = inp.get_attribute('value') or ''
        input_value_lower = input_value.lower()
        
        # 1. Chercher la valeur à sélectionner
        val = None
        
        # Chercher par nom exact (ex: 'size' dans provided_values)
        if field_name and field_name in provided_values:
            val = provided_values[field_name]
        
        # Chercher par champ logique
        if val is None and logical and logical in provided_values:
            val = provided_values[logical]
        
        # Valeur par défaut
        if val is None and logical:
            val = DEFAULT_VALUES.get(logical)
        
        # 2. Vérifier si cette radio doit être sélectionnée
        if val is None:
            return None
        
        should_select = False
        
        if isinstance(val, str):
            # Si la valeur fournie correspond à la value de ce radio
            if val.lower() == input_value_lower:
                should_select = True
        
        # 3. Sélectionner si nécessaire
        if should_select and not inp.is_selected():
            inp.click()
            return {
                'type': 'radio',
                'name': field_name,
                'logical': logical,
                'value': input_value,
                'action': 'selected'
            }
        
        return None
    
    except Exception as e:
        print(f"  Erreur radio {field_name}: {e}")
        return None


# ===============================================
# 🔽 GESTION DES SELECTS (AMÉLIORÉ)
# ===============================================

def get_title_option(select_element, preferred='Mrs') -> Optional[str]:
    """Cherche la meilleure option de titre"""
    try:
        options = select_element.find_elements(By.TAG_NAME, 'option')
        option_texts = [opt.text.strip() for opt in options]
        
        # Ordre de préférence
        preferences = ['Mrs.', 'Mrs', 'Mme', 'Mme.', 'Madame', 'Ms.', 'Ms', 'Miss']
        
        for pref in preferences:
            for text in option_texts:
                if text.lower() == pref.lower():
                    return text
        
        # Si rien trouvé, retourner la 2e option (après le placeholder)
        if len(option_texts) > 1:
            return option_texts[1]
        
        return None
    except Exception:
        return None


def find_closest_option(select_element, search_text: str, threshold: float = 0.6) -> Optional[str]:
    """Cherche l'option la plus proche avec Levenshtein"""
    try:
        options = select_element.find_elements(By.TAG_NAME, 'option')
        option_texts = [opt.text.strip() for opt in options]
        
        if not search_text or not option_texts:
            return None
        
        search_lower = search_text.lower()
        best_match = None
        best_ratio = 0.0
        
        for text in option_texts:
            text_lower = text.lower()
            
            # Match exact
            if text_lower == search_lower:
                return text
            
            # Levenshtein
            ratio = Levenshtein.ratio(search_lower, text_lower)
            
            # Bonus si contenu
            if search_lower in text_lower or text_lower in search_lower:
                ratio = max(ratio, 0.75)
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = text
        
        return best_match if best_ratio >= threshold else None
    except Exception:
        return None


# ===============================================
# 🌐 DRIVER SELENIUM
# ===============================================

def create_driver():
    """Crée une nouvelle instance de driver Edge"""
    service = Service(DRIVER_PATH)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Edge(service=service, options=options)
    try:
        driver.maximize_window()
    except Exception:
        pass
    
    return driver


# ===============================================
# 📝 FONCTION PRINCIPALE DE REMPLISSAGE
# ===============================================

def fill_forms(driver, provided_values: Dict = None, use_levenshtein: bool = True, threshold: float = 0.7) -> List[Dict]:
    """
    Remplit automatiquement les formulaires détectés.
    
    Args:
        driver: Instance Selenium WebDriver
        provided_values: Dictionnaire des valeurs à remplir
        use_levenshtein: Utiliser la distance de Levenshtein
        threshold: Seuil de similarité
    
    Returns:
        Liste des champs remplis
    """
    if provided_values is None:
        provided_values = {}
    
    filled_fields = []
    
    # Fonction de détection
    detect_fn = detect_logical_key_levenshtein if use_levenshtein else detect_logical_key
    
    def get_value(logical_key: str):
        """Récupère la valeur pour un champ logique"""
        if logical_key in provided_values:
            return provided_values[logical_key]
        return DEFAULT_VALUES.get(logical_key)
    
    # Trouver tous les formulaires
    forms = driver.find_elements(By.TAG_NAME, 'form')
    
    # Si pas de formulaire, chercher les inputs directement
    if not forms:
        print("Aucun formulaire trouvé, recherche des inputs directement...")
        forms = [driver.find_element(By.TAG_NAME, 'body')]
    
    for i, form in enumerate(forms):
        print(f'\n📋 Formulaire {i+1}')
        print('-' * 40)
        
        # ============================================
        # 1. TRAITEMENT DES INPUTS
        # ============================================
        for inp in form.find_elements(By.TAG_NAME, 'input'):
            try:
                if not (inp.is_displayed() and inp.is_enabled()):
                    continue
                
                itype = (inp.get_attribute('type') or 'text').lower()
                realname = inp.get_attribute('name') or inp.get_attribute('id') or inp.get_attribute('placeholder') or ''
                
                # Ignorer certains types
                if itype in ['submit', 'button', 'hidden', 'image', 'reset']:
                    continue
                
                # Détecter le champ logique
                logical = detect_fn(realname, threshold) if use_levenshtein else detect_fn(realname)
                
                # ----------------------------------------
                # CHECKBOXES
                # ----------------------------------------
                if itype == 'checkbox':
                    result = handle_checkbox(inp, realname, provided_values, logical)
                    if result:
                        filled_fields.append(result)
                        print(f"  ☑️  Checkbox '{realname}' = {result['value']} (coché)")
                    continue
                
                # ----------------------------------------
                # RADIOS
                # ----------------------------------------
                if itype == 'radio':
                    result = handle_radio(inp, realname, provided_values, logical)
                    if result:
                        filled_fields.append(result)
                        print(f"  🔘 Radio '{realname}' = {result['value']} (sélectionné)")
                    continue
                
                # ----------------------------------------
                # CHAMPS TEXTE (et autres)
                # ----------------------------------------
                value = None
                
                # Chercher par nom exact
                if realname in provided_values:
                    value = provided_values[realname]
                
                # Chercher par champ logique
                if value is None and logical:
                    value = provided_values.get(logical)
                
                # Valeur par défaut
                if value is None and logical:
                    value = get_value(logical)
                
                # Gestion des dates séparées
                if is_day_field(realname):
                    date_val = provided_values.get('date_of_birth') or DEFAULT_VALUES.get('date_of_birth')
                    parts = parse_date_components(date_val)
                    if parts:
                        value = parts['day']
                
                elif is_month_field(realname):
                    date_val = provided_values.get('date_of_birth') or DEFAULT_VALUES.get('date_of_birth')
                    parts = parse_date_components(date_val)
                    if parts:
                        value = parts['month']
                
                elif is_year_field(realname):
                    date_val = provided_values.get('date_of_birth') or DEFAULT_VALUES.get('date_of_birth')
                    parts = parse_date_components(date_val)
                    if parts:
                        value = parts['year']
                
                # Remplir le champ
                if value is not None:
                    try:
                        inp.clear()
                    except Exception:
                        pass
                    
                    inp.send_keys(str(value))
                    filled_fields.append({
                        'type': itype,
                        'name': realname,
                        'logical': logical,
                        'value': value
                    })
                    print(f"  ✏️  Input '{realname}' ({itype}) = '{value}'")
            
            except Exception as e:
                print(f"  ❌ Erreur input: {e}")
        
        # ============================================
        # 2. TRAITEMENT DES TEXTAREAS
        # ============================================
        for ta in form.find_elements(By.TAG_NAME, 'textarea'):
            try:
                if not (ta.is_displayed() and ta.is_enabled()):
                    continue
                
                realname = ta.get_attribute('name') or ta.get_attribute('id') or ''
                logical = detect_fn(realname, threshold) if use_levenshtein else detect_fn(realname)
                
                value = None
                if realname in provided_values:
                    value = provided_values[realname]
                if value is None and logical:
                    value = provided_values.get(logical) or get_value(logical)
                
                if value is not None:
                    try:
                        ta.clear()
                    except Exception:
                        pass
                    ta.send_keys(str(value))
                    filled_fields.append({
                        'type': 'textarea',
                        'name': realname,
                        'logical': logical,
                        'value': value
                    })
                    print(f"  📝 Textarea '{realname}' = '{value[:30]}...' " if len(str(value)) > 30 else f"  📝 Textarea '{realname}' = '{value}'")
            
            except Exception as e:
                print(f"  ❌ Erreur textarea: {e}")
        
        # ============================================
        # 3. TRAITEMENT DES SELECTS
        # ============================================
        for sel_elem in form.find_elements(By.TAG_NAME, 'select'):
            try:
                if not (sel_elem.is_displayed() and sel_elem.is_enabled()):
                    continue
                
                sel = Select(sel_elem)
                realname = sel_elem.get_attribute('name') or sel_elem.get_attribute('id') or ''
                logical = detect_fn(realname, threshold) if use_levenshtein else detect_fn(realname)
                
                # Champ Title
                if is_title_field(realname):
                    title_opt = get_title_option(sel_elem)
                    if title_opt:
                        try:
                            sel.select_by_visible_text(title_opt)
                            filled_fields.append({
                                'type': 'select',
                                'name': realname,
                                'logical': 'title',
                                'value': title_opt
                            })
                            print(f"  🔽 Select '{realname}' (Titre) = '{title_opt}'")
                        except Exception as e:
                            print(f"  ⚠️  Erreur titre: {e}")
                    continue
                
                # Champ Country
                if is_country_field(realname):
                    for country_val in ['France', 'FR', 'FRA']:
                        try:
                            sel.select_by_visible_text(country_val)
                            filled_fields.append({
                                'type': 'select',
                                'name': realname,
                                'logical': 'country',
                                'value': country_val
                            })
                            print(f"  🔽 Select '{realname}' (Pays) = '{country_val}'")
                            break
                        except Exception:
                            try:
                                sel.select_by_value(country_val)
                                filled_fields.append({
                                    'type': 'select',
                                    'name': realname,
                                    'logical': 'country',
                                    'value': country_val
                                })
                                print(f"  🔽 Select '{realname}' (Pays) = '{country_val}'")
                                break
                            except Exception:
                                continue
                    continue
                
                # Autres selects
                opt = None
                if realname in provided_values:
                    opt = provided_values[realname]
                if opt is None and logical:
                    opt = provided_values.get(logical) or get_value(logical)
                
                if opt is not None:
                    selected = False
                    
                    # Essayer différentes méthodes
                    for method in ['visible_text', 'value', 'levenshtein']:
                        if selected:
                            break
                        
                        try:
                            if method == 'visible_text':
                                sel.select_by_visible_text(str(opt))
                            elif method == 'value':
                                sel.select_by_value(str(opt))
                            elif method == 'levenshtein' and use_levenshtein:
                                closest = find_closest_option(sel_elem, str(opt))
                                if closest:
                                    sel.select_by_visible_text(closest)
                                    opt = closest
                                else:
                                    continue
                            
                            filled_fields.append({
                                'type': 'select',
                                'name': realname,
                                'logical': logical,
                                'value': opt
                            })
                            print(f"  🔽 Select '{realname}' = '{opt}'")
                            selected = True
                        except Exception:
                            continue
            
            except Exception as e:
                print(f"  ❌ Erreur select: {e}")
    
    return filled_fields


# ===============================================
# 🌐 ENDPOINTS API
# ===============================================

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "Form Autofill API - Version Améliorée",
        "version": "2.0.0",
        "features": ["checkboxes", "radios", "selects", "levenshtein"],
        "active_sessions": len(active_sessions)
    }


@app.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """Crée une nouvelle session de navigation"""
    if request.session_id in active_sessions:
        raise HTTPException(status_code=400, detail=f"Session {request.session_id} existe déjà")
    
    try:
        driver = create_driver()
        
        if request.maximize:
            try:
                driver.maximize_window()
            except Exception:
                pass
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
        raise HTTPException(status_code=500, detail=f"Erreur création session: {str(e)}")


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Récupère les informations d'une session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} non trouvée")
    
    session = active_sessions[session_id]
    driver = session['driver']
    
    try:
        return {
            "session_id": session_id,
            "current_url": driver.current_url,
            "title": driver.title,
            "created_at": session['created_at']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/form/fill", response_model=FormFillResponse)
async def fill_form(request: FillFormRequest):
    """Remplit les formulaires sur la page actuelle"""
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} non trouvée")
    
    session = active_sessions[request.session_id]
    driver = session['driver']
    
    try:
        # Attendre les formulaires
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        except Exception:
            pass
        
        filled_fields = fill_forms(
            driver,
            provided_values=request.values,
            use_levenshtein=request.use_levenshtein,
            threshold=request.levenshtein_threshold
        )
        
        return FormFillResponse(
            success=True,
            message=f"✅ {len(filled_fields)} champ(s) rempli(s) avec succès",
            filled_fields=filled_fields
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur remplissage: {str(e)}")


@app.post("/session/{session_id}/navigate")
async def navigate(session_id: str, url: str):
    """Navigue vers une nouvelle URL"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} non trouvée")
    
    driver = active_sessions[session_id]['driver']
    
    try:
        driver.get(url)
        time.sleep(2)
        return {
            "success": True,
            "message": f"Navigation vers {url}",
            "current_url": driver.current_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur navigation: {str(e)}")


@app.get("/sessions")
async def list_sessions():
    """Liste toutes les sessions actives"""
    sessions_info = []
    for session_id, session in active_sessions.items():
        try:
            driver = session['driver']
            sessions_info.append({
                "session_id": session_id,
                "current_url": driver.current_url,
                "created_at": session['created_at']
            })
        except Exception:
            sessions_info.append({
                "session_id": session_id,
                "status": "error"
            })
    
    return {
        "total_sessions": len(active_sessions),
        "sessions": sessions_info
    }


# ===============================================
# 🚀 POINT D'ENTRÉE
# ===============================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage de l'API Form Autofill - Version Améliorée")
    print("📚 Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
