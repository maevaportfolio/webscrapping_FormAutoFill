
# 📋 Form AutoFill - Système de Détection et Remplissage Automatique de Formulaires

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Objectif du Projet

Créer un système intelligent qui :

| # | Fonctionnalité | Description |
|---|----------------|-------------|
| 1 | **Détection automatique** | Trouve les formulaires sur n'importe quel site web |
| 2 | **Identification des champs** | Reconnaît nom, prénom, email, téléphone, adresse... |
| 3 | **Remplissage automatique** | Insère les données utilisateur dans les champs |
| 4 | **API REST** | Expose les fonctionnalités pour industrialisation |
| 5 | **Extension navigateur** | Utilisation en temps réel (bonus) |

---

## 🎯 Résultat Final

```
AVANT (sans le projet)          APRÈS (avec le projet)
─────────────────────          ────────────────────────

Tu vas sur un site      →      Tu vas sur un site

Tu remplis à la main :         Tu cliques sur l'extension :
- Prénom: [________]           - 1 clic "Détecter"
- Nom: [___________]           - 1 clic "Remplir"
- Email: [_________]
- Téléphone: [_____]           → TOUT SE REMPLIT AUTOMATIQUEMENT

⏱️ 2-3 minutes                 ⏱️ 2 secondes
```

---

## 🗂️ Structure du Projet

```
form-autofill-project/
│
├── src/
│   ├── detectors/
│   │   └── form_detector.py      # Détection des formulaires HTML
│   ├── classifiers/
│   │   └── field_classifier.py   # Classification avec Levenshtein
│   ├── fillers/
│   │   └── form_filler.py        # Remplissage automatique
│   └── api/
│       └── main.py               # API REST FastAPI
│
├── extension/                     # Extension Chrome/Firefox
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   └── content.js
│
├── notebooks/
│   └── projet_formulaires.ipynb  # Notebook de démonstration
│
├── tests/
│   └── test_all.py               # Tests unitaires
│
├── test_demo.py                  # Script de test rapide
├── requirements.txt              # Dépendances Python
├── Dockerfile                    # Conteneurisation
└── README.md
```

---

## 🚀 Guide d'Installation et d'Utilisation

### Prérequis

- Python 3.10 ou supérieur
- pip (gestionnaire de packages)
- Chrome ou Firefox (pour l'extension)

---

### 📥 Étape 1 : Installation (une seule fois)

```bash
# Cloner le repository
git clone https://github.com/votre-username/form-autofill-project.git
cd form-autofill-project

# Installer les dépendances
pip install -r requirements.txt
```

---

### ▶️ Étape 2 : Lancer l'API

Ouvre un terminal et lance :

```bash
uvicorn src.api.main:app --reload --port 8000
```

✅ **Vérification** : Va sur http://localhost:8000/docs - tu dois voir la documentation Swagger.

> ⚠️ **Important** : Garde ce terminal ouvert pendant toute l'utilisation !

---

### 👤 Étape 3 : Configurer tes données personnelles

#### Option A : Via PowerShell (Windows)

Ouvre un **nouveau terminal** et exécute :

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/user-data" -Method POST -ContentType "application/json" -Body '{"firstname":"Maeva","lastname":"Dupont","email":"maeva.dupont@example.com","phone":"+33 6 12 34 56 78","birthdate":"2000-01-15","address":"123 Rue de la Paix","city":"Paris","zipcode":"75001","country":"France"}'
```

#### Option B : Via le navigateur (plus simple ✨)

1. Va sur http://localhost:8000/docs
2. Clique sur `POST /api/user-data`
3. Clique sur `Try it out`
4. Modifie le JSON avec tes informations :

```json
{
  "firstname": "Ton Prénom",
  "lastname": "Ton Nom",
  "email": "ton.email@example.com",
  "phone": "+33 6 XX XX XX XX",
  "birthdate": "AAAA-MM-JJ",
  "address": "Ton Adresse",
  "city": "Ta Ville",
  "zipcode": "Code Postal",
  "country": "France"
}
```

5. Clique sur `Execute`

✅ **Succès** : Tu verras `"message": "Données utilisateur enregistrées avec succès"`

---

### 🧪 Étape 4 : Tester sur un site web

1. Va sur http://localhost:8000/docs
2. Clique sur `POST /api/fill-form`
3. Clique sur `Try it out`
4. Entre l'URL d'un site avec un formulaire :

```json
{
  "url": "https://httpbin.org/forms/post",
  "user_id": "default"
}
```

5. Clique sur `Execute`
6. Regarde le résultat `fill_mapping` :

```json
{
  "success": true,
  "fill_mapping": {
    "#custname": "Maeva Dupont",
    "#custemail": "maeva.dupont@example.com",
    "#custtel": "+33 6 12 34 56 78"
  }
}
```

✅ **Ça fonctionne !** Le système a détecté les champs et préparé les valeurs.

---

### 🌐 Étape 5 (Bonus) : Installer l'extension Chrome

1. Ouvre Chrome
2. Tape `chrome://extensions/` dans la barre d'adresse
3. Active le **"Mode développeur"** (en haut à droite)
4. Clique sur **"Charger l'extension non empaquetée"**
5. Sélectionne le dossier `extension/` du projet

#### Utilisation de l'extension

1. Va sur un site avec un formulaire (ex: https://httpbin.org/forms/post)
2. Clique sur l'icône de l'extension 📝
3. Clique **"Détecter les formulaires"**
4. Clique **"Remplir automatiquement"**
5. ✨ Les champs se remplissent !

---

## 📊 Résultats des Tests

Le système a été testé sur plusieurs types de formulaires :

| Site / Formulaire | Champs détectés | Champs remplis | Taux de réussite |
|-------------------|-----------------|----------------|------------------|
| HTTPBin (test) | 3 | 3 | ✅ 100% |
| Formulaire d'inscription | 6 | 5 | ✅ 83% |
| Formulaire e-commerce | 7 | 7 | ✅ 100% |
| Formulaire français | 6 | 6 | ✅ 100% |
| **Clarins.fr (réel)** | 11 | 8 | ✅ 73% |
| **TOTAL** | **33** | **29** | ✅ **88%** |

> Le champ "mot de passe" est exclu volontairement pour des raisons de sécurité.

---

## 🔧 Architecture Technique

### Pipeline de traitement

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   URL du    │     │   Détection     │     │  Classification │
│    site     │────▶│  BeautifulSoup  │────▶│   Levenshtein   │
└─────────────┘     └─────────────────┘     └─────────────────┘
                                                     │
                                                     ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Extension  │◀────│    API REST     │◀────│   Remplissage   │
│  Navigateur │     │    FastAPI      │     │    Mapping      │
└─────────────┘     └─────────────────┘     └─────────────────┘
```

### Distance de Levenshtein

L'algorithme compare les noms de champs avec des mots-clés connus :

```
"prenom"      ≈ "firstname"  → 85% similarité → Type: FIRSTNAME
"email"       = "email"      → 100% match     → Type: EMAIL
"telephone"   ≈ "phone"      → 80% similarité → Type: PHONE
```

### Endpoints de l'API

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/detect-form` | POST | Détecte et classifie les formulaires d'une URL |
| `/api/fill-form` | POST | Retourne le mapping de remplissage |
| `/api/user-data` | GET | Récupère les données utilisateur |
| `/api/user-data` | POST | Configure les données utilisateur |
| `/health` | GET | Vérifie que l'API fonctionne |

---

## 📝 Explication du Code

### 1. Détection (`src/detectors/form_detector.py`)

```python
detector = FormDetector()
forms = detector.detect_from_url("https://example.com/register")

# Résultat : Liste de tous les <input>, <select>, <textarea>
```

### 2. Classification (`src/classifiers/field_classifier.py`)

```python
classifier = FieldClassifier()
result = classifier.classify({"name": "prenom", "type": "text"})

# Résultat : type=FIRSTNAME, confiance=100%
```

### 3. Remplissage (`src/fillers/form_filler.py`)

```python
user = UserData(firstname="Maeva", email="maeva@example.com")
filler = FormFiller(user)
mapping = filler.fill_fields(classified_fields)

# Résultat : {"#prenom": "Maeva", "#email": "maeva@example.com"}
```

---

## ⚠️ Limites Connues

| Limite | Raison | Solution possible |
|--------|--------|-------------------|
| Sites avec CAPTCHA | Protection anti-bot | Intervention manuelle |
| Formulaires React/Vue | JavaScript dynamique | Utiliser Selenium |
| Sites avec authentification | Accès bloqué | Cookies de session |
| iFrames | Contenu isolé | Analyse récursive |

---

## 🧪 Exécuter les Tests

```bash
# Test rapide (sans dépendances externes)
python test_demo.py

# Tests unitaires complets
pytest tests/ -v
```

---

## 🐳 Docker (Optionnel)

```bash
# Construire l'image
docker build -t form-autofill-api .

# Lancer le conteneur
docker run -p 8000:8000 form-autofill-api
```

---

## 📚 Glossaire

| Terme | Définition |
|-------|------------|
| `localhost` | Ton propre ordinateur |
| `:8000` | Le port où l'API écoute |
| `/docs` | Documentation Swagger auto-générée |
| `user_id: "default"` | Identifiant de tes données sauvegardées |
| Levenshtein | Algorithme mesurant la similarité entre chaînes |

---

## 👤 Auteur


---

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE) pour plus de détails.
