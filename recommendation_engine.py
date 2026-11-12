"""Drug Recommendation Engine — Production-Ready"""

import numpy as np
import pandas as pd
from config import TOP_K_RECOMMENDATIONS, CONFIDENCE_THRESHOLD


class DrugDatabase:
    """Comprehensive drug database with condition-to-drug mapping"""
    
    def __init__(self):
        self.drugs = {}
        self.drug_ratings = {}
        self.drug_side_effects = {}
        self.condition_to_drugs = {}
        self._initialize_drug_database()
    
    def _initialize_drug_database(self):
        """Initialize with a production-grade drug catalogue (55+ medications)"""
        sample_drugs = [
            # ── Critical / General Advice (Special IDs) ──────────────────────
            {'id': 999, 'name': 'CONSULT DOCTOR IMMEDIATELY', 'category': 'critical', 'base_rating': 5.0},
            {'id': 998, 'name': 'General Health Advice', 'category': 'general_health', 'base_rating': 4.5},

            # ── Analgesics / Pain Relief ─────────────────────────────────────
            {'id': 0, 'name': 'Aspirin', 'category': 'pain_relief', 'base_rating': 4.2},
            {'id': 1, 'name': 'Ibuprofen', 'category': 'pain_relief', 'base_rating': 4.5},
            {'id': 2, 'name': 'Paracetamol', 'category': 'pain_relief', 'base_rating': 4.3},
            {'id': 3, 'name': 'Naproxen', 'category': 'pain_relief', 'base_rating': 4.0},
            {'id': 39, 'name': 'Diclofenac', 'category': 'pain_relief', 'base_rating': 4.1},
            {'id': 40, 'name': 'Tramadol', 'category': 'pain_relief', 'base_rating': 3.8},

            # ── Antibiotics ──────────────────────────────────────────────────
            {'id': 4, 'name': 'Amoxicillin', 'category': 'antibiotic', 'base_rating': 4.3},
            {'id': 5, 'name': 'Ciprofloxacin', 'category': 'antibiotic', 'base_rating': 4.0},
            {'id': 6, 'name': 'Azithromycin', 'category': 'antibiotic', 'base_rating': 4.4},
            {'id': 7, 'name': 'Doxycycline', 'category': 'antibiotic', 'base_rating': 4.2},
            {'id': 41, 'name': 'Metronidazole', 'category': 'antibiotic', 'base_rating': 4.0},
            {'id': 42, 'name': 'Cephalexin', 'category': 'antibiotic', 'base_rating': 4.1},
            {'id': 43, 'name': 'Clindamycin', 'category': 'antibiotic', 'base_rating': 3.9},

            # ── Antimalarials ────────────────────────────────────────────────
            {'id': 8, 'name': 'Chloroquine', 'category': 'antimalarial', 'base_rating': 4.3},
            {'id': 9, 'name': 'Artemether-Lumefantrine', 'category': 'antimalarial', 'base_rating': 4.7},
            {'id': 10, 'name': 'Quinine', 'category': 'antimalarial', 'base_rating': 4.0},
            {'id': 11, 'name': 'Mefloquine', 'category': 'antimalarial', 'base_rating': 3.9},
            {'id': 12, 'name': 'Atovaquone-Proguanil', 'category': 'antimalarial', 'base_rating': 4.5},

            # ── Antivirals ───────────────────────────────────────────────────
            {'id': 13, 'name': 'Oseltamivir (Tamiflu)', 'category': 'antiviral', 'base_rating': 4.2},
            {'id': 14, 'name': 'Acyclovir', 'category': 'antiviral', 'base_rating': 4.1},
            {'id': 44, 'name': 'Remdesivir', 'category': 'antiviral', 'base_rating': 3.9},

            # ── Antipyretics / Fever ─────────────────────────────────────────
            {'id': 15, 'name': 'Acetaminophen', 'category': 'fever', 'base_rating': 4.4},

            # ── Diabetes ─────────────────────────────────────────────────────
            {'id': 16, 'name': 'Metformin', 'category': 'diabetes', 'base_rating': 4.4},
            {'id': 17, 'name': 'Insulin Glargine', 'category': 'diabetes', 'base_rating': 4.5},
            {'id': 18, 'name': 'Glimepiride', 'category': 'diabetes', 'base_rating': 4.1},
            {'id': 45, 'name': 'Sitagliptin', 'category': 'diabetes', 'base_rating': 4.0},

            # ── Hypertension ─────────────────────────────────────────────────
            {'id': 19, 'name': 'Lisinopril', 'category': 'hypertension', 'base_rating': 4.2},
            {'id': 20, 'name': 'Amlodipine', 'category': 'hypertension', 'base_rating': 4.3},
            {'id': 21, 'name': 'Losartan', 'category': 'hypertension', 'base_rating': 4.1},
            {'id': 46, 'name': 'Atenolol', 'category': 'hypertension', 'base_rating': 4.0},

            # ── Cholesterol ──────────────────────────────────────────────────
            {'id': 22, 'name': 'Atorvastatin', 'category': 'cholesterol', 'base_rating': 4.3},
            {'id': 23, 'name': 'Rosuvastatin', 'category': 'cholesterol', 'base_rating': 4.4},

            # ── Acid Reflux / Gastric ────────────────────────────────────────
            {'id': 24, 'name': 'Omeprazole', 'category': 'acid_reflux', 'base_rating': 4.0},
            {'id': 25, 'name': 'Pantoprazole', 'category': 'acid_reflux', 'base_rating': 4.1},
            {'id': 47, 'name': 'Ranitidine', 'category': 'antacid', 'base_rating': 3.9},
            {'id': 48, 'name': 'Aluminum Hydroxide', 'category': 'antacid', 'base_rating': 3.7},

            # ── Allergy / Antihistamines ─────────────────────────────────────
            {'id': 26, 'name': 'Loratadine', 'category': 'allergy', 'base_rating': 4.1},
            {'id': 27, 'name': 'Cetirizine', 'category': 'allergy', 'base_rating': 4.2},
            {'id': 49, 'name': 'Fexofenadine', 'category': 'allergy', 'base_rating': 4.0},

            # ── Respiratory / Cough / Bronchodilator ─────────────────────────
            {'id': 28, 'name': 'Dextromethorphan', 'category': 'cough', 'base_rating': 3.9},
            {'id': 29, 'name': 'Guaifenesin', 'category': 'expectorant', 'base_rating': 3.8},
            {'id': 30, 'name': 'Salbutamol', 'category': 'bronchodilator', 'base_rating': 4.3},
            {'id': 50, 'name': 'Montelukast', 'category': 'bronchodilator', 'base_rating': 4.1},

            # ── Autoimmune ───────────────────────────────────────────────────
            {'id': 31, 'name': 'Hydroxychloroquine', 'category': 'autoimmune', 'base_rating': 3.8},

            # ── Thyroid ──────────────────────────────────────────────────────
            {'id': 32, 'name': 'Levothyroxine', 'category': 'thyroid', 'base_rating': 4.4},

            # ── Antidepressants / Anxiolytics ────────────────────────────────
            {'id': 33, 'name': 'Sertraline', 'category': 'antidepressant', 'base_rating': 4.1},
            {'id': 34, 'name': 'Fluoxetine', 'category': 'antidepressant', 'base_rating': 4.0},
            {'id': 51, 'name': 'Escitalopram', 'category': 'antidepressant', 'base_rating': 4.2},
            {'id': 52, 'name': 'Alprazolam', 'category': 'sedative', 'base_rating': 3.7},

            # ── Antifungals / Dermatology ────────────────────────────────────
            {'id': 35, 'name': 'Clotrimazole', 'category': 'antifungal', 'base_rating': 4.0},
            {'id': 36, 'name': 'Hydrocortisone Cream', 'category': 'skin', 'base_rating': 4.1},
            {'id': 53, 'name': 'Ketoconazole', 'category': 'antifungal', 'base_rating': 3.9},

            # ── GI / Antidiarrheal / Rehydration ─────────────────────────────
            {'id': 37, 'name': 'Loperamide', 'category': 'antidiarrheal', 'base_rating': 4.0},
            {'id': 38, 'name': 'ORS (Oral Rehydration Salts)', 'category': 'rehydration', 'base_rating': 4.6},
            {'id': 54, 'name': 'Bisacodyl', 'category': 'laxative', 'base_rating': 3.8},

            # ── Anticonvulsants / Epilepsy ───────────────────────────────────
            {'id': 55, 'name': 'Gabapentin', 'category': 'anticonvulsant', 'base_rating': 4.0},
            {'id': 56, 'name': 'Pregabalin', 'category': 'anticonvulsant', 'base_rating': 4.1},

            # ── Muscle Relaxants ─────────────────────────────────────────────
            {'id': 57, 'name': 'Cyclobenzaprine', 'category': 'muscle_relaxant', 'base_rating': 3.9},
            {'id': 58, 'name': 'Tizanidine', 'category': 'muscle_relaxant', 'base_rating': 3.8},

            # ── Antiemetics ──────────────────────────────────────────────────
            {'id': 59, 'name': 'Ondansetron', 'category': 'antiemetic', 'base_rating': 4.3},
            {'id': 60, 'name': 'Domperidone', 'category': 'antiemetic', 'base_rating': 4.0},

            # ── Anticoagulants ───────────────────────────────────────────────
            {'id': 61, 'name': 'Warfarin', 'category': 'anticoagulant', 'base_rating': 4.0},
            {'id': 62, 'name': 'Rivaroxaban', 'category': 'anticoagulant', 'base_rating': 4.2},

            # ── Corticosteroids ──────────────────────────────────────────────
            {'id': 63, 'name': 'Prednisolone', 'category': 'corticosteroid', 'base_rating': 4.0},
            {'id': 64, 'name': 'Dexamethasone', 'category': 'corticosteroid', 'base_rating': 4.2},

            # ── Supplements ──────────────────────────────────────────────────
            {'id': 65, 'name': 'Ferrous Sulfate (Iron)', 'category': 'iron_supplement', 'base_rating': 4.0},
            {'id': 66, 'name': 'Vitamin D3 (Cholecalciferol)', 'category': 'supplement', 'base_rating': 4.3},
        ]
        
        for drug in sample_drugs:
            self.drugs[drug['id']] = drug
            self.drug_ratings[drug['id']] = drug['base_rating']
            self.drug_side_effects[drug['id']] = self._get_side_effects(drug['name'])
        
        # Map conditions to relevant drug categories (condition keywords → list of categories)
        self.condition_to_drugs = {
            # Critical / Emergency
            'heart':         ['critical'],
            'cardiac':       ['critical'],
            'stroke':        ['critical'],
            'attack':        ['critical'],
            'breathing':     ['critical'],
            'difficulty breathing': ['critical'],
            'chest pain':    ['critical'],
            'emergency':     ['critical'],
            'unconscious':   ['critical'],
            
            # General / Vague
            'general':       ['general_health', 'pain_relief'],
            'checkup':       ['general_health'],
            'wellness':      ['general_health'],
            'healthy':       ['general_health'],
            'weakness':      ['general_health', 'rehydration'],
            'fatigue':       ['general_health', 'rehydration'],
            
            # Specific Conditions
            'malaria':       ['antimalarial', 'fever', 'pain_relief'],
            'fever':         ['fever', 'pain_relief'],
            'temperature':   ['fever', 'pain_relief'],
            'headache':      ['pain_relief'],
            'pain':          ['pain_relief'],
            'infection':     ['antibiotic'],
            'bacterial':     ['antibiotic'],
            'flu':           ['antiviral', 'fever', 'pain_relief'],
            'influenza':     ['antiviral', 'fever', 'pain_relief'],
            'cold':          ['cough', 'expectorant', 'fever', 'allergy'],
            'cough':         ['cough', 'expectorant', 'bronchodilator'],
            'asthma':        ['bronchodilator'],
            'diabetes':      ['diabetes'],
            'blood sugar':   ['diabetes'],
            'hypertension':  ['hypertension'],
            'blood pressure':['hypertension'],
            'bp':            ['hypertension'],
            'cholesterol':   ['cholesterol'],
            'acid':          ['acid_reflux'],
            'reflux':        ['acid_reflux'],
            'gerd':          ['acid_reflux'],
            'gastric':       ['acid_reflux'],
            'allergy':       ['allergy'],
            'allergic':      ['allergy'],
            'autoimmune':    ['autoimmune'],
            'thyroid':       ['thyroid'],
            'depression':    ['antidepressant'],
            'anxiety':       ['antidepressant'],
            'diarrhea':      ['antidiarrheal', 'rehydration'],
            'dehydration':   ['rehydration'],
            'skin':          ['skin', 'antifungal'],
            'fungal':        ['antifungal'],
            'rash':          ['skin', 'allergy'],
            'vomit':         ['rehydration', 'acid_reflux', 'antiemetic'],
            'nausea':        ['acid_reflux', 'rehydration', 'antiemetic'],
            'body ache':     ['pain_relief', 'fever'],
            'muscle':        ['pain_relief', 'muscle_relaxant'],
            'muscle spasm':  ['muscle_relaxant'],
            'joint':         ['pain_relief'],
            'sore throat':   ['antibiotic', 'pain_relief'],
            'chest':         ['bronchodilator'],
            'seizure':       ['anticonvulsant'],
            'epilepsy':      ['anticonvulsant'],
            'convulsion':    ['anticonvulsant'],
            'nerve':         ['anticonvulsant', 'pain_relief'],
            'neuropathy':    ['anticonvulsant'],
            'spasm':         ['muscle_relaxant'],
            'stiffness':     ['muscle_relaxant', 'pain_relief'],
            'clot':          ['anticoagulant'],
            'dvt':           ['anticoagulant'],
            'thrombosis':    ['anticoagulant'],
            'inflammation':  ['corticosteroid', 'pain_relief'],
            'swelling':      ['corticosteroid', 'pain_relief'],
            'anemia':        ['iron_supplement'],
            'iron':          ['iron_supplement'],
            'vitamin':       ['supplement'],
            'constipation':  ['laxative'],
            'sedation':      ['sedative'],
            'insomnia':      ['sedative'],
            'sleep':         ['sedative'],
        }
    
    def _get_side_effects(self, drug_name):
        """Get side effects for drug"""
        side_effects = {
            'Aspirin': ['stomach irritation', 'allergic reactions', 'bleeding risk'],
            'Ibuprofen': ['stomach upset', 'dizziness', 'headache'],
            'Paracetamol': ['liver damage (overdose)', 'allergic reactions'],
            'Naproxen': ['stomach upset', 'dizziness', 'drowsiness'],
            'Amoxicillin': ['allergic reactions', 'diarrhea', 'nausea'],
            'Ciprofloxacin': ['tendon damage', 'photosensitivity', 'diarrhea'],
            'Azithromycin': ['diarrhea', 'nausea', 'abdominal pain'],
            'Doxycycline': ['photosensitivity', 'nausea', 'esophageal irritation'],
            'Chloroquine': ['retinal toxicity', 'nausea', 'headache'],
            'Artemether-Lumefantrine': ['headache', 'dizziness', 'anorexia'],
            'Quinine': ['cinchonism', 'hypoglycemia', 'cardiac arrhythmia'],
            'Mefloquine': ['vivid dreams', 'anxiety', 'dizziness'],
            'Atovaquone-Proguanil': ['abdominal pain', 'nausea', 'headache'],
            'Oseltamivir (Tamiflu)': ['nausea', 'vomiting', 'headache'],
            'Acyclovir': ['nausea', 'diarrhea', 'headache'],
            'Acetaminophen': ['liver damage (overdose)', 'allergic reactions'],
            'Metformin': ['gastrointestinal issues', 'vitamin B12 deficiency'],
            'Insulin Glargine': ['hypoglycemia', 'injection site reactions'],
            'Glimepiride': ['hypoglycemia', 'weight gain', 'dizziness'],
            'Lisinopril': ['dry cough', 'dizziness', 'low blood pressure'],
            'Amlodipine': ['ankle swelling', 'flushing', 'headache'],
            'Losartan': ['dizziness', 'hyperkalemia', 'fatigue'],
            'Atorvastatin': ['muscle pain', 'liver changes', 'memory issues'],
            'Rosuvastatin': ['muscle pain', 'headache', 'constipation'],
            'Omeprazole': ['headache', 'nausea', 'diarrhea'],
            'Pantoprazole': ['headache', 'diarrhea', 'nausea'],
            'Loratadine': ['drowsiness', 'dry mouth', 'headache'],
            'Cetirizine': ['drowsiness', 'dry mouth', 'fatigue'],
            'Dextromethorphan': ['drowsiness', 'dizziness', 'nausea'],
            'Guaifenesin': ['nausea', 'vomiting', 'dizziness'],
            'Salbutamol': ['tremor', 'palpitations', 'headache'],
            'Hydroxychloroquine': ['vision problems', 'headache', 'nausea'],
            'Levothyroxine': ['tremor', 'weight loss', 'increased heart rate'],
            'Sertraline': ['insomnia', 'sexual dysfunction', 'weight changes'],
            'Fluoxetine': ['insomnia', 'nausea', 'drowsiness'],
            'Clotrimazole': ['skin irritation', 'burning sensation'],
            'Hydrocortisone Cream': ['skin thinning', 'burning', 'itching'],
            'Loperamide': ['constipation', 'abdominal pain', 'dizziness'],
            'ORS (Oral Rehydration Salts)': ['minimal side effects'],
            'Diclofenac': ['stomach pain', 'nausea', 'increased blood pressure'],
            'Tramadol': ['dizziness', 'nausea', 'constipation', 'dependence risk'],
            'Metronidazole': ['nausea', 'metallic taste', 'diarrhea'],
            'Cephalexin': ['diarrhea', 'stomach pain', 'rash'],
            'Clindamycin': ['diarrhea', 'nausea', 'C. difficile risk'],
            'Remdesivir': ['nausea', 'elevated liver enzymes', 'infusion reactions'],
            'Sitagliptin': ['upper respiratory infection', 'headache', 'pancreatitis risk'],
            'Atenolol': ['fatigue', 'cold extremities', 'dizziness'],
            'Ranitidine': ['headache', 'dizziness', 'constipation'],
            'Aluminum Hydroxide': ['constipation', 'nausea', 'phosphate depletion'],
            'Fexofenadine': ['headache', 'nausea', 'dizziness'],
            'Montelukast': ['headache', 'mood changes', 'abdominal pain'],
            'Escitalopram': ['nausea', 'insomnia', 'sexual dysfunction'],
            'Alprazolam': ['drowsiness', 'dependence risk', 'memory impairment'],
            'Ketoconazole': ['nausea', 'liver toxicity risk', 'headache'],
            'Bisacodyl': ['abdominal cramps', 'diarrhea', 'nausea'],
            'Gabapentin': ['dizziness', 'drowsiness', 'peripheral edema'],
            'Pregabalin': ['dizziness', 'drowsiness', 'weight gain'],
            'Cyclobenzaprine': ['drowsiness', 'dry mouth', 'dizziness'],
            'Tizanidine': ['drowsiness', 'dry mouth', 'low blood pressure'],
            'Ondansetron': ['headache', 'constipation', 'fatigue'],
            'Domperidone': ['dry mouth', 'headache', 'QT prolongation risk'],
            'Warfarin': ['bleeding risk', 'bruising', 'drug interactions'],
            'Rivaroxaban': ['bleeding risk', 'headache', 'dizziness'],
            'Prednisolone': ['weight gain', 'mood swings', 'increased blood sugar'],
            'Dexamethasone': ['insomnia', 'increased appetite', 'mood changes'],
            'Ferrous Sulfate (Iron)': ['constipation', 'nausea', 'dark stools'],
            'Vitamin D3 (Cholecalciferol)': ['minimal side effects at standard doses'],
        }
        return side_effects.get(drug_name, ['minimal side effects'])
    
    def get_drug(self, drug_id):
        """Get drug information"""
        return self.drugs.get(drug_id)
    
    def get_drugs_by_category(self, category):
        """Get all drugs in a category"""
        return [drug for drug in self.drugs.values() if drug['category'] == category]
    
    def get_drugs_by_categories(self, categories):
        """Get all drugs matching any of the given categories"""
        return [drug for drug in self.drugs.values() if drug['category'] in categories]
    
    def update_rating(self, drug_id, new_rating):
        """Update drug rating based on feedback"""
        if drug_id in self.drug_ratings:
            alpha = 0.1
            current_rating = self.drug_ratings[drug_id]
            self.drug_ratings[drug_id] = current_rating + alpha * (new_rating - current_rating)
    
    def get_all_drugs(self):
        """Get all drugs"""
        return list(self.drugs.values())


class RecommendationEngine:
    """Production-grade drug recommendation engine with condition-aware matching"""
    
    def __init__(self):
        self.drug_db = DrugDatabase()
        self.user_history = {}
        self.recommendation_scores = {}
        
    def recommend(self, patient_condition, sentiment_score, confidence, top_k=TOP_K_RECOMMENDATIONS):
        """
        Generate drug recommendations based on patient condition and sentiment.
        
        Matches the condition text against known condition keywords to find
        appropriate drug categories, then scores candidates using a composite
        of base rating, sentiment, and confidence.
        """
        # Match condition to drug categories
        matched_categories = self._match_condition(patient_condition)
        
        if matched_categories:
            candidates = self.drug_db.get_drugs_by_categories(matched_categories)
        else:
            # Fallback strategy for unknown/general conditions
            # If nothing matched, prefer general health advice instead of all drugs
            candidates = self.drug_db.get_drugs_by_categories(['general_health'])
            matched_categories = ['general_health'] # Treat as general
        
        # Safety net: if even general health fails (shouldn't happen), fallback to all but careful
        if not candidates:
            candidates = self.drug_db.get_all_drugs()
        
        # Score candidates
        recommendations = []
        for drug in candidates:
            drug_id = drug['id']
            base_rating = self.drug_db.drug_ratings.get(drug_id, drug['base_rating'])
            
            # Sentiment impact: normalize to 0-1 range
            sentiment_factor = min(max(float(sentiment_score) / 2.0, 0.0), 1.0)
            confidence_factor = min(max(float(confidence), 0.0), 1.0)
            
            # Composite score calculation
            efficacy = base_rating / 5.0  # Normalize to 0-1
            sentiment_impact = sentiment_factor * 0.3  # Up to 0.3 boost from positive sentiment
            confidence_boost = confidence_factor * 0.2  # Up to 0.2 boost from high confidence
            
            composite = efficacy * 0.6 + sentiment_impact + confidence_boost
            
            # Category relevance bonus: if drug category matches the condition, boost score
            if matched_categories and drug['category'] in matched_categories:
                composite += 0.15  # Relevance bonus
            
            # Critical / General handling for reasons
            if drug['category'] == 'critical':
                reason = "CRITICAL CONDITION DETECTED. Immediate professional medical attention is required. Do not rely on self-medication."
                composite = 2.0 # Force to very top
            elif drug['category'] == 'general_health':
                reason = "No specific condition detected. General health maintenance is recommended. Consult a doctor for specific symptoms."
            else:
                # Generate reason for "Why this drug?"
                category_labels = {
                    'antimalarial': 'an antimalarial drug',
                    'antibiotic': 'an antibiotic',
                    'antiviral': 'an antiviral medication',
                    'fever': 'a fever reducer',
                    'pain_relief': 'a pain reliever',
                    'diabetes': 'a diabetes medication',
                    'hypertension': 'a blood pressure medication',
                    'cholesterol': 'a cholesterol-lowering medication',
                    'acid_reflux': 'a gastric acid reducer',
                    'allergy': 'an antihistamine',
                    'cough': 'a cough suppressant',
                    'expectorant': 'an expectorant',
                    'bronchodilator': 'a bronchodilator',
                    'autoimmune': 'an autoimmune therapy',
                    'thyroid': 'a thyroid medication',
                    'antidepressant': 'an antidepressant',
                    'antifungal': 'an antifungal medication',
                    'skin': 'a dermatological treatment',
                    'antidiarrheal': 'an antidiarrheal agent',
                    'anticonvulsant': 'an anticonvulsant',
                    'muscle_relaxant': 'a muscle relaxant',
                    'antiemetic': 'an antiemetic (anti-nausea)',
                    'anticoagulant': 'an anticoagulant (blood thinner)',
                    'sedative': 'a sedative / anxiolytic',
                    'corticosteroid': 'a corticosteroid',
                    'antacid': 'an antacid',
                    'laxative': 'a laxative',
                    'iron_supplement': 'an iron supplement',
                    'supplement': 'a nutritional supplement',
                    'rehydration': 'a rehydration solution',
                }
                cat_label = category_labels.get(drug['category'], f"a {drug['category']} medication")
                
                if matched_categories and drug['category'] in matched_categories:
                    reason = (
                        f"{drug['name']} is {cat_label} directly relevant to the detected condition "
                        f"'{patient_condition}'. It has a base rating of {base_rating}/5.0 "
                        f"(efficacy: {efficacy*100:.0f}%). "
                        f"Sentiment analysis contributed +{sentiment_impact:.3f} to the composite score, "
                        f"and model confidence added +{confidence_boost:.3f}. "
                        f"Composite score: {composite:.4f}."
                    )
                else:
                    reason = (
                        f"{drug['name']} ({cat_label}) is recommended as a supportive treatment. "
                        f"Base rating: {base_rating}/5.0, efficacy: {efficacy*100:.0f}%. "
                        f"Composite score: {composite:.4f}."
                    )
            
            recommendations.append({
                'drug_id': drug_id,
                'drug_name': drug['name'],
                'category': drug['category'],
                'score': round(float(base_rating), 2),
                'base_rating': round(float(base_rating), 2),
                'confidence': round(float(confidence_factor), 4),
                'composite_score': round(float(composite), 4),
                'efficacy_score': round(float(efficacy), 4),
                'sentiment_score': round(float(sentiment_impact), 4),
                'side_effects': self.drug_db.drug_side_effects.get(drug_id, []),
                'reason': reason,
            })
        
        # Sort by composite score
        recommendations.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return recommendations[:top_k]
    
    def _match_condition(self, patient_condition):
        """Match a patient condition string to relevant drug categories."""
        if not patient_condition:
            return []
        
        condition_lower = patient_condition.lower()
        matched = set()
        
        for keyword, categories in self.drug_db.condition_to_drugs.items():
            if keyword in condition_lower:
                matched.update(categories)
        
        return list(matched) if matched else []
    
    def _get_safe_recommendations(self, top_k=TOP_K_RECOMMENDATIONS):
        """Get safe recommendations when confidence is very low"""
        all_drugs = self.drug_db.get_all_drugs()
        recommendations = []
        
        for drug in all_drugs:
            drug_id = drug['id']
            base_rating = drug['base_rating']
            efficacy = base_rating / 5.0
            recommendations.append({
                'drug_id': drug_id,
                'drug_name': drug['name'],
                'category': drug['category'],
                'score': round(float(base_rating), 2),
                'base_rating': round(float(base_rating), 2),
                'confidence': 0.0,
                'composite_score': round(float(efficacy * 0.6), 4),
                'efficacy_score': round(float(efficacy), 4),
                'sentiment_score': 0.0,
                'side_effects': self.drug_db.drug_side_effects.get(drug_id, []),
                'warning': 'Low confidence — consult healthcare provider'
            })
        
        recommendations.sort(key=lambda x: x['composite_score'], reverse=True)
        return recommendations[:top_k]
    
    def update_from_feedback(self, drug_id, patient_feedback_rating):
        """Update drug rating based on patient feedback"""
        normalized_rating = patient_feedback_rating / 5.0 * 5.0
        self.drug_db.update_rating(drug_id, normalized_rating)
    
    def get_recommendation_report(self, recommendations, patient_info):
        """Generate a detailed recommendation report"""
        return {
            'patient_condition': patient_info.get('condition', 'Unknown'),
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_recommendations': len(recommendations),
            'top_recommendation': recommendations[0] if recommendations else None,
            'all_recommendations': recommendations,
            'consultation_note': 'Patient should consult healthcare provider before medication'
        }
