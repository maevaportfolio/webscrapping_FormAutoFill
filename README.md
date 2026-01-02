# 📋 Form Autofill API - Documentation Complète

Télécharger le msedgedriver à partir du lien et le mettre dans le dossier du projet : "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/?form=MA13LH"

## 📖 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation & Démarrage](#installation--démarrage)
4. [API Endpoints](#api-endpoints)
5. [Détection des champs](#détection-des-champs)
6. [Distance Levenshtein](#distance-levenshtein)
7. [Remplissage des formulaires](#remplissage-des-formulaires)
8. [Gestion des types de champs](#gestion-des-types-de-champs)
9. [Exemple complet](#exemple-complet)

---

## 🎯 Vue d'ensemble

**Form Autofill API** est une API FastAPI qui automatise le remplissage de formulaires web en utilisant Selenium. Elle :

- ✅ Crée des sessions de navigateur (Edge)
- ✅ Détecte automatiquement les champs de formulaire
- ✅ Remplit les champs avec des valeurs intelligentes
- ✅ Gère les menus déroulants (selects)
- ✅ Traite les dates (jour/mois/année séparé)
- ✅ Reste ouvert pour navigation manuelle
- ✅ Détecte automatiquement les changements de page

---

## 🏗️ Architecture

### Structure des fichiers

```
webscraping_project/
├── api_form_autofill.py       # API principale (FastAPI)
├── test_simple.py             # Client de test/surveillance
├── msedgedriver.exe           # Driver Selenium Edge
└── requirements.txt           # Dépendances Python
```

### Composants principaux

| Composant | Rôle |
|-----------|------|
| **FastAPI Server** | API REST qui gère les sessions et remplissage |
| **Selenium WebDriver** | Contrôle le navigateur Edge |
| **Levenshtein Distance** | Compare les strings pour détecter les champs |
| **Client de test** | Surveille les changements de page et déclenche le remplissage |

---

## 🚀 Installation & Démarrage

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
# Contient: selenium, fastapi, uvicorn, python-Levenshtein, webdriver-manager
```

### 2. Démarrer l'API

```bash
# Terminal 1 - API
python api_form_autofill.py
# Ou avec uvicorn
uvicorn api_form_autofill:app --reload
```

L'API démarre sur `http://localhost:8000`

### 3. Lancer le test

```bash
# Terminal 2 - Client
python test_simple.py
```

---

## 📡 API Endpoints

### 1️⃣ POST `/session/create` - Créer une session

**À quoi ça sert ?** Démarre un **nouveau navigateur Edge** et le garde **ouvert en arrière-plan**. C'est la première étape obligatoire.

#### 🔍 Ce que fait vraiment cette fonction

1. **Crée un nouveau WebDriver Edge** (`webdriver.Edge()`)
2. **Lance une instance du navigateur Edge** (tu la vois apparaître)
3. **Charge la page** à l'URL spécifiée
4. **Enregistre la session** dans le dictionnaire `active_sessions`
5. **Retient le driver** pour l'utiliser dans d'autres appels

#### Pourquoi c'est important

Sans cette étape, tu n'as pas de navigateur à contrôler ! L'API a besoin d'une **référence au driver** pour pouvoir faire les actions suivantes (remplir, naviguer, etc).

#### Request

```json
{
  "session_id": "test_session",
  "url": "https://www.airarabia.com/en",
  "maximize": true,
  "width": null,
  "height": null
}
```

#### Response

```json
{
  "success": true,
  "message": "Session test_session created successfully",
  "session_id": "test_session"
}
```

#### Paramètres détaillés

| Param | Type | Requis | Description | Exemple |
|-------|------|--------|-------------|---------|
| `session_id` | string | ✅ | Identifiant unique - tu l'utilises pour les appels suivants | `"session_1"`, `"user_123"` |
| `url` | string | ❌ | URL à charger (défaut: `test_form1.html`) | `"https://example.com"` |
| `maximize` | bool | ❌ | Maximiser la fenêtre (défaut: `true`) | `true` / `false` |
| `width` | int | ❌ | Largeur personnalisée en pixels (défaut: null=auto) | `1920` |
| `height` | int | ❌ | Hauteur personnalisée en pixels (défaut: null=auto) | `1080` |

#### Code backend (ce qui se passe)

```python
@app.post("/session/create")
async def create_session(request_body: dict):
    """
    Étape 1: Créer et configurer le driver
    """
    session_id = request_body.get('session_id')
    url = request_body.get('url', 'test_form1.html')
    
    # Créer une instance du navigateur Edge
    driver = create_driver()
    
    # Charger la page
    driver.get(url)
    
    # Enregistrer pour usage futur
    active_sessions[session_id] = {
        'driver': driver,
        'current_url': url,
        'created_at': time.time()
    }
    
    return {"success": True, "session_id": session_id}
```

#### Exemple d'utilisation

```python
import requests

response = requests.post("http://localhost:8000/session/create", json={
    "session_id": "session_1",
    "url": "https://www.airarabia.com/en",
    "maximize": True
})

print(response.json())
# {'success': True, 'message': 'Session session_1 created successfully', 'session_id': 'session_1'}
```

**À ce moment :** Une fenêtre Edge s'ouvre et charge airarabia.com ✅

---

### 2️⃣ GET `/session/{session_id}` - Récupérer info session

**À quoi ça sert ?** Vérifier où on en est actuellement dans le navigateur. C'est utilisé pour **déterminer si on a changé de page**.

#### 🔍 Ce que fait vraiment cette fonction

1. **Récupère le driver** de la session stockée
2. **Récupère l'URL actuelle** du navigateur (`driver.current_url`)
3. **Récupère le titre de la page** (`driver.title`)
4. **Retourne ces infos** pour qu'on sache où on est

#### Pourquoi c'est important

Tu **dois savoir quand la page a changé** pour remplir les nouveaux formulaires. Par exemple :
- Page 1 : https://example.com/form → Remplir
- Utilisateur clique sur "Suivant"
- Page 2 : https://example.com/confirmation → Remplir cette nouvelle page aussi !

Sans ce GET, tu ne saurais pas qu'il y a une nouvelle page à remplir.

#### Request

```
GET /session/test_session
```

#### Response

```json
{
  "session_id": "test_session",
  "current_url": "https://www.airarabia.com/en",
  "title": "AirArabia",
  "created_at": 1703431200.123456
}
```

#### Code backend

```python
@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Récupérer l'état actuel du navigateur
    """
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    driver = active_sessions[session_id]['driver']
    
    return {
        "session_id": session_id,
        "current_url": driver.current_url,      # ← URL actuelle
        "title": driver.title,                   # ← Titre de la page
        "created_at": active_sessions[session_id]['created_at']
    }
```

#### Exemple d'utilisation

```python
# Vérifier où on est maintenant
response = requests.get("http://localhost:8000/session/session_1")
data = response.json()

print(f"URL actuelle: {data['current_url']}")
# URL actuelle: https://www.airarabia.com/en

print(f"Titre: {data['title']}")
# Titre: AirArabia
```

#### Cas d'usage : Détection de changement de page

```python
last_url = "https://www.airarabia.com/en"

while True:
    response = requests.get("http://localhost:8000/session/session_1")
    current_url = response.json()['current_url']
    
    if current_url != last_url:
        print(f"🚀 Page changée ! {last_url} → {current_url}")
        # Remplir la nouvelle page
        remplir_formulaire(session_1)
        last_url = current_url
    
    time.sleep(3)
```

---

### 3️⃣ POST `/form/fill` - Remplir les formulaires

**À quoi ça sert ?** L'action principale : **trouver et remplir TOUS les champs du formulaire** avec les valeurs intelligentes.

#### 🔍 Ce que fait vraiment cette fonction

```
1. Récupérer le driver de la session
2. Chercher TOUS les <form> sur la page
3. Pour chaque formulaire:
   └─ Pour chaque <input>, <textarea>, <select>:
      ├─ Vérifier que c'est visible et activé
      ├─ Déterminer le type de champ (texte, date, select, etc)
      ├─ Détecter le champ logique (first_name, email, etc)
      ├─ Récupérer la valeur à remplir
      └─ Remplir le champ
4. Enregistrer tous les champs remplis
5. Retourner le résumé
```

#### Pourquoi c'est important

C'est la **fonction principale** qui fait tout le travail d'automatisation. Sans elle, les formulaires ne sont pas remplis !

#### Request

```json
{
  "session_id": "test_session",
  "values": {
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean@example.com",
    "phone": "+33123456789",
    "address": "1 Rue Exemple",
    "city": "Paris",
    "zip": "75001",
    "passport": "12345678",
    "date_of_birth": "1990-01-15",
    "country": "France",
    "title": "Mrs."
  },
  "use_levenshtein": true,
  "levenshtein_threshold": 0.7
}
```

#### Response

```json
{
  "success": true,
  "message": "Successfully filled 8 fields",
  "filled_fields": [
    {
      "type": "text",
      "name": "first_name_field",
      "logical": "first_name",
      "value": "Jean"
    },
    {
      "type": "email",
      "name": "customer_email",
      "logical": "email",
      "value": "jean@example.com"
    },
    {
      "type": "select",
      "name": "title_select",
      "logical": "title",
      "value": "Mrs."
    },
    {
      "type": "select",
      "name": "country_dropdown",
      "logical": "country",
      "value": "France"
    },
    {
      "type": "day",
      "name": "day_field",
      "logical": "date_of_birth",
      "value": "15"
    },
    {
      "type": "month",
      "name": "month_field",
      "logical": "date_of_birth",
      "value": "01"
    },
    {
      "type": "year",
      "name": "year_field",
      "logical": "date_of_birth",
      "value": "1990"
    }
  ]
}
```

#### Paramètres détaillés

| Param | Type | Requis | Description | Exemple |
|-------|------|--------|-------------|---------|
| `session_id` | string | ✅ | ID de la session | `"session_1"` |
| `values` | dict | ❌ | Les valeurs à remplir (défaut: utiliser `DEFAULT_VALUES`) | `{"first_name": "Jean", ...}` |
| `use_levenshtein` | bool | ❌ | Utiliser la distance Levenshtein pour match approx (défaut: `true`) | `true` / `false` |
| `levenshtein_threshold` | float | ❌ | Seuil de similarité 0.0-1.0 (défaut: `0.7`) | `0.6`, `0.8` |

#### Le seuil Levenshtein (très important !)

```
threshold = 0.9  → Très strict (doit matcher à 90%)
                    - Acepte: "email" → "email" ✅
                    - Rejette: "email" → "e_mail" ❌

threshold = 0.7  → Normal (doit matcher à 70%) [DÉFAUT]
                    - Accepte: "email" → "email" ✅
                    - Accepte: "email" → "e_mail" ✅
                    - Rejette: "email" → "xyz" ❌

threshold = 0.5  → Permissif (doit matcher à 50%)
                    - Accepte: "email" → "mail" ✅
                    - Accepte: "email" → "contact" ✅
```

#### Code backend simplifié

```python
@app.post("/form/fill")
async def fill_forms(request_body: dict):
    """
    Remplir TOUS les formulaires trouvés sur la page
    """
    session_id = request_body.get('session_id')
    provided_values = request_body.get('values', {})
    use_levenshtein = request_body.get('use_levenshtein', True)
    threshold = request_body.get('levenshtein_threshold', 0.7)
    
    # Récupérer le driver
    driver = active_sessions[session_id]['driver']
    
    filled_fields = []
    
    # ÉTAPE 1: Trouver tous les formulaires
    forms = driver.find_elements(By.TAG_NAME, 'form')
    
    for form in forms:
        # ÉTAPE 2: Traiter les inputs
        for inp in form.find_elements(By.TAG_NAME, 'input'):
            # Vérifier que visible et activé
            if not (inp.is_displayed() and inp.is_enabled()):
                continue
            
            # ÉTAPE 3: Détecter le champ logique
            realname = inp.get_attribute('name')
            input_type = inp.get_attribute('type') or 'text'
            
            logical = detect_logical_key_levenshtein(realname, threshold)
            
            # ÉTAPE 4: Récupérer la valeur
            value = provided_values.get(logical) or DEFAULT_VALUES.get(logical)
            
            # ÉTAPE 5: Remplir
            if value:
                inp.send_keys(value)
                filled_fields.append({
                    "type": input_type,
                    "name": realname,
                    "logical": logical,
                    "value": value
                })
        
        # ÉTAPE 2b: Traiter les selects
        for sel in form.find_elements(By.TAG_NAME, 'select'):
            # ... (même processus mais avec select logic)
    
    return {
        "success": True,
        "message": f"Successfully filled {len(filled_fields)} fields",
        "filled_fields": filled_fields
    }
```

#### Exemple d'utilisation

```python
response = requests.post("http://localhost:8000/form/fill", json={
    "session_id": "session_1",
    "values": {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean@example.com"
    },
    "levenshtein_threshold": 0.7
})

result = response.json()
print(f"Champs remplis: {len(result['filled_fields'])}")
for field in result['filled_fields']:
    print(f"  - {field['name']} ({field['type']}) = {field['value']}")
```

#### Résultat

```
Champs remplis: 10
  - customer_first_name (text) = Jean
  - customer_last_name (text) = Dupont
  - contact_email (email) = jean@example.com
  - user_title (select) = Mrs.
  - nationality (select) = France
  - birth_day (text) = 15
  - birth_month (text) = 01
  - birth_year (text) = 1990
  - user_address (textarea) = 1 Rue Exemple
```

---

### 4️⃣ POST `/session/{session_id}/navigate` - Naviguer

**À quoi ça sert ?** Faire naviguer le navigateur vers une **nouvelle URL sans fermer la session**.

#### 🔍 Ce que fait vraiment cette fonction

1. **Récupère le driver** de la session
2. **Appelle `driver.get(nouvelle_url)`** pour charger la page
3. **Met à jour l'URL** dans les informations de session
4. **Retourne la confirmation**

#### Pourquoi c'est important

Si tu veux que l'utilisateur navigue vers une autre page, tu peux appeler ce endpoint au lieu de fermer et recréer une session. La session reste **ouverte et conserve tous les cookies/données**.

#### Request

```
POST /session/test_session/navigate?url=https://example.com
```

Ou avec JSON :

```json
{
  "url": "https://example.com"
}
```

#### Response

```json
{
  "success": true,
  "message": "Navigated to https://example.com",
  "current_url": "https://example.com"
}
```

#### Code backend

```python
@app.post("/session/{session_id}/navigate")
async def navigate_session(session_id: str, url: str = None, request_body: dict = None):
    """
    Naviguer vers une nouvelle URL dans la session
    """
    if session_id not in active_sessions:
        return {"error": "Session not found"}
    
    # Récupérer l'URL
    if url is None and request_body:
        url = request_body.get('url')
    
    driver = active_sessions[session_id]['driver']
    
    # Naviguer
    driver.get(url)
    
    # Mettre à jour
    active_sessions[session_id]['current_url'] = url
    
    return {
        "success": True,
        "message": f"Navigated to {url}",
        "current_url": driver.current_url
    }
```

#### Exemple d'utilisation

```python
# L'utilisateur a fini avec la page 1
# On le fait aller à la page 2

response = requests.post("http://localhost:8000/session/session_1/navigate", json={
    "url": "https://www.airarabia.com/en/checkout"
})

print(response.json())
# {'success': True, 'message': 'Navigated to https://www.airarabia.com/en/checkout', 
#  'current_url': 'https://www.airarabia.com/en/checkout'}
```

#### Différence : Navigate vs New Session

```
🔴 Créer nouvelle session:
   - Nouvelle fenêtre Edge
   - Pas de cookies de session précédente
   - Plus lent

✅ Navigate dans session existante:
   - Même fenêtre Edge
   - Conserve les cookies
   - Plus rapide
   - Idéal pour naviguer dans un site sans perdre l'état
```

---

### 5️⃣ GET `/sessions` - Lister les sessions

**À quoi ça sert ?** Voir **toutes les sessions actuellement actives** et leurs états.

#### 🔍 Ce que fait vraiment cette fonction

1. **Parcourt le dictionnaire `active_sessions`**
2. **Pour chaque session, récupère :**
   - L'ID de session
   - L'URL actuelle du navigateur
   - La date de création
3. **Retourne la liste**

#### Pourquoi c'est important

Si tu as plusieurs navigateurs ouverts, tu peux voir :
- Lesquels sont actifs
- Sur quelle page ils sont
- Depuis quand ils existent

C'est utile pour **gérer plusieurs sessions en parallèle**.

#### Request

```
GET /sessions
```

#### Response

```json
{
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "session1",
      "current_url": "https://example.com",
      "created_at": 1703431200.123
    },
    {
      "session_id": "session2",
      "current_url": "https://airarabia.com",
      "created_at": 1703431250.456
    }
  ]
}
```

#### Code backend

```python
@app.get("/sessions")
async def list_sessions():
    """
    Lister toutes les sessions actives
    """
    sessions = []
    
    for session_id, session_data in active_sessions.items():
        driver = session_data['driver']
        
        sessions.append({
            "session_id": session_id,
            "current_url": driver.current_url,
            "created_at": session_data['created_at']
        })
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }
```

#### Exemple d'utilisation

```python
response = requests.get("http://localhost:8000/sessions")
data = response.json()

print(f"Sessions actives: {data['total_sessions']}")
for session in data['sessions']:
    print(f"  - {session['session_id']}: {session['current_url']}")
```

#### Résultat

```
Sessions actives: 2
  - session1: https://example.com
  - session2: https://airarabia.com
```

---

## 🔍 Détection des champs

### ❓ RÉPONSE À TA QUESTION : On utilise quoi pour le mapping ?

**TL;DR (résumé rapide) :**

```
POUR LE MAPPING : ON UTILISE LES DEUX ENSEMBLE !

1️⃣ La LISTE DE MOTS CLÉS (keywords) → QUOI chercher
   COMMON_FIELD_KEYWORDS['first_name'] = ['first', 'firstname', ...]
                                          ^^^^^^^
                                          Les patterns à chercher

2️⃣ LEVENSHTEIN → COMMENT chercher (avec intelligence)
   Si "first" n'est pas trouvé EXACTEMENT,
   on utilise Levenshtein pour dire: "fname" ressemble à 75% à "first"
```

**Analogie :** 
- Les **mots clés** = Les adresses des maisons que tu cherches
- **Levenshtein** = Le GPS qui t'aide si l'adresse est mal écrite

---

### Explication étape par étape : QUI FAIT QUOI ?

#### ÉTAPE 1: Récupérer un champ HTML

```html
Tu reçois ce champ:
<input name="fname" type="text">
```

La question: **"C'est quel champ logique ? first_name ? email ?"**

#### ÉTAPE 2: Les mots clés te disent QUOI chercher

```python
COMMON_FIELD_KEYWORDS = {
    'first_name': ['first', 'firstname', 'given-name', ...],  ← Chercher ces mots
    'email': ['email', 'e-mail', 'mail', ...],               ← Ou ces mots
    'phone': ['phone', 'tel', 'telephone', ...],             ← Ou ces mots
}
```

**Pour "fname", tu cherches :**
- Y a-t-il "first" dans "fname" ? ❌ NON
- Y a-t-il "firstname" dans "fname" ? ❌ NON
- Y a-t-il "given-name" dans "fname" ? ❌ NON
- → Les mots clés n'ont pas trouvé de match EXACT

#### ÉTAPE 3: Levenshtein prend le relais (match APPROX)

Maintenant qu'on sait qu'il n'y a pas de match exact, Levenshtein dit:

```
"fname" ressemble combien à "first" ?
Levenshtein.ratio("fname", "first") = 0.75 (75% similaire)

Est-ce que 0.75 >= seuil 0.7 ? ✅ OUI !
Donc c'est "first_name" !
```

#### RÉSULTAT FINAL

```
HTML Input: <input name="fname">
↓
Mots clés: pas de match exact
↓
Levenshtein: 75% similaire à "first"
↓
Détecté comme: "first_name" ✅
↓
Valeur utilisée: DEFAULT_VALUES['first_name'] = "Jean"
↓
Action: input.send_keys("Jean")
```

---

### Concept : Champ logique vs Champ HTML

**Le problème :** Chaque site nomme les champs différemment !

```html
Site 1: <input name="first_name">
Site 2: <input name="customer_first_name">
Site 3: <input name="fname">
Site 4: <input name="user_firstname">
```

**La solution :** Détecter le **concept** (first_name) peu importe le **nom HTML**.

### Système de mapping avec keywords

L'API utilise un **dictionnaire de keywords** pour identifier les champs logiques :

```python
COMMON_FIELD_KEYWORDS = {
    'first_name': ['first', 'firstname', 'given-name', 'givenname', 'prenom', 'prénom'],
    'last_name': ['last', 'lastname', 'family-name', 'familyname', 'nom'],
    'email': ['email', 'e-mail', 'mail'],
    'phone': ['phone', 'tel', 'telephone', 'mobile'],
    'address': ['address', 'addr', 'street', 'adresse'],
    'city': ['city', 'ville'],
    'zip': ['zip', 'postal', 'postcode', 'codepostal'],
    'passport': ['passport', 'passeport', 'passport_number', 'passport_no'],
    'date_of_birth': ['birth', 'birthdate', 'dob', 'date_of_birth', 'dateofbirth', 'date_naissance'],
    'country': ['country', 'pays', 'nationality', 'nationalité'],
    'title': ['title', 'civilité', 'civility', 'mr', 'mrs', 'ms', 'mademoiselle']
}

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
```

### Processus de détection COMPLET

```
ÉTAPE 1 : Récupérer le nom HTML du champ
          ↓
          name="customer_first_name"

ÉTAPE 2 : Convertir en minuscules
          ↓
          "customer_first_name"

ÉTAPE 3 : Pour chaque champ logique (first_name, email, etc):
          ├─ Pour chaque keyword du champ:
          │  ├─ Chercher: "first" IN "customer_first_name"? ✅
          │  └─ Calculer similarité avec Levenshtein
          └─ Garder le meilleur match

ÉTAPE 4 : Vérifier que la similarité > seuil (0.7)
          ✅ Match trouvé: "first_name"

ÉTAPE 5 : Récupérer la valeur par défaut
          ↓
          DEFAULT_VALUES['first_name'] = 'Jean'

ÉTAPE 6 : Remplir le champ avec la valeur
          ↓
          input.send_keys('Jean') ✅
```

### La fonction de détection

```python
def detect_logical_key_levenshtein(field_name, threshold=0.7):
    """
    Détecte le champ logique à partir du nom HTML
    
    Parameters:
        field_name (str): Le name/id du champ HTML
        threshold (float): Seuil de similarité minimum (0-1)
    
    Returns:
        str: Le champ logique (first_name, email, etc) ou None
    """
    field_name_lower = field_name.lower()
    best_ratio = 0.0
    best_logical = None
    
    # Parcourir tous les champs logiques
    for logical, keywords in COMMON_FIELD_KEYWORDS.items():
        for kw in keywords:
            # TECHNIQUE 1: Chercher le keyword dans le nom
            if kw in field_name_lower:
                # BONUS: Si le keyword est dans le nom, score élevé
                ratio = 0.95  # Très haut car c'est une correspondance contenue
            else:
                # TECHNIQUE 2: Calculer la similarité Levenshtein
                ratio = Levenshtein.ratio(field_name_lower, kw)
            
            # Garder le meilleur match
            if ratio > best_ratio:
                best_ratio = ratio
                best_logical = logical
    
    # Ne retourner que si > seuil
    if best_ratio >= threshold:
        return best_logical
    
    return None
```

### Exemples concrets

#### Exemple 1 : Match exact par contenance

```html
<input name="customer_first_name" type="text">
```

**Détection :**
```
1. field_name = "customer_first_name"
2. Chercher "first" in "customer_first_name" ? ✅ OUI
3. Bonus: ratio = 0.95
4. Champ logique: "first_name"
5. Valeur: "Jean" ✓
```

#### Exemple 2 : Match partiel avec Levenshtein

```html
<input name="usr_email_xyz" type="email">
```

**Détection :**
```
1. field_name = "usr_email_xyz"
2. Chercher "email" in "usr_email_xyz" ? ✅ OUI
3. Bonus: ratio = 0.95
4. Champ logique: "email"
5. Valeur: "jean.dupont@example.com" ✓
```

#### Exemple 3 : Match approx avec Levenshtein

```html
<input name="fname" type="text">
```

**Détection :**
```
1. field_name = "fname"
2. Chercher "first" in "fname" ? ❌ NON
3. Levenshtein.ratio("fname", "first") = 0.75 ✅
4. Levenshtein.ratio("fname", "firstname") = 0.67 ✅
5. Meilleur: 0.75 (contre "first")
6. Seuil 0.7 ? 0.75 >= 0.7 ✅ OUI
7. Champ logique: "first_name"
8. Valeur: "Jean" ✓
```

#### Exemple 4 : Pas de match

```html
<input name="xyz123abc" type="text">
```

**Détection :**
```
1. field_name = "xyz123abc"
2. Aucun keyword trouvé
3. Levenshtein.ratio("xyz123abc", keywords) < 0.7 pour tous
4. Champ logique: None ❌
5. Action: Ignorer ce champ
```

### Ajuster le seuil pour plus de flexibilité

```python
# Moins strict - accepte plus de variations
response = requests.post(f"{BASE_URL}/form/fill", json={
    "session_id": "session_1",
    "levenshtein_threshold": 0.5  # Au lieu de 0.7 (défaut)
})
# Résultat: "fname" matchera même à 60% (entre 0.5 et 0.7)

# Plus strict - nécessite plus de similarité
response = requests.post(f"{BASE_URL}/form/fill", json={
    "session_id": "session_1",
    "levenshtein_threshold": 0.9  # Très strict
})
# Résultat: Seulement les matches très proches sont acceptés
```

---

## 📏 Distance Levenshtein

### Concept fondamental

La **distance de Levenshtein** mesure **combien de modifications** il faut pour transformer une chaîne en une autre.

Les modifications permetties:
1. **Insertion** : "cat" → "cart" (ajouter 'r')
2. **Suppression** : "cart" → "cat" (enlever 'r')
3. **Substitution** : "cat" → "bat" (remplacer 'c' par 'b')

### Calcul de la distance

```
Distance = nombre minimum d'opérations nécessaires

"first_name" vs "first_name"     → distance = 0   (identique)
"first_name" vs "firstname"      → distance = 1   (enlever underscore)
"first_name" vs "first_nam"      → distance = 1   (enlever 'e')
"email" vs "mail"                → distance = 2   (enlever 'e' + 'm')
"phone" vs "telephone"           → distance = 6
```

### Ratio de similarité

La **distance seule** n'est pas intuitive. On la convertit en **ratio** (0 à 1) :

```python
ratio = 1 - (distance / max_length)

ratio = 1.0  → Identique (100% similaire)
ratio = 0.8  → Très similaire (80%)
ratio = 0.6  → Similaire (60%)
ratio = 0.3  → Peu similaire (30%)
ratio = 0.0  → Complètement différent (0%)
```

### Exemples détaillés

#### Exemple 1: Strings courtes

```
"email" vs "mail"
Distance = 2
Max length = 5
Ratio = 1 - (2/5) = 1 - 0.4 = 0.6 (60% similaire)
```

**Seuil 0.7 ?** 0.6 < 0.7 → ❌ REJETÉ

#### Exemple 2: Avec underscore

```
"first_name" vs "firstname"
Distance = 1 (enlever underscore)
Max length = 10
Ratio = 1 - (1/10) = 0.9 (90% similaire)
```

**Seuil 0.7 ?** 0.9 >= 0.7 → ✅ ACCEPTÉ

#### Exemple 3: Variations de langues

```
"date_naissance" vs "date_of_birth"
Distance = 8 (plusieurs opérations)
Max length = 14
Ratio = 1 - (8/14) ≈ 0.43 (43% similaire)
```

**Seuil 0.7 ?** 0.43 < 0.7 → ❌ REJETÉ

**MAIS** notre code a une **optimisation** :
```python
if "birth" in "date_naissance":
    ratio = 0.95  # Bonus car "birth" est dans "date_naissance"
```
**Résultat :** 0.95 >= 0.7 → ✅ ACCEPTÉ

### Comment ça fonctionne dans l'API

```python
from Levenshtein import ratio

# Cas 1: Match exact par contenance
field_name = "customer_email"
keyword = "email"

if keyword in field_name.lower():
    match_ratio = 0.95  # BONUS immédiat
    # Résultat: ✅ Accepté (0.95 >= 0.7)

# Cas 2: Match approx
field_name = "usr_email_xyz"
keyword = "mail"

if keyword not in field_name.lower():
    match_ratio = Levenshtein.ratio("usr_email_xyz", "mail")
    # = 0.42 (seulement "mail" en commun)
    # Résultat: ❌ Rejeté (0.42 < 0.7)

# Cas 3: Match approx (meilleur keyword)
field_name = "fname"
keyword = "first"

if keyword not in field_name.lower():
    match_ratio = Levenshtein.ratio("fname", "first")
    # = 0.75 (4 caractères communs sur 5)
    # Résultat: ✅ Accepté (0.75 >= 0.7)
```

### Tableau de comparaisons

| Field HTML | Keyword | Contenance ? | Levenshtein | Seuil 0.7 | Résultat |
|-----------|---------|-------------|-------------|----------|----------|
| `first_name` | `first` | ✅ OUI | 0.95 | 0.7 | ✅ MATCH |
| `firstname` | `first` | ✅ OUI | 0.95 | 0.7 | ✅ MATCH |
| `customer_first_name` | `first` | ✅ OUI | 0.95 | 0.7 | ✅ MATCH |
| `fname` | `first` | ❌ NON | 0.75 | 0.7 | ✅ MATCH |
| `fn` | `first` | ❌ NON | 0.33 | 0.7 | ❌ NO MATCH |
| `email` | `email` | ✅ OUI | 0.95 | 0.7 | ✅ MATCH |
| `user_email` | `email` | ✅ OUI | 0.95 | 0.7 | ✅ MATCH |
| `mail` | `email` | ❌ NON | 0.67 | 0.7 | ❌ NO MATCH |
| `contact` | `email` | ❌ NON | 0.11 | 0.7 | ❌ NO MATCH |

### Avantages et limitations

**✅ Avantages :**
- Flexible pour différentes variations de noms
- Robuste contre les typos
- Fonctionne en plusieurs langues
- Seuil configurable

**⚠️ Limitations :**
- Les très courts noms (2-3 caractères) peuvent avoir des ratios trompeurs
- Ne comprend pas la sémantique ("email" ≠ "contact" même s'ils veulent dire pareil)
- Sensible à la longueur du keyword

### Configuration recommandée

```python
# Stricte (peu de faux positifs)
levenshtein_threshold = 0.8
# Accepte seulement les matches très proches
# Exemple: "first_name" ✅ mais "fn" ❌

# Normal (équilibre) [DÉFAUT]
levenshtein_threshold = 0.7
# Accepte les variations raisonnables
# Exemple: "first_name" ✅ et "fname" ✅

# Permissif (peu de faux négatifs)
levenshtein_threshold = 0.5
# Accepte même les matches approx
# Exemple: "first_name" ✅, "fname" ✅, "fn" ❌ mais "mail" pour email? ✅
```

---

## 🔧 Remplissage des formulaires

### Processus général

```
1. Trouver tous les <form> de la page
2. Pour chaque formulaire:
   a. Traiter les <input>
   b. Traiter les <textarea>
   c. Traiter les <select>
3. Enregistrer les champs remplis
4. Retourner le résumé
```

### Code principal

```python
def fill_forms(driver, provided_values=None, use_levenshtein=True, threshold=0.7):
    """
    Remplit automatiquement les formulaires détectés
    Retourne la liste des champs remplis
    """
    filled_fields = []
    
    # Récupérer tous les formulaires
    forms = driver.find_elements(By.TAG_NAME, 'form')
    
    for form in forms:
        # Traiter les inputs
        for inp in form.find_elements(By.TAG_NAME, 'input'):
            # Vérifier si visible et activé
            if not (inp.is_displayed() and inp.is_enabled()):
                continue
            
            # Détecter le champ logique
            realname = inp.get_attribute('name')
            logical = detect_logical_key_levenshtein(realname, threshold)
            
            # Récupérer la valeur
            value = provided_values.get(logical) or DEFAULT_VALUES.get(logical)
            
            # Remplir
            if value:
                inp.send_keys(value)
                filled_fields.append({...})
    
    return filled_fields
```

---

## 🎯 Gestion des types de champs

### 1️⃣ Inputs texte simples

**Detection :** `type="text"`

**Remplissage :**
```python
inp.send_keys("Jean")
```

**Exemple :**
```html
<input type="text" name="user_first_name">
```

---

### 2️⃣ Checkboxes et Radios

**Detection :** `type="checkbox"` ou `type="radio"`

**Remplissage :**
```python
if value in ['y', 'yes', '1', 'true', 'on']:
    if not inp.is_selected():
        inp.click()
```

**Exemple :**
```html
<input type="checkbox" name="accept_terms" value="yes">
```

---

### 3️⃣ Champs de date (texte)

**Detection :** `name` contient "departure-date", "return-date"

**Remplissage :**
```python
if is_date_text_field(realname):
    if 'departure' in realname:
        value = provided_values.get('departure_date')
    inp.send_keys(value)
```

**Format :** YYYY-MM-DD
**Exemple :** "2025-12-30"

---

### 4️⃣ Champs jour/mois/année séparé

**Detection :** 
- Jour: `name` contient "jour" ou "day"
- Mois: `name` contient "mois" ou "month"
- Année: `name` contient "annee" ou "year"

**Remplissage :**
```python
def parse_date_components(date_str):
    """Parse '1990-01-15' en jour='15', mois='01', annee='1990'"""
    parts = date_str.split('-')
    return {
        'day': parts[2],
        'month': parts[1],
        'year': parts[0]
    }

# Utilisation
if is_day_field(realname):
    day = parse_date_components('1990-01-15')['day']
    inp.send_keys(day)  # "15"
```

---

### 5️⃣ Menus déroulants (Select)

**Detection :** `<select>` HTML

**Remplissage en 4 étapes :**

#### Étape 1: Match exact
```python
try:
    sel.select_by_visible_text("Jean")  # Cherche "Jean" exactement
    return
except:
    pass
```

#### Étape 2: Match par valeur
```python
try:
    sel.select_by_value("jean")  # value="jean"
    return
except:
    pass
```

#### Étape 3: Match par index
```python
try:
    sel.select_by_index(0)  # 1ère option
    return
except:
    pass
```

#### Étape 4: Match Levenshtein (approximatif)
```python
closest = find_closest_option(sel_elem, "Jean", threshold=0.6)
if closest:
    sel.select_by_visible_text(closest)  # "Jon" → match à 67%
```

---

### 6️⃣ Champs spéciaux: Title/Civilité

**Detection :** `is_title_field()` cherche "title", "civilité", "mr", "mrs", "ms"

**Remplissage spécial :**
```python
def get_title_option(select_element):
    """Cherche l'option de titre intelligemment"""
    options = [opt.text for opt in select_element.find_elements(...)]
    
    # Chercher 'Mrs.' exactement
    if "Mrs." in options:
        return "Mrs."
    
    # Sinon chercher 'Mrs' sans point
    for opt in options:
        if opt.lower() in ['mrs', 'mrs.']:
            return opt
    
    # Sinon chercher 'Madame'
    for opt in options:
        if 'madame' in opt.lower():
            return opt
    
    # Sinon 2e option (généralement Mrs après Mr)
    return options[1]
```

**Exemple :**
```html
<select name="title">
    <option value="">Select...</option>
    <option value="mr">Mr.</option>
    <option value="mrs">Mrs.</option>  ← sélectionné automatiquement
    <option value="ms">Ms.</option>
</select>
```

---

### 7️⃣ Champs spéciaux: Pays

**Detection :** `is_country_field()` cherche "country", "pays", "nationality"

**Remplissage :**
```python
if is_country_field(realname):
    # Chercher 'France' ou 'FR'
    try:
        sel.select_by_visible_text('France')
    except:
        try:
            sel.select_by_value('FR')
        except:
            print("France not found")
```

---

## 📊 Exemple complet

### Formulaire HTML

```html
<form>
    <input type="text" name="customer_first_name" placeholder="First name">
    <input type="text" name="customer_last_name" placeholder="Last name">
    <input type="email" name="contact_email" placeholder="Email">
    
    <input type="text" name="birth_day" placeholder="Day">
    <input type="text" name="birth_month" placeholder="Month">
    <input type="text" name="birth_year" placeholder="Year">
    
    <select name="user_title">
        <option>Select title</option>
        <option>Mr.</option>
        <option>Mrs.</option>
        <option>Ms.</option>
    </select>
    
    <select name="nationality">
        <option>Select country</option>
        <option value="FR">France</option>
        <option value="US">USA</option>
    </select>
    
    <textarea name="user_address"></textarea>
</form>
```

### Exécution

```bash
# Terminal 1
python api_form_autofill.py

# Terminal 2
python test_simple.py
```

### Logs

```
1️⃣ Création d'une session...
   URL: https://example.com
✅ Session créée: test_session

2️⃣ Vérification de la session (GET)...
   ✅ Page actuellement ouverte: https://example.com
   ✅ Titre: Example Website

3️⃣ Remplissage du formulaire initial...
   Valeurs à remplir:
     - first_name: Jean
     - last_name: Dupont
     - ...

Formulaire 1
  Rempli customer_first_name (type=text) avec 'Jean'
  Rempli customer_last_name (type=text) avec 'Dupont'
  Rempli contact_email (type=email) avec 'jean.dupont@example.com'
  Rempli birth_day (jour) avec '15'
  Rempli birth_month (mois) avec '01'
  Rempli birth_year (année) avec '1990'
  Select user_title (Titre) -> Mrs.
  Select nationality (Pays) -> France
  Rempli user_address (type=textarea) avec '1 Rue Exemple'

✅ Remplissage complété!
============================================================
📋 RÉSUMÉ DES CHAMPS REMPLIS
============================================================
📊 Total: 9 champs remplis

  1. customer_first_name
     └─ Type: text
     └─ Valeur: Jean
  2. customer_last_name
     └─ Type: text
     └─ Valeur: Dupont
  ...

🔄 SURVEILLANCE AUTOMATIQUE DES CHANGEMENTS DE PAGE
💡 Le script surveille automatiquement les changements de page
   Navigue librement, les formulaires seront remplis auto.
```

---

## 🔄 Flux complet du client (test_simple.py)

```
1. Créer session (POST /session/create)
   ↓
2. Vérifier session (GET /session/{id})
   ↓
3. Remplir formulaire initial (POST /form/fill)
   ↓
4. Enregistrer URL comme remplie (filled_urls.add(url))
   ↓
5. Boucle de surveillance (toutes les 3 secondes):
   ├─ Vérifier URL actuelle (GET /session/{id})
   ├─ Si URL change ET pas encore remplie:
   │  ├─ Attendre 2 secondes (chargement page)
   │  ├─ Remplir formulaire (POST /form/fill)
   │  └─ Enregistrer URL remplie
   └─ Répéter jusqu'à Ctrl+C
```

---

## 🛠️ Personnalisation

### Modifier les valeurs par défaut

**api_form_autofill.py :**
```python
DEFAULT_VALUES = {
    'first_name': 'Ton Prénom',
    'last_name': 'Ton Nom',
    'email': 'ton-email@example.com',
    # ...
}
```

### Ajouter un nouveau champ

```python
# 1. Ajouter au dictionnaire de keywords
COMMON_FIELD_KEYWORDS = {
    # ...
    'company': ['company', 'compagnie', 'enterprise']
}

# 2. Ajouter la valeur par défaut
DEFAULT_VALUES = {
    # ...
    'company': 'Ma Compagnie'
}

# 3. Utiliser dans test_simple.py
FORM_VALUES = {
    # ...
    'company': 'Ma Compagnie'
}
```

### Modifier le seuil Levenshtein

```python
# Moins strict (accepte plus de variations)
response = requests.post(f"{BASE_URL}/form/fill", json={
    "levenshtein_threshold": 0.5  # Défaut: 0.7
})

# Plus strict (nécessite plus de similarité)
response = requests.post(f"{BASE_URL}/form/fill", json={
    "levenshtein_threshold": 0.9
})
```

---

## 🐛 Dépannage

### Le champ n'est pas rempli

1. **Vérifier le keyword**
   ```python
   # Ajouter le keyword manquant
   'email': ['email', 'e-mail', 'mail', 'email_address']
   ```

2. **Augmenter le seuil Levenshtein**
   ```
   levenshtein_threshold: 0.5  # Au lieu de 0.7
   ```

3. **Déboguer manuellement**
   ```python
   field_name = "usr_email_xyz"
   ratio = Levenshtein.ratio("usr_email_xyz", "email")
   print(ratio)  # Voir le ratio
   ```

### Le select ne se remplit pas

1. **Vérifier le texte visible**
   ```python
   # Le texte dans l'option doit matcher
   <option>Mrs.</option>  # Chercher exactement "Mrs."
   ```

2. **Essayer par valeur**
   ```html
   <option value="mrs">Mrs.</option>
   <!-- Cherchera aussi par value="mrs" -->
   ```

3. **Utiliser Levenshtein pour l'approx**
   ```python
   # Si "Mrs" trouve "Mme", ok
   find_closest_option(select, "Mrs", threshold=0.6)
   ```

---

## 📌 Résumé des concepts clés

| Concept | Description |
|---------|-------------|
| **Session** | Une instance du navigateur Edge |
| **Keyword Mapping** | Dictionnaire name → champ logique |
| **Levenshtein** | Similarité entre strings pour détection flexible |
| **Logical Field** | Champ détecté (first_name, email, etc) |
| **HTML Field** | Champ réel dans le formulaire (customer_name, contact_email) |
| **Fill Strategy** | 4 étapes pour les selects (exact, value, index, Levenshtein) |
| **Special Fields** | Title/Country/Date gérés différemment |

---

## 📚 Dépendances

```
selenium==4.x.x              # Web automation
fastapi==0.x.x              # Web API framework
uvicorn==0.x.x              # ASGI server
python-Levenshtein==0.x.x   # String similarity
webdriver-manager==x.x.x    # Automatic driver management
requests==2.x.x             # HTTP client
pydantic==2.x.x             # Data validation
```

---

## 🎓 Conclusion

Cette API combine :
- **Selenium** pour contrôler le navigateur
- **Levenshtein** pour une détection flexible
- **FastAPI** pour une API rapide et moderne
- **Stratégies multi-niveaux** pour remplir tous les types de champs

Le résultat : un système robuste qui remplit les formulaires automatiquement, même avec des variations de noms et structures ! 🎉
