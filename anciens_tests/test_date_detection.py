#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify date field detection using Levenshtein distance.
This tests that FIELD_KEYWORDS is properly used for jour/mois/année fields.
"""

from difflib import SequenceMatcher
import re
from typing import Optional, Dict

# ===============================================
# Test FIELD_KEYWORDS and get_field_type
# ===============================================

FIELD_KEYWORDS = {
    'first_name': ['firstname', 'first_name', 'prenom', 'prénom', 'given', 'fname', 'vorname'],
    'last_name': ['lastname', 'last_name', 'nom', 'surname', 'family', 'lname', 'nachname'],
    'full_name': ['fullname', 'full_name', 'name', 'custname'],
    'gender': ['gender', 'sexe', 'sex', 'genre'],
    'title': ['title', 'civilité', 'civility', 'salutation'],
    
    # Contact
    'email': ['email', 'mail', 'courriel', 'e-mail'],
    'email_confirm': ['confirm', 'confirmez', 'verify', 'email2', 'emailconfirm'],
    'phone': ['phone', 'tel', 'telephone', 'mobile', 'gsm', 'portable'],
    
    # Adresse
    'zip': ['zip', 'postal', 'postcode', 'plz', 'code_postal', 'codepostal'],
    'street_number': ['numero', 'numéro', 'number', 'housenumber', 'streetnumber', 'no'],
    'street': ['rue', 'street', 'strasse', 'adresse', 'address'],
    'street_extra': ['complement', 'complément', 'extra', 'additional', 'zusatz', 'optionnel'],
    'city': ['city', 'ville', 'town', 'stadt', 'ort', 'locality'],
    'country': ['country', 'pays', 'land', 'nation'],
    
    # DATES - CRITICAL
    'date_of_birth': ['birthdate', 'dob', 'date_of_birth', 'dateofbirth', 'date_naissance'],
    'birth_day': ['day', 'jour', 'tag', 'birth_day', 'birthdate_day', 'day_of_birth'],
    'birth_month': ['month', 'mois', 'monat', 'birth_month', 'birthdate_month', 'month_of_birth'],
    'birth_year': ['year', 'année', 'an', 'jahr', 'birth_year', 'birthdate_year', 'year_of_birth'],
    
    # Auth
    'username': ['username', 'user', 'login', 'identifiant', 'pseudo', 'nickname'],
    'password': ['password', 'pwd', 'pass', 'mot_de_passe', 'mdp', 'secret'],
}


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Calculate Levenshtein ratio between two strings (0.0 to 1.0)"""
    matcher = SequenceMatcher(None, s1, s2)
    return matcher.ratio()


def get_field_type(field_name: str, threshold: float = 0.5) -> Optional[str]:
    """Detect field type using Levenshtein distance"""
    if not field_name:
        return None
    
    name_lower = field_name.lower().replace('-', '_').replace(' ', '_')
    best_type = None
    best_score = 0.0
    
    for field_type, keywords in FIELD_KEYWORDS.items():
        for kw in keywords:
            # Exact match scores higher
            if kw in name_lower:
                score = 0.95
            else:
                # Use Levenshtein
                score = levenshtein_ratio(name_lower, kw)
            
            if score > best_score:
                best_score = score
                best_type = field_type
    
    return best_type if best_score >= threshold else None


def parse_date_components(date_str: str) -> Optional[Dict[str, str]]:
    """Parse a date into components (day, month, year)"""
    if not date_str:
        return None
    
    # Format YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        parts = date_str.split('-')
        return {'day': parts[2], 'month': parts[1], 'year': parts[0]}
    
    # Format DD/MM/YYYY
    if re.match(r'\d{2}/\d{2}/\d{4}', date_str):
        parts = date_str.split('/')
        return {'day': parts[0], 'month': parts[1], 'year': parts[2]}
    
    return None


# ===============================================
# TEST CASES FOR DATE FIELD DETECTION
# ===============================================

test_cases = [
    # Common French field names
    ('jour', 'birth_day'),
    ('jour_naissance', 'birth_day'),
    ('jour_de_naissance', 'birth_day'),
    ('mois', 'birth_month'),
    ('mois_naissance', 'birth_month'),
    ('année', 'birth_year'),
    ('annee', 'birth_year'),
    ('année_naissance', 'birth_year'),
    
    # Common English field names
    ('day', 'birth_day'),
    ('day_of_birth', 'birth_day'),
    ('birth_day', 'birth_day'),
    ('birthdate_day', 'birth_day'),
    ('birthday_day', 'birth_day'),
    
    ('month', 'birth_month'),
    ('month_of_birth', 'birth_month'),
    ('birth_month', 'birth_month'),
    ('birthdate_month', 'birth_month'),
    
    ('year', 'birth_year'),
    ('year_of_birth', 'birth_year'),
    ('birth_year', 'birth_year'),
    ('birthdate_year', 'birth_year'),
    
    # German field names
    ('tag', 'birth_day'),
    ('monat', 'birth_month'),
    ('jahr', 'birth_year'),
    
    # ID attributes with underscores/dashes
    ('dob_day', 'birth_day'),
    ('dob-day', 'birth_day'),
    ('dob_month', 'birth_month'),
    ('dob_year', 'birth_year'),
    
    # Mixed case
    ('Jour', 'birth_day'),
    ('JOUR', 'birth_day'),
    ('Day', 'birth_day'),
    ('DAY', 'birth_day'),
]

print("=" * 80)
print("TESTING DATE FIELD DETECTION WITH LEVENSHTEIN DISTANCE")
print("=" * 80)

passed = 0
failed = 0

for field_name, expected_type in test_cases:
    detected_type = get_field_type(field_name, threshold=0.5)
    
    status = "[PASS]" if detected_type == expected_type else "[FAIL]"
    
    if detected_type == expected_type:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} | Field: '{field_name:20}' | Expected: {expected_type:15} | Got: {detected_type}")

print("\n" + "=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 80)

# ===============================================
# TEST DATE PARSING
# ===============================================

print("\n" + "=" * 80)
print("TESTING DATE PARSING")
print("=" * 80)

date_tests = [
    ('1990-01-15', {'day': '15', 'month': '01', 'year': '1990'}),
    ('15/01/1990', {'day': '15', 'month': '01', 'year': '1990'}),
    ('2000-12-25', {'day': '25', 'month': '12', 'year': '2000'}),
    ('25/12/2000', {'day': '25', 'month': '12', 'year': '2000'}),
]

for date_str, expected in date_tests:
    result = parse_date_components(date_str)
    status = "[PASS]" if result == expected else "[FAIL]"
    print(f"{status} | Date: '{date_str}' | Result: {result}")

# ===============================================
# TEST COMPLETE WORKFLOW
# ===============================================

print("\n" + "=" * 80)
print("TESTING COMPLETE WORKFLOW")
print("=" * 80)

# Simulate form fields and profile data
profile_data = {
    'date_of_birth': '1990-01-15',
    'birth_day': '15',
    'birth_month': '01',
    'birth_year': '1990',
}

values_lower = {k.lower(): v for k, v in profile_data.items()}

# Test field IDs that might appear on a form
field_ids_to_test = ['jour', 'mois', 'année', 'birthday_day', 'dob_month', 'year_of_birth']

print("\nFor profile data:", profile_data)
print("\nTesting field detection and value extraction:\n")

for field_id in field_ids_to_test:
    field_type = get_field_type(field_id, threshold=0.5)
    
    value = None
    if field_type in ['birth_day', 'birth_month', 'birth_year']:
        date_val = values_lower.get('date_of_birth')
        if date_val:
            parts = parse_date_components(date_val)
            if parts:
                if field_type == 'birth_day':
                    value = parts['day']
                elif field_type == 'birth_month':
                    value = parts['month']
                elif field_type == 'birth_year':
                    value = parts['year']
    
    print(f"Field: '{field_id:20}' | Type: {field_type:15} | Value: {value}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
