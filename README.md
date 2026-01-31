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
- **Tkinter** pour une interface graphique de sélection de profil
- **Recherche Google** comme point de départ réaliste

---

## 🆕 Nouveautés de la Version 5.0

| Fonctionnalité | Description |
|----------------|-------------|
| **3 Profils Utilisateurs** | Voyageur Standard, Client Affaires, Touriste International |
| **Interface Graphique** | Sélection visuelle du profil avec Tkinter |
| **Recherche Google** | Navigation libre depuis Google vers n'importe quel site |
| **Monitoring Continu** | Détection automatique des formulaires lors de la navigation |
| **Nouveaux Endpoints** | GET /profiles, POST /form/detect |
| **Profils Centralisés** | Stockés dans l'API, pas dans le client |

---

## 👥 Les 3 Profils Utilisateurs

L'API propose 3 profils prédéfinis pour différents scénarios de test :

### ✈️ Profil 1 : Voyageur Standard (Jean Dupont)

| Champ | Valeur |
|-------|--------|
| Prénom | Jean |
| Nom | Dupont |
| Email | jean.dupont@example.com |
| Téléphone | +33612345678 |
| Ville | Paris |
| Pays | France |
| Genre | Homme |

### 💼 Profil 2 : Client Affaires (Marie Martin)

| Champ | Valeur |
|-------|--------|
| Prénom | Marie |
| Nom | Martin |
| Email | marie.martin@example.com |
| Téléphone | +33687654321 |
| Ville | Lyon |
| Pays | France |
| Genre | Femme |

### 🌍 Profil 3 : Touriste International (Anna Schmidt)

| Champ | Valeur |
|-------|--------|
| Prénom | Anna |
| Nom | Schmidt |
| Email | anna.schmidt@gmail.com |
| Téléphone | +49301234567 |
| Ville | Paris |
| Pays | Germany |
| Genre | Femme |

---

## ✨ Fonctionnalités Supportées

### Types de Champs Gérés

| Type | Exemples | Status |
|------|----------|--------|
| **Inputs texte** | Nom, Email, Téléphone, Adresse | ✅ |
| **Inputs email** | Email de contact, Login | ✅ |
| **Inputs password** | Mot de passe + confirmation | ✅ |
| **Checkboxes simples** | "Se souvenir de moi", "Accepter les CGU" | ✅ |
| **Checkboxes multiples** | Garnitures pizza, Options de voyage | ✅ |
| **Checkboxes par label** | Communication, Partenaires (Basic-Fit) | ✅ |
| **Radios simples** | Genre (Homme/Femme/Autre), Taille (S/M/L) | ✅ |
| **Radios Yes/No** | "Voyagez-vous pour le travail ?" | ✅ |
| **Radios avec synonymes** | Male = Homme = Man = Masculin | ✅ |
| **Selects / Dropdowns** | Pays, Civilité, Heure d'arrivée | ✅ |
| **Textareas** | Commentaires, Adresse complète | ✅ |
| **Champs de date** | Jour/Mois/Année séparés ou combinés | ✅ |
| **Adresses séparées** | Numéro ≠ Rue ≠ Complément ≠ Ville | ✅ |

---

## 🌐 Sites Testés et Supportés

### Sites de Test

| Site | URL | Ce qui est testé |
|------|-----|------------------|
| **HTTPBin Pizza** | `httpbin.org/forms/post` | Radios (taille), Checkboxes (garnitures), Textarea |

### Sites Réels

| Site | URL | Ce qui est testé |
|------|-----|------------------|
| **Air Arabia** | `airarabia.com` | Réservation vol : civilité, dates, nationalité, passeport |
| **Basic-Fit** | `basic-fit.com/fr-fr/inscription` | Genre (radio), adresses séparées, checkboxes communication |
| **Booking.com** | `booking.com` | Radios "Pour qui ?", "Travail ?", options voiture/transfert |
| **Domino's** | `commande.dominos.fr/login` | Email, mot de passe, CGU, newsletter |
| **Spotify** | `spotify.com/signup` | Inscription multi-étapes : email → mot de passe → profil |
| **SNCF Connect** | `sncf-connect.com` | Connexion : email, mot de passe, "Se souvenir de moi" |

---

## 🏗️ Architecture du Projet

```
┌─────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR                               │
│                  Lance test_recherche_google.py                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INTERFACE TKINTER                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│   │ ✈️ Profil 1 │  │ 💼 Profil 2 │  │ 🌍 Profil 3 │             │
│   └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT (Python)                             │
│                  test_recherche_google.py                        │
│  • GET /profiles/{id} → Récupère les données du profil           │
│  • POST /session/create → Ouvre Google                           │
│  • POST /form/fill → Remplit les formulaires                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVEUR (API FastAPI)                       │
│                   api_form_autofill_v5.py                        │
│  • GENERIC_PROFILES → Les 3 profils stockés                      │
│  • FIELD_KEYWORDS → Mots-clés pour Levenshtein                   │
│  • RADIO_VALUES → Synonymes (Homme = Male = Man)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     NAVIGATEUR (Edge)                            │
│  1. Ouvre Google.com                                             │
│  2. L'utilisateur cherche un site (ex: "Air Arabia")             │
│  3. Détection automatique des formulaires                        │
│  4. Remplissage automatique avec le profil choisi                │
└─────────────────────────────────────────────────────────────────┘
```

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

Dans `api_form_autofill_v5.py`, ligne ~153 :
```python
DRIVER_PATH = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")
```

---

## ▶️ Utilisation

### Terminal 1 - Lancer l'API

```bash
python api_form_autofill_v5.py
```

Résultat attendu :
```
🚀 API Form Autofill v5
📚 http://localhost:8000/docs
✅ Levenshtein: OUI
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Lancer le test avec interface graphique

```bash
python test_recherche_google.py
```

### Flux d'utilisation

1. **L'interface Tkinter s'affiche** → Choisissez un profil (Voyageur, Affaires, ou Touriste)
2. **Google s'ouvre** dans le navigateur
3. **Faites une recherche** (ex: "Basic-Fit inscription")
4. **Cliquez sur un résultat** → Le formulaire est détecté automatiquement
5. **Remplissage automatique** avec les données du profil choisi
6. **Continuez à naviguer** → Le monitoring détecte les nouveaux formulaires

---

## 📡 API Endpoints

### Endpoints de Base

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Informations sur l'API et fonctionnalités |
| `/session/create` | POST | Crée une session navigateur |
| `/session/{id}` | GET | Récupère l'état de la session |
| `/session/{id}/navigate` | POST | Navigue vers une nouvelle URL |
| `/sessions` | GET | Liste toutes les sessions actives |
| `/form/fill` | POST | Remplit les formulaires de la page |

### Nouveaux Endpoints (v5)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/profiles` | GET | Liste tous les profils disponibles |
| `/profiles/{profile_id}` | GET | Récupère les données complètes d'un profil |
| `/form/detect` | POST | Détecte les champs AVANT de remplir |
| `/session/{id}/click-next` | POST | Clique sur le bouton "Suivant" |

### Exemple d'appel API

```python
import requests

# 1. Récupérer un profil
response = requests.get("http://localhost:8000/profiles/profile1")
profile_data = response.json()['data']

# 2. Créer une session
requests.post("http://localhost:8000/session/create", json={
    "session_id": "ma_session",
    "url": "https://www.google.com"
})

# 3. Détecter les champs (optionnel)
requests.post("http://localhost:8000/form/detect", json={
    "session_id": "ma_session",
    "use_levenshtein": True,
    "levenshtein_threshold": 0.5
})

# 4. Remplir le formulaire
requests.post("http://localhost:8000/form/fill", json={
    "session_id": "ma_session",
    "values": profile_data,
    "use_levenshtein": True,
    "levenshtein_threshold": 0.5
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

## 🔄 Système de Synonymes pour Radios

### Genre

```python
RADIO_VALUES = {
    'homme': ['homme', 'male', 'man', 'm', 'masculin', 'herr'],
    'femme': ['femme', 'female', 'woman', 'f', 'féminin', 'frau'],
    'autre': ['autre', 'other', 'divers', 'non-binary'],
}
```

**Exemple** : Si le profil a `gender: "Male"` et le site affiche "Homme", le système comprend que c'est synonyme et coche le bon radio.

### Yes/No

```python
RADIO_VALUES = {
    'oui': ['oui', 'yes', 'true', '1', 'on', 'ja'],
    'non': ['non', 'no', 'false', '0', 'off', 'nein'],
}
```

**Exemple** : Si le profil a `work_travel: "no"` et le site demande "Voyagez-vous pour le travail ? Oui/Non", le système sélectionne "Non".

---

## ☑️ Détection des Checkboxes par Label

Pour les checkboxes avec des labels complexes (Basic-Fit, Domino's), le système lit le texte du label :

```python
# Si le label contient "partenaire" ou "partner"
if any(kw in label_text for kw in ['partenaire', 'partner', 'promotions']):
    # Chercher la valeur correspondante dans le profil
    if 'partner_promo' in provided_values:
        return provided_values['partner_promo']  # True ou False
```

**Exemple** : 
- Label : "Oui, je souhaite recevoir des promotions des partenaires"
- Profil : `partner_promo: False`
- Résultat : La checkbox n'est PAS cochée ✅

---

## 🏠 Séparation des Champs d'Adresse

Pour les sites comme Basic-Fit qui ont des champs séparés :

```python
# Si le champ contient "numero" ou "number" (mais pas "phone")
if 'numero' in field_name and 'phone' not in field_name:
    value = "15"  # Juste le numéro

# Si le champ contient "rue" ou "street" (mais pas "number")
if 'rue' in field_name and 'number' not in field_name:
    value = "Rue de la Paix"  # Juste le nom de rue

# Si le champ contient "complement" ou "extra"
if 'complement' in field_name:
    value = "Appartement 3B"  # Le complément
```

**Résultat** :
| Champ | Valeur |
|-------|--------|
| Numéro | 15 |
| Rue | Rue de la Paix |
| Complément | Appartement 3B |
| Ville | Paris |

---

## 📊 Résultats des Tests

| Site | Champs détectés | Champs remplis | Taux |
|------|-----------------|----------------|------|
| HTTPBin Pizza | 6 | 6 | ✅ 100% |
| Basic-Fit | 15 | 14 | ✅ 93% |
| Air Arabia | 12 | 10 | ✅ 83% |
| Booking | 15 | 12 | ✅ 80% |
| Domino's | 5 | 5 | ✅ 100% |
| SNCF Connect | 3 | 3 | ✅ 100% |

---

## 🗂️ Structure du Projet

```
webscraping_project/
│
├── api_form_autofill_v5.py      # API principale (FastAPI + Selenium + Profils)
├── test_recherche_google.py     # Script de test avec interface Tkinter + Google
├── msedgedriver.exe             # Driver Selenium pour Edge
├── requirements_api.txt         # Dépendances Python
│
├── README.md                    # Cette documentation
└── rapport_version_amelioree.md # Rapport détaillé pour la soutenance
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

## 🛠️ Personnalisation

### Ajouter un nouveau profil

Dans `api_form_autofill_v5.py`, ajoutez dans `GENERIC_PROFILES` :

```python
'profile4': {
    'name': 'Profil 4 - Mon Nouveau Profil',
    'first_name': 'Pierre',
    'last_name': 'Durant',
    'email': 'pierre.durant@example.com',
    'phone': '+33698765432',
    'city': 'Marseille',
    'country': 'France',
    # ... autres champs
}
```

### Ajouter un nouveau type de champ

1. **Dans `FIELD_KEYWORDS`** :
```python
'mon_nouveau_champ': ['keyword1', 'keyword2', 'motcle']
```

2. **Dans les profils** :
```python
'mon_nouveau_champ': 'valeur_par_defaut'
```

### Ajouter des synonymes pour les radios

Dans `RADIO_VALUES` :
```python
'ma_valeur': ['ma_valeur', 'synonym1', 'synonym2', 'traduction']
```
