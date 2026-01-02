# 📋 Form Autofill API - Système de Remplissage Automatique de Formulaires

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Selenium](https://img.shields.io/badge/Selenium-4.16+-orange.svg)](https://www.selenium.dev/)

> **Projet Master MOSEF** - Université Paris 1 Panthéon-Sorbonne  
> Web Scraping & Automatisation

---

## 🎯 Objectif du Projet

Créer un système intelligent qui **remplit automatiquement les formulaires web** sur n'importe quel site, en utilisant :

- **Selenium** pour contrôler le navigateur
- **Distance de Levenshtein** pour détecter les champs de manière flexible
- **FastAPI** pour exposer une API REST

---

## ✨ Fonctionnalités Supportées

### Types de Champs Gérés

| Type | Exemples | Status |
|------|----------|--------|
| **Inputs texte** | Nom, Email, Téléphone, Adresse | ✅ |
| **Inputs email** | Email de contact, Login | ✅ |
| **Inputs password** | Mot de passe (avec génération sécurisée) | ✅ |
| **Checkboxes simples** | "Se souvenir de moi", "Accepter les CGU" | ✅ |
| **Checkboxes multiples** | Garnitures pizza, Options de voyage | ✅ |
| **Radios simples** | Genre (M/F), Taille (S/M/L) | ✅ |
| **Radios complexes** | "Pour qui réservez-vous ?", "Voyagez-vous pour le travail ?" | ✅ |
| **Selects / Dropdowns** | Pays, Civilité, Heure d'arrivée | ✅ |
| **Textareas** | Commentaires, Adresse complète | ✅ |
| **Champs de date** | Jour/Mois/Année séparés ou combinés | ✅ |

---

## 🌐 Sites Testés et Supportés

### Sites de Test

| Site | URL | Ce qui est testé |
|------|-----|------------------|
| **HTTPBin Pizza** | `httpbin.org/forms/post` | Radios (taille), Checkboxes (garnitures), Textarea |
| **DemoQA** | `demoqa.com/automation-practice-form` | Formulaire complet de test |
| **Formy** | `formy-project.herokuapp.com/form` | Radios, Checkboxes, Dates |
| **The Internet** | `the-internet.herokuapp.com/checkboxes` | Checkboxes isolées |

### Sites Réels (Vie Quotidienne)

| Site | URL | Ce qui est testé |
|------|-----|------------------|
| **Air Arabia** | `airarabia.com` | Réservation vol : civilité, dates, nationalité, passeport |
| **Booking.com** | `booking.com` | Réservation hôtel : radios "Pour qui ?", "Travail ?", heure d'arrivée, options voiture/transfert |
| **SNCF Connect** | `sncf-connect.com` | Connexion : email, mot de passe, checkbox "Se souvenir de moi" |
| **Spotify** | `spotify.com/signup` | Inscription multi-étapes : email → mot de passe → profil |

---

## 🔧 Cas d'Usage Spécifiques

### 1. Checkbox "Se souvenir de moi" (SNCF)

```python
# Configuration
"remember_me": True  # Coche automatiquement la case
```

Le système détecte les checkboxes de type "remember", "souvenir", "stay_logged" et les coche si `True`.

---

### 2. Radios "Pour qui réservez-vous ?" (Booking)

```python
# Configuration
"booking_for": "main_guest"  # Options: "main_guest" ou "other_guest"
```

Le système comprend les synonymes :
- `main_guest` → "Je suis le client principal", "myself", "moi"
- `other_guest` → "Je réserve pour un autre", "someone else"

---

### 3. Radios "Voyagez-vous pour le travail ?" (Booking)

```python
# Configuration
"work_travel": "no"  # Options: "yes" ou "no"
```

Le système comprend les synonymes français/anglais :
- `yes` → "Oui", "Yes", "true"
- `no` → "Non", "No", "false"

---

### 4. Select "Heure d'arrivée" avec plages horaires (Booking)

```python
# Configuration
"arrival_time": "15:00"  # Sera matché avec "15:00 - 16:00" ou "15h00"
```

Le système trouve automatiquement la plage horaire correspondante dans le dropdown.

---

### 5. Checkboxes d'options (Booking)

```python
# Configuration
"car_rental": True,       # "Je suis intéressé(e) par la location d'une voiture"
"airport_transfer": True  # "Je suis intéressé(e) par un transfert aéroport"
```

Le système détecte ces checkboxes par leurs mots-clés : "car", "voiture", "location", "transfer", "transfert", "navette".

---

### 6. Checkboxes multiples (HTTPBin Pizza)

```python
# Configuration - Liste de valeurs à cocher
"topping": ["bacon", "cheese", "mushroom"]
```

Le système coche automatiquement chaque checkbox dont la `value` correspond à un élément de la liste.

---

### 7. Formulaires multi-étapes (Spotify)

```python
# Le système gère automatiquement les changements de page
# Étape 1: Email
"email": "jean@example.com"

# Étape 2: Mot de passe (respecte les contraintes)
"password": "SecurePass123!"  # Min 10 chars, 1 lettre, 1 chiffre/special

# Étape 3: Profil
"username": "jeandupont1990"
"date_of_birth": "1990-01-15"
"gender": "Male"
```

Le script de test surveille les changements de page et remplit automatiquement chaque étape.

---

## 🚀 Guide d'Installation

### Prérequis

- Python 3.10+
- Microsoft Edge (le navigateur)
- Edge WebDriver (msedgedriver.exe)

### 1. Télécharger le WebDriver

Télécharge le driver Edge correspondant à ta version :
👉 https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

Place `msedgedriver.exe` dans le dossier du projet.

### 2. Installer les dépendances

```bash
pip install -r requirements_api.txt
```

Le fichier `requirements_api.txt` contient :
```
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
selenium==4.16.0
python-Levenshtein==0.25.0
requests==2.31.0
```

### 3. Modifier le chemin du driver (si nécessaire)

Dans `api_form_autofill_v3.py`, ligne 50 :
```python
DRIVER_PATH = r"C:\ton\chemin\vers\msedgedriver.exe"
```

---

## ▶️ Utilisation

### Terminal 1 - Lancer l'API

```bash
python api_form_autofill_v3.py
```

Résultat attendu :
```
🚀 Démarrage de l'API Form Autofill - Version 3.0 Complète
📚 Documentation: http://localhost:8000/docs
✨ Supporte: checkboxes, radios, selects, dates, passwords, et plus!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Lancer le test

```bash
python test_simple_v3.py
```

### Changer de site à tester

Dans `test_simple_v3.py`, modifie la variable `CURRENT_SITE` :

```python
CURRENT_SITE = "httpbin"    # Formulaire pizza
CURRENT_SITE = "booking"    # Réservation hôtel
CURRENT_SITE = "sncf"       # Connexion SNCF
CURRENT_SITE = "spotify"    # Inscription Spotify
CURRENT_SITE = "airarabia"  # Réservation vol
CURRENT_SITE = "demoqa"     # Formulaire de test
```

---

## 📡 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Informations sur l'API et fonctionnalités |
| `/session/create` | POST | Crée une session navigateur |
| `/session/{id}` | GET | Récupère l'état de la session |
| `/session/{id}/navigate` | POST | Navigue vers une nouvelle URL |
| `/sessions` | GET | Liste toutes les sessions actives |
| `/form/fill` | POST | Remplit les formulaires de la page |

### Exemple d'appel API

```python
import requests

# 1. Créer une session
requests.post("http://localhost:8000/session/create", json={
    "session_id": "ma_session",
    "url": "https://httpbin.org/forms/post"
})

# 2. Remplir le formulaire
requests.post("http://localhost:8000/form/fill", json={
    "session_id": "ma_session",
    "values": {
        "custname": "Jean Dupont",
        "size": "medium",
        "topping": ["bacon", "cheese"]
    }
})
```

---

## 🔬 Distance de Levenshtein

### Principe

L'algorithme compare les noms de champs HTML avec des mots-clés connus pour détecter leur type.

```
"customer_email"  ≈  "email"     →  85% similaire  →  Type: EMAIL
"prenom"          ≈  "firstname" →  70% similaire  →  Type: FIRST_NAME
"remember_me"     ≈  "remember"  →  90% similaire  →  Type: REMEMBER_ME
```

### Avantage

Fonctionne même si les sites nomment leurs champs différemment :
- Site A : `<input name="email">`
- Site B : `<input name="customer_email">`
- Site C : `<input name="courriel">`

→ Tous détectés comme champ EMAIL ✅

---

## 📊 Résultats des Tests

| Site | Champs détectés | Champs remplis | Taux |
|------|-----------------|----------------|------|
| HTTPBin Pizza | 6 | 6 | ✅ 100% |
| DemoQA | 10 | 9 | ✅ 90% |
| Formy | 6 | 6 | ✅ 100% |
| Air Arabia | 12 | 10 | ✅ 83% |
| Booking | 15 | 12 | ✅ 80% |
| SNCF Connect | 3 | 3 | ✅ 100% |

---

## 🗂️ Structure du Projet

```
webscraping_project/
│
├── api_form_autofill_v3.py   # API principale (FastAPI + Selenium)
├── test_simple_v3.py         # Script de test avec configs par site
├── msedgedriver.exe          # Driver Selenium pour Edge
├── requirements_api.txt      # Dépendances Python
│
├── README.md                 # Cette documentation
├── GUIDE_RAPIDE.md          # Guide de démarrage rapide
└── AMELIORATIONS.md         # Historique des améliorations
```

---

## ⚠️ Limitations Connues

| Limitation | Raison | Solution |
|------------|--------|----------|
| Sites avec CAPTCHA | Protection anti-bot | Intervention manuelle |
| Champs JavaScript dynamiques | Générés après chargement | Augmenter le délai d'attente |
| Sites avec authentification forte | 2FA, SMS | Non automatisable |
| iFrames | Contenu isolé | Nécessite switch de contexte |


---

## 👥 Équipe

- **Lina RAGALA, Roland DUTAUZIET, Maeva N'GUESSAN** - Université Paris 1 Panthéon-Sorbonne
- Projet de Web Scraping - 2026

---

## 📄 Licence

MIT License - Projet académique
