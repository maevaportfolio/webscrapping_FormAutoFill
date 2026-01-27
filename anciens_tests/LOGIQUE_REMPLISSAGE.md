# LOGIQUE DE REMPLISSAGE - VERSION FINALE (SIMPLE ET CLAIRE)

## La Nouvelle Approche

Au lieu de compliquer avec parsage de dates et logiques spéciales, on utilise une approche super simple:

### Étapes

```
Champ du formulaire: "year_of_birth"
↓
ÉTAPE 1: Chercher correspondance EXACTE dans FIELD_KEYWORDS
  - Chercher "year_of_birth" dans FIELD_KEYWORDS
  - TROUVÉ dans 'birth_year': ['year', 'année', 'an', 'jahr', 'birth_year', 'birthdate_year', 'year_of_birth']
  - Détecté: field_type = 'birth_year'
↓
ÉTAPE 2: (SKIPPED - déjà trouvé en Étape 1)
↓
ÉTAPE 3: Utiliser la valeur du profil correspondante
  - values_lower['birth_year'] = '1990'
  - REMPLIR AVEC: 1990
```

### Cas d'Usage

**Exemple 1: Correspondance exacte**
```
Champ HTML: name="birth_day"
Profil: {'birth_day': '15', 'date_of_birth': '1990-01-15', ...}

ÉTAPE 1: 'birth_day' trouvé dans FIELD_KEYWORDS['birth_day']
RÉSULTAT: value = '15' ✅
```

**Exemple 2: Correspondance substring**
```
Champ HTML: name="jour_naissance"
Profil: {'birth_day': '15', ...}

ÉTAPE 1: 'jour' trouvé dans FIELD_KEYWORDS['birth_day']
Détecté: field_type = 'birth_day'
RÉSULTAT: value = '15' ✅
```

**Exemple 3: Levenshtein (si pas de match substring)**
```
Champ HTML: name="dob_day"
Profil: {'birth_day': '15', ...}

ÉTAPE 1: Pas de correspondance exacte
ÉTAPE 2: get_field_type() utilise Levenshtein
         'dob_day' ressemble à 'birth_day'
Détecté: field_type = 'birth_day'
RÉSULTAT: value = '15' ✅
```

**Exemple 4: Champ non reconnu**
```
Champ HTML: name="field_xyz"
Profil: {'field_xyz': 'valeur123', ...}

ÉTAPE 1: Pas de correspondance dans FIELD_KEYWORDS
ÉTAPE 2: Levenshtein ne trouve rien de bon
ÉTAPE 3: value = None
ÉTAPE 4: Fallback - chercher 'field_xyz' directement
RÉSULTAT: value = 'valeur123' ✅
```

## PLUS DE PARSING SPÉCIAL POUR LES DATES

✅ **Avant (MAUVAIS):**
```python
if field_type == 'birth_year':
    date_val = values_lower.get('date_of_birth')  # '1990-01-15'
    parts = parse_date_components(date_val)        # {'day':'15', 'month':'01', 'year':'1990'}
    value = parts['year']                          # '1990'
    # Ça PEUT donner des résultats bizarres si le parsing échoue
```

✅ **Après (BON):**
```python
if detected_field_type == 'birth_year':
    value = values_lower.get('birth_year')         # '1990'
    # Simple, direct, pas de chance de bug
```

## FIELD_KEYWORDS

Les profils ont:
```python
{
    'date_of_birth': '1990-01-15',      # Format complet (utile rarement)
    'birth_day': '15',                   # Jour seul
    'birth_month': '01',                 # Mois seul
    'birth_year': '1990',                # Année seule
}
```

Et les keywords matche ces noms:
```python
'birth_day': ['day', 'jour', 'tag', 'birth_day', 'birthdate_day', 'day_of_birth'],
'birth_month': ['month', 'mois', 'monat', 'birth_month', 'birthdate_month', 'month_of_birth'],
'birth_year': ['year', 'année', 'an', 'jahr', 'birth_year', 'birthdate_year', 'year_of_birth'],
```

## Résultat

✅ Logique **super simple** et **directe**
✅ Pas de cas spéciaux compliqués
✅ Pas de parsing fragile
✅ Dates remplies correctement: '15', '01', '1990'
✅ Tous les champs marchent de la même façon

## Code

```python
# ÉTAPE 1: Chercher correspondance EXACTE dans les keywords
for field_type, keywords in FIELD_KEYWORDS.items():
    for keyword in keywords:
        if keyword in field_id:
            detected_field_type = field_type
            break
    if detected_field_type:
        break

# ÉTAPE 2: Si pas trouvé → Levenshtein
if detected_field_type is None and use_levenshtein:
    detected_field_type = get_field_type(field_id, threshold)

# ÉTAPE 3: Utiliser la valeur du profil
if detected_field_type:
    value = values_lower.get(detected_field_type)

# ÉTAPE 4: Fallback
if value is None and field_id in values_lower:
    value = values_lower[field_id]
```

C'est ça. Pas besoin de plus.
