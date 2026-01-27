# 🚀 Form Autofill - Documentation Complète

## 📋 Table des matières
- [Architecture Générale](#architecture-générale)
- [Structure du Projet](#structure-du-projet)
- [API REST - Endpoints](#api-rest---endpoints)
- [Processus de Détection et Remplissage](#processus-de-détection-et-remplissage)
- [Profiles Disponibles](#profiles-disponibles)
- [Installation et Démarrage](#installation-et-démarrage)
- [Exemples d'Utilisation](#exemples-dutilisation)

---

## 🏗️ Architecture Générale

Le projet est composé de **2 composants principaux**:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (test_recherche_google.py)         │
│  - Interface GUI pour choisir le profil                      │
│  - Gestion de la session utilisateur                         │
│  - Monitoring continu des formulaires                        │
└────────────────┬────────────────────────────────────────────┘
                 │ Requêtes HTTP (REST API)
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              API REST (api_form_autofill_v5.py)              │
│  - Port: 8000                                               │
│  - Framework: FastAPI                                        │
│  - Driver: Selenium + Microsoft Edge                         │
│  - Détection: Levenshtein Distance                          │
└────────────────┬────────────────────────────────────────────┘
                 │ Contrôle navigateur
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              NAVIGATEUR (Microsoft Edge)                     │
│  - Affichage des pages web                                  │
│  - Détection et remplissage des formulaires                 │
│  - Interaction avec l'utilisateur                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure du Projet

```
webscrapping_FormAutoFill-main/
│
├── 🔧 API
│   ├── api_form_autofill_v5.py          # API REST principale
│   ├── api_form_autofill_v3.py          # Ancienne version
│   ├── requirements_api.txt              # Dépendances Python
│   └── msedgedriver.exe                 # Driver Selenium Edge
│
├── 🧪 TESTS & CLIENTS
│   ├── test_recherche_google.py         # CLIENT: Google Search + Autofill
│   ├── test_simple_v5.py                # Test simple v5
│   ├── test_simple_v5_new.py            # Test simple v5 (nouveau)
│   ├── test_upgrade.py                  # Tests avancés
│   ├── test_upgrade_gui.py              # GUI tests
│   ├── test_date_detection.py           # Tests détection dates
│   └── test_recherche_google.py         # Tests recherche Google
│
├── 📚 DOCUMENTATION
│   ├── README.md                        # README principal
│   ├── README_ARCHITECTURE.md           # Ce fichier
│   ├── GUIDE_RAPIDE.md                  # Guide rapide
│   ├── LOGIQUE_REMPLISSAGE.md           # Explications détaillées
│   ├── FIX_LEVENSHTEIN_DATES.md         # Corrections Levenshtein
│   └── SOLUTION_FORM_ID.md              # Solutions form_id
│
└── 🐍 DEPENDENCIES
    └── requirements_api.txt             # fastapi, selenium, levenshtein, etc.
```

---

## 🌐 API REST - Endpoints

### 📌 Base de l'API
- **URL**: `http://localhost:8000`
- **Documentation Interactive**: `http://localhost:8000/docs`
- **Framework**: FastAPI

---

### 1️⃣ **GET / - Accueil**
```http
GET http://localhost:8000/
```
**Réponse:**
```json
{
  "message": "Form Autofill API v5.0 - Bienvenue!",
  "version": "5.0.0"
}
```

---

### 2️⃣ **GET /profiles - Lister tous les profils**
```http
GET http://localhost:8000/profiles
```
**Réponse:**
```json
{
  "available_profiles": [
    {
      "id": "profile1",
      "name": "Voyageur Standard",
      "description": "Jean Dupont - Voyageur régulier"
    },
    {
      "id": "profile2",
      "name": "Client Affaires",
      "description": "Marie Martin - Professionnel"
    },
    {
      "id": "profile3",
      "name": "Touriste International",
      "description": "Anna Schmidt - Explorateur"
    }
  ]
}
```

---

### 3️⃣ **GET /profiles/{profile_id} - Récupérer un profil spécifique**
```http
GET http://localhost:8000/profiles/profile1
```
**Réponse:**
```json
{
  "data": {
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "phone": "+33612345678",
    "gender": "Homme",
    "date_of_birth": "1990-01-15",
    "street": "123 Rue de Paris",
    "street_number": "123",
    "city": "Paris",
    "zip": "75001",
    "country": "France",
    "passport": "AB123456"
  }
}
```

---

### 4️⃣ **POST /session/create - Créer une nouvelle session**
```http
POST http://localhost:8000/session/create
Content-Type: application/json

{
  "session_id": "test_session_001",
  "url": "https://www.google.com",
  "maximize": true
}
```
**Réponse:**
```json
{
  "session_id": "test_session_001",
  "status": "created",
  "url": "https://www.google.com",
  "message": "Session créée avec succès"
}
```

**Paramètres:**
| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `session_id` | string | ✅ | ID unique de la session |
| `url` | string | ✅ | URL de démarrage |
| `maximize` | boolean | ❌ | Maximiser la fenêtre (défaut: false) |

---

### 5️⃣ **GET /session/{session_id} - Récupérer infos de session**
```http
GET http://localhost:8000/session/test_session_001
```
**Réponse:**
```json
{
  "session_id": "test_session_001",
  "driver_active": true,
  "current_url": "https://www.google.com",
  "window_size": [1920, 1080]
}
```

---

### 6️⃣ **POST /form/detect - Détecter les champs d'un formulaire**
```http
POST http://localhost:8000/form/detect
Content-Type: application/json

{
  "session_id": "test_session_001",
  "use_levenshtein": true,
  "levenshtein_threshold": 0.5
}
```
**Réponse:**
```json
{
  "success": true,
  "total": 5,
  "fields": [
    {
      "name": "email",
      "id": "email_input",
      "type": "email",
      "form_id": "form_1",
      "visible": true,
      "required": true,
      "suggestions": [
        {
          "field_type": "email",
          "score": 0.98
        }
      ]
    },
    {
      "name": "first_name",
      "id": "fname",
      "type": "text",
      "form_id": "form_1",
      "visible": true,
      "required": false,
      "suggestions": [
        {
          "field_type": "first_name",
          "score": 0.85
        }
      ]
    }
  ]
}
```

**Paramètres:**
| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `session_id` | string | ✅ | ID de la session |
| `use_levenshtein` | boolean | ❌ | Activer la détection Levenshtein (défaut: false) |
| `levenshtein_threshold` | float | ❌ | Seuil de similarité 0.0-1.0 (défaut: 0.5) |

**Modes de Détection:**
1. **Par nom exact** (priorité 1): Correspondance exacte du nom du champ
2. **Par Levenshtein** (priorité 2): Distance Levenshtein si score >= seuil
3. **Par label HTML** (priorité 3): Texte du label associé au champ

---

### 7️⃣ **POST /form/fill - Remplir les champs d'un formulaire**
```http
POST http://localhost:8000/form/fill
Content-Type: application/json

{
  "session_id": "test_session_001",
  "values": {
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "phone": "+33612345678",
    "street": "123 Rue de Paris",
    "city": "Paris",
    "zip": "75001"
  },
  "use_levenshtein": true,
  "levenshtein_threshold": 0.5,
  "form_id": "form_1"
}
```
**Réponse:**
```json
{
  "success": true,
  "total_fields": 7,
  "filled_fields": [
    {
      "name": "email",
      "type": "email",
      "value": "jean.dupont@example.com",
      "status": "filled"
    },
    {
      "name": "first_name",
      "type": "text",
      "value": "Jean",
      "status": "filled"
    }
  ],
  "errors": []
}
```

**Paramètres:**
| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `session_id` | string | ✅ | ID de la session |
| `values` | object | ✅ | Dictionnaire des valeurs à remplir |
| `use_levenshtein` | boolean | ❌ | Activer la détection Levenshtein |
| `levenshtein_threshold` | float | ❌ | Seuil de similarité 0.0-1.0 |
| `form_id` | string | ❌ | ID du formulaire (si plusieurs) |

---

### 8️⃣ **POST /session/{session_id}/navigate - Naviguer vers une URL**
```http
POST http://localhost:8000/session/test_session_001/navigate?url=https://example.com
```
**Réponse:**
```json
{
  "success": true,
  "previous_url": "https://www.google.com",
  "current_url": "https://example.com",
  "message": "Navigation réussie"
}
```

---

### 9️⃣ **POST /session/{session_id}/click-next - Cliquer sur bouton suivant**
```http
POST http://localhost:8000/session/test_session_001/click-next
```
**Réponse:**
```json
{
  "success": true,
  "message": "Bouton 'Suivant' cliqué",
  "current_url": "https://example.com/step2"
}
```

---

### 🔟 **GET /sessions - Lister toutes les sessions actives**
```http
GET http://localhost:8000/sessions
```
**Réponse:**
```json
{
  "total": 2,
  "sessions": [
    {
      "id": "test_session_001",
      "url": "https://www.google.com"
    },
    {
      "id": "test_session_002",
      "url": "https://example.com"
    }
  ]
}
```

---

## 🔍 Processus de Détection et Remplissage

### 📊 Algorithme de Détection (Levenshtein)

```python
# Étape 1: Normaliser le nom du champ
field_name = "email_address"

# Étape 2: Chercher dans FIELD_KEYWORDS
# 'email': ['email', 'mail', 'courriel', 'e-mail']

# Étape 3: Calculer Levenshtein pour chaque mot-clé
score = levenshtein_distance(field_name, "email") / max(len(field_name), len("email"))

# Étape 4: Si score >= seuil (0.5), c'est un match!
```

### 🎯 Priorités de Détection
1. **Nom exact** (100%): `email` == `email`
2. **Levenshtein** (si threshold respecté): distance calculée
3. **Label HTML parent**: Texte du label associé

### 🔄 Processus Complet

```
Utilisateur clique sur un lien (navigation)
           ↓
API détecte changement d'URL
           ↓
      POST /form/detect
           ↓
  Extraction des champs HTML
           ↓
    Détection avec Levenshtein
           ↓
  Affichage dans le terminal
           ↓
      POST /form/fill
           ↓
   Remplissage automatique
           ↓
 Message de succès à l'utilisateur
           ↓
    Attente de navigation suivante
```

---

## 👥 Profiles Disponibles

### Profile 1: Voyageur Standard
```json
{
  "id": "profile1",
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@example.com",
  "phone": "+33612345678",
  "gender": "Homme",
  "date_of_birth": "1990-01-15",
  "street": "123 Rue de Paris",
  "street_number": "123",
  "city": "Paris",
  "zip": "75001",
  "country": "France",
  "passport": "AB123456"
}
```

### Profile 2: Client Affaires
```json
{
  "id": "profile2",
  "first_name": "Marie",
  "last_name": "Martin",
  "email": "marie.martin@example.com",
  "phone": "+33612345679",
  "gender": "Femme",
  "date_of_birth": "1985-05-20",
  "street": "456 Avenue de Lyon",
  "street_number": "456",
  "city": "Lyon",
  "zip": "69000",
  "country": "France",
  "passport": "CD789012"
}
```

### Profile 3: Touriste International
```json
{
  "id": "profile3",
  "first_name": "Anna",
  "last_name": "Schmidt",
  "email": "anna.schmidt@example.com",
  "phone": "+49123456789",
  "gender": "Femme",
  "date_of_birth": "1992-08-10",
  "street": "789 Straße Berlin",
  "street_number": "789",
  "city": "Berlin",
  "zip": "10115",
  "country": "Allemagne",
  "passport": "EF345678"
}
```

---

## 🚀 Installation et Démarrage

### Prérequis
- Python 3.8+
- Microsoft Edge navigateur
- msedgedriver.exe dans le répertoire du projet

### Installation

**1. Installer les dépendances:**
```bash
pip install -r requirements_api.txt
```

**2. Contenu de requirements_api.txt:**
```
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
selenium==4.16.0
python-Levenshtein==0.25.0
```

### Démarrage

**Terminal 1: Lancer l'API**
```bash
python api_form_autofill_v5.py
```
✅ API disponible sur `http://localhost:8000`

**Terminal 2: Lancer le client**
```bash
python test_recherche_google.py
```
✅ Interface GUI de sélection de profil s'affiche

---

## 📚 Exemples d'Utilisation

### Exemple Complet: Google Search + Autofill

```python
import requests
import time

BASE_URL = "http://localhost:8000"
SESSION_ID = "my_session_001"

# 1. Créer une session avec Google
response = requests.post(f"{BASE_URL}/session/create", json={
    "session_id": SESSION_ID,
    "url": "https://www.google.com",
    "maximize": True
})
print(f"✅ Session créée: {response.json()}")

# 2. Attendre le chargement
time.sleep(3)

# 3. Récupérer les données du profil
profile_data = requests.get(f"{BASE_URL}/profiles/profile1").json()["data"]
print(f"✅ Profil récupéré: {profile_data['first_name']} {profile_data['last_name']}")

# 4. Détecter les champs
detect_response = requests.post(f"{BASE_URL}/form/detect", json={
    "session_id": SESSION_ID,
    "use_levenshtein": True,
    "levenshtein_threshold": 0.5
})
print(f"✅ {len(detect_response.json()['fields'])} champs détectés")

# 5. Remplir le formulaire
fill_response = requests.post(f"{BASE_URL}/form/fill", json={
    "session_id": SESSION_ID,
    "values": profile_data,
    "use_levenshtein": True,
    "levenshtein_threshold": 0.5
})
print(f"✅ {len(fill_response.json()['filled_fields'])} champs remplis")
```

### Exemple: Navigation et Remplissage Multiple

```python
# Naviguer vers un site
requests.post(f"{BASE_URL}/session/{SESSION_ID}/navigate?url=https://example.com")
time.sleep(3)

# Détecter et remplir
detect = requests.post(f"{BASE_URL}/form/detect", json={"session_id": SESSION_ID})
fill = requests.post(f"{BASE_URL}/form/fill", json={
    "session_id": SESSION_ID,
    "values": profile_data
})

# Cliquer sur "Suivant"
requests.post(f"{BASE_URL}/session/{SESSION_ID}/click-next")
```

---

## 🎯 Cas d'Usage: test_recherche_google.py

### 🌐 Fonctionnement

1. **Lancement**: Interface GUI pour choisir profil
2. **Google Search**: Google s'ouvre automatiquement
3. **Recherche Libre**: Utilisateur fait ses recherches normalement
4. **Clic sur URL**: Détection automatique du formulaire
5. **Remplissage Automatique**: Sans quitter la page
6. **Monitoring Continu**: Détecte les nouveaux formulaires

### 📋 Architecture du Client

```
show_profile_picker_gui()
    ↓ (Retourne profile_id)
run_test()
    ├─→ Récupère les données du profil via GET /profiles/{profile_id}
    ├─→ Crée une session avec POST /session/create
    ├─→ Lance le monitoring continu
    │   ├─→ Attend la navigation utilisateur
    │   ├─→ Détecte changement d'URL
    │   ├─→ POST /form/detect
    │   ├─→ POST /form/fill
    │   └─→ Affiche résultats
    └─→ Reste actif jusqu'à Ctrl+C
```

### 🎨 Interface GUI

La fenêtre de sélection est **professionnelle et moderne**:
- Header sombre avec titre
- 3 boutons de profil avec couleurs
- Emojis descriptifs (✈️, 💼, 🌍)
- Effet de survol (couleur foncée)
- Footer informatif

---

## 🔧 Configuration Avancée

### Seuil Levenshtein

Le seuil de Levenshtein détermine la **sensibilité** de la détection:

| Seuil | Sensibilité | Cas d'Usage |
|-------|-------------|-----------|
| 0.9 | Très haute | Correspondances exactes uniquement |
| 0.7 | Haute | Champs avec petites variations |
| 0.5 | Moyenne | **Recommandé par défaut** |
| 0.3 | Basse | Tolère grandes variations |

### Exemple:
```python
# Très strict
requests.post(f"{BASE_URL}/form/detect", json={
    "session_id": SESSION_ID,
    "use_levenshtein": True,
    "levenshtein_threshold": 0.9  # Seuil très élevé
})

# Tolérant
requests.post(f"{BASE_URL}/form/detect", json={
    "session_id": SESSION_ID,
    "use_levenshtein": True,
    "levenshtein_threshold": 0.3  # Seuil bas
})
```

---

## 🚨 Gestion des Erreurs

### Erreur: Session non trouvée
```json
{
  "detail": "Session non trouvée"
}
```
**Solution**: Créer une session avec `/session/create`

### Erreur: Aucun champ détecté
```json
{
  "success": false,
  "total": 0,
  "fields": []
}
```
**Solution**: Augmenter le seuil Levenshtein ou vérifier le formulaire

### Erreur: Profil invalide
```json
{
  "detail": "Profil non trouvé"
}
```
**Solution**: Utiliser un profil valide: `profile1`, `profile2`, ou `profile3`

---

## 📞 Support et Debugging

### Activer le logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Vérifier l'API
```bash
# Test simple
curl http://localhost:8000/

# Liste les profils
curl http://localhost:8000/profiles

# Vérifie la documentation
# Ouvrez: http://localhost:8000/docs
```

### Vérifier les sessions actives
```bash
curl http://localhost:8000/sessions
```

---

## 📝 Résumé

| Composant | Langage | Port | Rôle |
|-----------|---------|------|------|
| **API** | Python/FastAPI | 8000 | Détection, remplissage, gestion sessions |
| **Client** | Python/Tkinter | - | Interface GUI, coordination |
| **Navigateur** | Edge/Selenium | - | Affichage et interaction utilisateur |

**Flux Principal:**
```
Google → Détection champs → Remplissage auto → Résultat → Nouveau formulaire
```

---

Créé avec ❤️ pour l'automatisation de formulaires
