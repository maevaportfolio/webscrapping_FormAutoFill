# 🚀 GUIDE RAPIDE - Démarrer le remplissage de formulaires

## ⚡ Démarrage rapide

### Terminal 1 - Démarrer l'API
```bash
cd "c:\Users\HK6691\OneDrive - ENGIE\Bureau\webscraping_project"
python api_form_autofill.py
```

Ou si tu as un virtualenv activé:
```bash
uvicorn api_form_autofill:app --reload
```

Tu devrais voir:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Lancer le test
```bash
cd "c:\Users\HK6691\OneDrive - ENGIE\Bureau\webscraping_project"
python test_simple.py
```

## 🎯 Ce qui se passe

1. **Création de session** - Un navigateur Edge s'ouvre
2. **Chargement du formulaire** - La page se charge
3. **Remplissage automatique** - Les champs sont remplis avec:
   - Prénom, nom, email, téléphone
   - Adresse, ville, code postal
   - **Passeport**: 12345678
   - **Date de naissance**: 1990-01-15
   - **Pays**: France (auto-détecté)
   - **Civilité**: Madame (auto-détecté)

4. **Résumé** - Tu vois exactement ce qui a été rempli
5. **Navigation libre** - Le navigateur reste ouvert ✨

## 📝 Personnaliser les valeurs

Édite `test_simple.py` et modifie:

```python
TARGET_URL = "https://ton-site.com"  # ← Change l'URL

FORM_VALUES = {
    "first_name": "Ton Prénom",
    "last_name": "Ton Nom",
    "email": "ton@email.com",
    # etc...
}
```

Puis relance: `python test_simple.py`

## 🔄 Navigation en cours de session

Tu peux naviguer vers d'autres pages:
```bash
curl -X POST "http://localhost:8000/session/test_session/navigate?url=https://google.com"
```

Ou directement depuis le navigateur (clic, scrolling, etc.)

## 🛑 Arrêter

- **Ferme le navigateur** quand tu as terminé
- **Appuie sur Ctrl+C** dans les terminaux API et test

## ⚠️ Troubleshooting

### "Impossible de se connecter à l'API"
→ L'API n'est pas démarrée. Vérifie Terminal 1.

### Le formulaire ne se remplit pas
→ Les champs ne sont pas reconnus. Tu peux:
- Ajouter des keywords dans `COMMON_FIELD_KEYWORDS`
- Augmenter le seuil Levenshtein dans le test

### Driver pas trouvé
→ Vérifie le chemin `DRIVER_PATH` dans `api_form_autofill.py`

## 📚 Documentation complète

Voir `MODIFICATIONS.md` pour tous les détails techniques.

---
Happy form filling! 🎉
