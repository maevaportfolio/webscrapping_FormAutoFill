from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
from contextlib import asynccontextmanager
import Levenshtein

app = FastAPI(title="Form Autofill API", version="1.0.0")

# Storage for active sessions
active_sessions: Dict[str, Any] = {}

# Configuration
DRIVER_PATH = r"C:\Users\HK6691\OneDrive - ENGIE\Bureau\webscraping_project\msedgedriver.exe"

# Mapping keywords -> logical fields
COMMON_FIELD_KEYWORDS = {
    'first_name': ['first', 'firstname', 'given-name', 'givenname', 'prenom', 'prénom'],
    'last_name': ['last', 'lastname', 'family-name', 'familyname', 'nom'],
    'email': ['email', 'e-mail', 'mail'],
    'phone': ['phone', 'tel', 'telephone', 'mobile'],
    'address': ['address', 'addr', 'street', 'adresse'],
    'city': ['city', 'ville'],
    'zip': ['zip', 'postal', 'postcode', 'codepostal'],
    'passport': ['passport', 'passeport', 'passport_number', 'passport_no'],
    'date_of_birth': ['birth', 'birthdate', 'dob', 'date_of_birth', 'dateofbirth', 'date_naissance', 'datenaissance'],
    'country': ['country', 'pays', 'nationality', 'nationalité'],
    'title': ['title', 'civilité', 'civility', 'mr', 'mrs', 'ms', 'mademoiselle']
}

# Default values
DEFAULT_VALUES = {
    'first_name': 'Jean',
    'last_name': 'Dupont',
    'email': 'jean.dupont@example.com',
    'phone': '+33123456789',
    'address': '1 Rue Exemple',
    'city': 'Paris',
    'zip': '75001',
    'passport': '12345678',
    'date_of_birth': '1990-01-15',
    'country': 'France',
    'title': 'Mrs.'
}


# Pydantic Models
class SessionCreateRequest(BaseModel):
    session_id: str
    url: Optional[str] = 'file:///C:/Users/HK6691/OneDrive - ENGIE/Bureau/webscraping_project/test_form1.html'
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


def detect_logical_key_levenshtein(field_name: str, threshold: float = 0.7):
    """
    Détecte le champ logique en utilisant la distance de Levenshtein.
    Retourne le champ logique avec la meilleure correspondance si le ratio est supérieur au seuil.
    """
    if not field_name:
        return None
    
    lname = field_name.lower()
    best_match = None
    best_ratio = 0.0
    best_logical = None
    
    for logical, keywords in COMMON_FIELD_KEYWORDS.items():
        for kw in keywords:
            # Calcul du ratio de similarité (1.0 = identique, 0.0 = totalement différent)
            ratio = Levenshtein.ratio(lname, kw)
            
            # Vérifier aussi si le mot clé est contenu dans le nom du champ
            if kw in lname:
                ratio = max(ratio, 0.9)  # Bonus si contenu
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = kw
                best_logical = logical
    
    # Retourner le meilleur match si supérieur au seuil
    if best_ratio >= threshold:
        return best_logical
    
    return None


def detect_logical_key(field_name: str):
    """Version originale sans Levenshtein (fallback)"""
    if not field_name:
        return None
    lname = field_name.lower()
    for logical, keywords in COMMON_FIELD_KEYWORDS.items():
        for kw in keywords:
            if kw in lname:
                return logical
    return None


def parse_date_components(date_str):
    """
    Parse une date en format YYYY-MM-DD et retourne jour, mois, année
    Exemple: '1990-01-15' -> {'day': '15', 'month': '01', 'year': '1990'}
    """
    try:
        if not date_str:
            return None
        
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            return {
                'day': day,
                'month': month,
                'year': year
            }
    except Exception:
        pass
    
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


def is_country_field(field_name):
    """Vérifie si un champ est un champ pays/nationalité"""
    if not field_name:
        return False
    name_lower = field_name.lower()
    country_keywords = ['country', 'pays', 'nationality', 'nationalité', 'nation']
    return any(kw in name_lower for kw in country_keywords)


def is_title_field(field_name):
    """Vérifie si un champ est un champ de civilité/titre"""
    if not field_name:
        return False
    name_lower = field_name.lower()
    title_keywords = ['title', 'civilité', 'civility', 'mr', 'mrs', 'ms', 'mademoiselle', 'salutation', 'salutation']
    return any(kw in name_lower for kw in title_keywords)


def get_title_option(select_element, preferred='Mrs'):
    """
    Cherche l'option de titre la plus proche du préféré.
    Cherche 'Mrs.' en priorité, puis 'Mrs', puis 'Ms'
    """
    try:
        options = select_element.find_elements(By.TAG_NAME, 'option')
        option_texts = [opt.text.strip() for opt in options]
        
        # Chercher 'Mrs.' (avec point) en priorité - exact match
        for text in option_texts:
            if text == 'Mrs.':
                return text
        
        # Puis chercher 'Mrs' sans point
        for text in option_texts:
            text_lower = text.lower()
            if text_lower == 'mrs' or text_lower == 'mrs.':
                return text
        
        # Puis chercher 'Madame' ou 'Mme'
        for text in option_texts:
            text_lower = text.lower()
            if text_lower in ['madame', 'mme', 'mme.']:
                return text
        
        # Puis chercher 'Ms' ou 'Mademoiselle'
        for text in option_texts:
            text_lower = text.lower()
            if text_lower in ['ms', 'ms.', 'mademoiselle', 'mlle']:
                return text
        
        # Si rien trouvé, retourner la deuxième option (généralement après Mr)
        if len(option_texts) > 1:
            return option_texts[1]
        
        return None
    except Exception:
        return None


def find_closest_option(select_element, search_text, threshold=0.6):
    """
    Cherche l'option la plus proche du texte recherché avec Levenshtein.
    Retourne l'option si le ratio est supérieur au seuil.
    """
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
            # Vérifier si c'est une correspondance exacte
            if text_lower == search_lower:
                return text
            
            # Sinon calculer Levenshtein ratio
            ratio = Levenshtein.ratio(search_lower, text_lower)
            
            # Bonus si le texte recherché est contenu dans l'option
            if search_lower in text_lower or text_lower in search_lower:
                ratio = max(ratio, 0.75)
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = text
        
        # Retourner seulement si le ratio est assez élevé
        if best_ratio >= threshold:
            return best_match
        
        return None
    except Exception:
        return None


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


def fill_forms(driver, provided_values=None, use_levenshtein=True, threshold=0.7):
    """
    Remplit automatiquement les formulaires détectés.
    Retourne la liste des champs remplis.
    """
    if provided_values is None:
        provided_values = {}
    
    filled_fields = []
    
    # Choisir la fonction de détection appropriée
    detect_fn = detect_logical_key_levenshtein if use_levenshtein else detect_logical_key
    
    def choose_value(logical_key):
        if logical_key in provided_values:
            return provided_values[logical_key]
        return DEFAULT_VALUES.get(logical_key, '')
    
    forms = driver.find_elements(By.TAG_NAME, 'form')
    
    for i, form in enumerate(forms):
        print(f'Formulaire {i+1}')
        
        # Inputs
        for inp in form.find_elements(By.TAG_NAME, 'input'):
            try:
                if not (inp.is_displayed() and inp.is_enabled()):
                    continue
                
                itype = (inp.get_attribute('type') or '').lower()
                realname = inp.get_attribute('name') or inp.get_attribute('id') or inp.get_attribute('placeholder')
                
                if use_levenshtein:
                    logical = detect_logical_key_levenshtein(realname, threshold)
                else:
                    logical = detect_logical_key(realname)
                
                if itype in ['submit', 'button', 'hidden', 'image', 'reset']:
                    continue
                
                # Checkboxes / radios
                if itype in ['checkbox', 'radio']:
                    val = None
                    if logical:
                        val = provided_values.get(logical)
                    if val is None and realname:
                        val = provided_values.get(realname)
                    if val is None:
                        val = choose_value(logical)
                    
                    if isinstance(val, str):
                        vlow = val.lower()
                        truthy = vlow in ['y', 'yes', '1', 'true', 'on']
                    else:
                        truthy = bool(val)
                    
                    try:
                        if truthy and not inp.is_selected():
                            inp.click()
                            filled_fields.append({
                                'type': itype,
                                'name': realname,
                                'logical': logical,
                                'value': val
                            })
                    except Exception:
                        pass
                    continue
                
                # Autres types d'input
                value = None
                if realname and realname in provided_values:
                    value = provided_values[realname]
                if value is None and logical:
                    value = provided_values.get(logical)
                if value is None:
                    value = choose_value(logical)
                
                if value is not None:
                    try:
                        inp.clear()
                    except Exception:
                        pass
                    try:
                        # Gestion spéciale pour les champs de date texte (departure-date, return-date)
                        if is_date_text_field(realname):
                            # Chercher la date correspondante
                            if 'departure' in realname.lower() or 'depart' in realname.lower() or 'outbound' in realname.lower():
                                date_value = provided_values.get('departure_date', DEFAULT_VALUES.get('departure_date', ''))
                                if date_value:
                                    inp.send_keys(date_value)
                                    filled_fields.append({
                                        'type': itype,
                                        'name': realname,
                                        'logical': logical,
                                        'value': date_value
                                    })
                                    print(f"  Rempli {realname} (date départ) avec '{date_value}'")
                            elif 'return' in realname.lower() or 'retour' in realname.lower() or 'inbound' in realname.lower():
                                date_value = provided_values.get('return_date', DEFAULT_VALUES.get('return_date', ''))
                                if date_value:
                                    inp.send_keys(date_value)
                                    filled_fields.append({
                                        'type': itype,
                                        'name': realname,
                                        'logical': logical,
                                        'value': date_value
                                    })
                                    print(f"  Rempli {realname} (date retour) avec '{date_value}'")
                        
                        # Gestion des champs jour/mois/année séparés
                        elif is_day_field(realname):
                            # Extraire le jour
                            date_value = provided_values.get('date_of_birth', DEFAULT_VALUES.get('date_of_birth', ''))
                            date_parts = parse_date_components(date_value)
                            if date_parts:
                                inp.send_keys(date_parts['day'])
                                filled_fields.append({
                                    'type': itype,
                                    'name': realname,
                                    'logical': logical,
                                    'value': date_parts['day']
                                })
                                print(f"  Rempli {realname} (jour) avec '{date_parts['day']}'")
                        
                        elif is_month_field(realname):
                            # Extraire le mois
                            date_value = provided_values.get('date_of_birth', DEFAULT_VALUES.get('date_of_birth', ''))
                            date_parts = parse_date_components(date_value)
                            if date_parts:
                                inp.send_keys(date_parts['month'])
                                filled_fields.append({
                                    'type': itype,
                                    'name': realname,
                                    'logical': logical,
                                    'value': date_parts['month']
                                })
                                print(f"  Rempli {realname} (mois) avec '{date_parts['month']}'")
                        
                        elif is_year_field(realname):
                            # Extraire l'année
                            date_value = provided_values.get('date_of_birth', DEFAULT_VALUES.get('date_of_birth', ''))
                            date_parts = parse_date_components(date_value)
                            if date_parts:
                                inp.send_keys(date_parts['year'])
                                filled_fields.append({
                                    'type': itype,
                                    'name': realname,
                                    'logical': logical,
                                    'value': date_parts['year']
                                })
                                print(f"  Rempli {realname} (année) avec '{date_parts['year']}'")
                        
                        # Gestion standard pour les autres types
                        else:
                            inp.send_keys(value)
                            filled_fields.append({
                                'type': itype,
                                'name': realname,
                                'logical': logical,
                                'value': value
                            })
                            print(f"  Rempli {realname} (type={itype}) avec '{value}'")
                    except Exception as e:
                        print(f'Erreur en remplissant input: {e}')
            
            except Exception as e:
                print(f'err input: {e}')
        
        # Textareas
        for ta in form.find_elements(By.TAG_NAME, 'textarea'):
            try:
                if not (ta.is_displayed() and ta.is_enabled()):
                    continue
                
                realname = ta.get_attribute('name') or ta.get_attribute('id')
                
                if use_levenshtein:
                    logical = detect_logical_key_levenshtein(realname, threshold)
                else:
                    logical = detect_logical_key(realname)
                
                value = None
                if realname and realname in provided_values:
                    value = provided_values[realname]
                if value is None and logical:
                    value = provided_values.get(logical)
                if value is None:
                    value = choose_value(logical)
                
                if value is not None:
                    try:
                        ta.clear()
                    except Exception:
                        pass
                    ta.send_keys(value)
                    filled_fields.append({
                        'type': 'textarea',
                        'name': realname,
                        'logical': logical,
                        'value': value
                    })
                    print(f"  Rempli textarea {realname} avec '{value}'")
            
            except Exception as e:
                print(f'err textarea: {e}')
        
        # Selects
        for sel_elem in form.find_elements(By.TAG_NAME, 'select'):
            try:
                sel = Select(sel_elem)
                realname = sel_elem.get_attribute('name') or sel_elem.get_attribute('id')
                
                if use_levenshtein:
                    logical = detect_logical_key_levenshtein(realname, threshold)
                else:
                    logical = detect_logical_key(realname)
                
                # Gestion spéciale pour les champs de titre/civilité
                if is_title_field(realname) or (logical and 'title' in str(logical).lower()):
                    title_opt = get_title_option(sel_elem)
                    if title_opt:
                        try:
                            sel.select_by_visible_text(title_opt)
                            filled_fields.append({
                                'type': 'select',
                                'name': realname,
                                'logical': logical,
                                'value': title_opt
                            })
                            print(f"  Select {realname} (Titre) -> {title_opt}")
                        except Exception as e:
                            print(f'  Erreur sélection titre: {e}')
                    continue
                
                # Gestion spéciale pour les champs pays/nationalité
                if is_country_field(realname):
                    country_opt = 'France'
                    try:
                        sel.select_by_visible_text(country_opt)
                        filled_fields.append({
                            'type': 'select',
                            'name': realname,
                            'logical': logical,
                            'value': country_opt
                        })
                        print(f"  Select {realname} (Pays) -> {country_opt}")
                    except Exception:
                        # Essayer par valeur
                        try:
                            sel.select_by_value('FR')
                            filled_fields.append({
                                'type': 'select',
                                'name': realname,
                                'logical': logical,
                                'value': 'FR'
                            })
                            print(f"  Select {realname} (Pays) -> FR")
                        except Exception:
                            print(f'  Option France/FR non trouvée')
                    continue
                
                # Sélection normale avec Levenshtein si nécessaire
                opt = None
                if realname and realname in provided_values:
                    opt = provided_values[realname]
                if opt is None and logical:
                    opt = provided_values.get(logical)
                if opt is None:
                    opt = choose_value(logical)
                
                if opt is not None:
                    selected = False
                    
                    # 1. Essayer par texte exact
                    try:
                        sel.select_by_visible_text(opt)
                        filled_fields.append({
                            'type': 'select',
                            'name': realname,
                            'logical': logical,
                            'value': opt
                        })
                        print(f"  Select {realname} -> {opt}")
                        selected = True
                    except Exception:
                        pass
                    
                    # 2. Essayer par valeur exacte
                    if not selected:
                        try:
                            sel.select_by_value(opt)
                            filled_fields.append({
                                'type': 'select',
                                'name': realname,
                                'logical': logical,
                                'value': opt
                            })
                            selected = True
                        except Exception:
                            pass
                    
                    # 3. Essayer par index
                    if not selected:
                        try:
                            sel.select_by_index(int(opt))
                            filled_fields.append({
                                'type': 'select',
                                'name': realname,
                                'logical': logical,
                                'value': opt
                            })
                            selected = True
                        except Exception:
                            pass
                    
                    # 4. Essayer avec Levenshtein pour trouver l'option la plus proche
                    if not selected and use_levenshtein:
                        closest_opt = find_closest_option(sel_elem, opt, threshold=0.6)
                        if closest_opt:
                            try:
                                sel.select_by_visible_text(closest_opt)
                                filled_fields.append({
                                    'type': 'select',
                                    'name': realname,
                                    'logical': logical,
                                    'value': closest_opt
                                })
                                print(f"  Select {realname} -> {closest_opt} (approx de '{opt}')")
                                selected = True
                            except Exception:
                                pass
                    
                    if not selected:
                        print(f'  Option non trouvée: {opt}')
            
            except Exception as e:
                print(f'err select: {e}')
    
    return filled_fields


# API Endpoints

@app.get("/")
async def root():
    """Endpoint racine pour vérifier que l'API fonctionne"""
    return {
        "message": "Form Autofill API is running",
        "version": "1.0.0",
        "active_sessions": len(active_sessions)
    }


@app.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """
    POST - Crée une nouvelle session de navigation
    """
    if request.session_id in active_sessions:
        raise HTTPException(status_code=400, detail=f"Session {request.session_id} already exists")
    
    try:
        driver = create_driver()
        
        # Configuration de la fenêtre
        try:
            if request.maximize:
                driver.maximize_window()
            elif request.width and request.height:
                driver.set_window_size(request.width, request.height)
        except Exception as e:
            print(f"Window configuration error: {e}")
        
        # Naviguer vers l'URL
        driver.get(request.url)
        
        # Attendre que la page charge
        time.sleep(2)
        
        # Stocker la session
        active_sessions[request.session_id] = {
            'driver': driver,
            'url': request.url,
            'created_at': time.time()
        }
        
        return SessionResponse(
            success=True,
            message=f"Session {request.session_id} created successfully",
            session_id=request.session_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    GET - Récupère les informations d'une session
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session = active_sessions[session_id]
    driver = session['driver']
    
    try:
        current_url = driver.current_url
        title = driver.title
        
        return {
            "session_id": session_id,
            "current_url": current_url,
            "title": title,
            "created_at": session['created_at']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session info: {str(e)}")


@app.post("/form/fill", response_model=FormFillResponse)
async def fill_form(request: FillFormRequest):
    """
    POST - Remplit les formulaires sur la page actuelle
    """
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    session = active_sessions[request.session_id]
    driver = session['driver']
    
    try:
        # Attendre que les formulaires soient présents
        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        except Exception:
            pass
        
        # Remplir les formulaires
        filled_fields = fill_forms(
            driver,
            provided_values=request.values,
            use_levenshtein=request.use_levenshtein,
            threshold=request.levenshtein_threshold
        )
        
        return FormFillResponse(
            success=True,
            message=f"Successfully filled {len(filled_fields)} fields",
            filled_fields=filled_fields
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filling form: {str(e)}")


@app.post("/session/{session_id}/navigate")
async def navigate(session_id: str, url: str):
    """
    POST - Navigue vers une nouvelle URL dans la session
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session = active_sessions[session_id]
    driver = session['driver']
    
    try:
        driver.get(url)
        time.sleep(2)
        
        return {
            "success": True,
            "message": f"Navigated to {url}",
            "current_url": driver.current_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error navigating: {str(e)}")


@app.get("/session/{session_id}/screenshot")
async def get_screenshot(session_id: str):
    """
    GET - Endpoint supprimé (screenshots désactivés)
    """
    raise HTTPException(status_code=404, detail="Screenshot endpoint has been removed")



@app.delete("/session/{session_id}")
async def close_session(session_id: str):
    """
    DELETE - Ferme et supprime une session (Endpoint supprimé - sessions restent ouvertes)
    """
    raise HTTPException(status_code=404, detail="Session close endpoint has been removed. Sessions remain open for manual navigation.")


@app.get("/sessions")
async def list_sessions():
    """
    GET - Liste toutes les sessions actives
    """
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
