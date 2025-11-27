# 📚 INDEX - Système de Reporting Lettres de Liaison

## Bienvenue dans votre nouveau système de reporting automatique !

---

## 🎯 Par où commencer ?

### 👥 Vous êtes un **Utilisateur Final** (Gaëlle, Direction Qualité)
➡️ Lisez : **QUICKSTART.md**  
⏱️ Temps : 5 minutes  
🎯 Objectif : Comprendre comment utiliser le système

### 🔧 Vous êtes un **Administrateur IT**
➡️ Lisez : **INSTALLATION.md**  
⏱️ Temps : 30-45 minutes  
🎯 Objectif : Installer et configurer le système

### 📊 Vous voulez comprendre le **Projet Complet**
➡️ Lisez : **PROJET_RECAP.md**  
⏱️ Temps : 15 minutes  
🎯 Objectif : Vue d'ensemble technique et fonctionnelle

### 📖 Vous cherchez la **Documentation Complète**
➡️ Lisez : **README.md**  
⏱️ Temps : 20 minutes  
🎯 Objectif : Référence complète de toutes les fonctionnalités

---

## 📁 Fichiers du Projet

### 🐍 Fichiers Python (Code Source)

| Fichier | Description | À Modifier ? |
|---------|-------------|--------------|
| `main.py` | Application principale avec interface web | ⚠️ Rarement |
| `config.py` | Gestion de la configuration | ⚠️ Rarement |
| `database.py` | Connexions aux bases de données GAM et ESL | ⚠️ Rarement |
| `data_processing.py` | Traitement et analyse des données | ⚠️ Rarement |
| `pptx_generator.py` | Génération des PowerPoint | ✅ Personnalisation |
| `email_sender.py` | Envoi des emails | ✅ Personnalisation |
| `monthly_report.py` | Script pour rapports mensuels | ❌ Non |
| `setup_scheduler.py` | Configuration tâche planifiée | ❌ Non |
| `test_installation.py` | Tests d'installation | ❌ Non |

### 📄 Fichiers de Configuration

| Fichier | Description | À Créer/Modifier ? |
|---------|-------------|-------------------|
| `.env` | **À CRÉER** - Configuration sensible (BDD, Email) | ✅ OUI - Obligatoire |
| `requirements.txt` | Liste des dépendances Python | ❌ Non |
| `.gitignore` | Fichiers à ignorer dans git | ❌ Non |

### 📊 Fichiers de Données

| Fichier | Description | À Créer/Modifier ? |
|---------|-------------|-------------------|
| `iqss_ll_ufum3_exemple.csv` | Exemple de mapping UF/Spécialités | ⚠️ Remplacer par le vrai |

### 📚 Documentation

| Fichier | Description | Pour Qui ? |
|---------|-------------|-----------|
| `INDEX.md` | Ce fichier - Point d'entrée | 👤 Tous |
| `QUICKSTART.md` | Démarrage rapide | 👥 Utilisateurs |
| `INSTALLATION.md` | Guide d'installation | 🔧 Admins IT |
| `PROJET_RECAP.md` | Récapitulatif du projet | 📊 Managers |
| `README.md` | Documentation complète | 📖 Tous |

---

## 🚀 Installation en 3 Étapes

### 1️⃣ Installer Python et les dépendances
```bash
pip install -r requirements.txt
```

### 2️⃣ Créer le fichier .env avec vos paramètres
```env
GAM_URL=jdbc:oracle:thin:@//votre-serveur:1521/service
ESL_URL=jdbc:sqlserver://votre-serveur:1433;databaseName=EASILY
SMTP_USER=votre-email@hopital-foch.com
# ... (voir INSTALLATION.md pour la liste complète)
```

### 3️⃣ Lancer l'application
```bash
python main.py
```

➡️ Ouvrir : http://localhost:8000

---

## 🎓 Formation Utilisateur - 10 Minutes

### Objectif
Savoir générer un rapport et l'envoyer par email

### Étapes

1. **Ouvrir l'interface**
   - Navigateur : http://localhost:8000

2. **Choisir le type de rapport**
   - Option A : Par période (dates)
   - Option B : Par séjours (liste de numéros)

3. **Remplir le formulaire**
   - Dates ou numéros de séjour
   - Cocher "Envoyer par email" si souhaité

4. **Cliquer sur "Générer le rapport"**
   - Attendre quelques secondes
   - Message de succès s'affiche

5. **Télécharger les fichiers**
   - PowerPoint : Rapport formaté
   - Excel : Données brutes

### Fonctionnalités Avancées

- **Test Email** : Vérifier la configuration email
- **API REST** : Intégration avec d'autres systèmes
- **Rapports Mensuels** : Automatiques le 1er du mois

---

## 📧 Rapport Mensuel Automatique

### Comment ça marche ?

1. **Quand ?** Le 1er de chaque mois à 8h00

2. **Quoi ?**
   - Analyse automatique du mois précédent
   - Génération PowerPoint + Excel
   - Envoi par email à Gaëlle et destinataires

3. **Où ?**
   - Fichiers dans : `outputs/monthly/`
   - Email reçu à : s.ben-yahia@hopital-foch.com

### Configuration

Une seule fois, exécuter :
```bash
python setup_scheduler.py
```

Puis suivre les instructions affichées.

---

## 🎨 Personnalisation

### Modifier les couleurs du PowerPoint

Éditer `pptx_generator.py` :
```python
# Ligne 11-16 : Couleurs
FOCH_BLUE = RGBColor(0, 82, 147)     # Bleu principal
FOCH_GREEN = RGBColor(106, 168, 79)  # Vert
# ... etc
```

### Modifier les seuils de couleur

Éditer `pptx_generator.py` :
```python
# Ligne 68-76 : Fonction get_color_by_value
thresholds.get('excellent', 95)  # Vert si >= 95%
thresholds.get('good', 85)       # Jaune si >= 85%
# ... etc
```

### Modifier les destinataires email

Éditer `.env` :
```env
EMAIL_TO=nouveau-destinataire@hopital-foch.com
EMAIL_CC=copie1@hopital-foch.com,copie2@hopital-foch.com
```

### Modifier le contenu de l'email

Éditer `email_sender.py` :
- Fonction `generate_monthly_report_email()` (ligne 61)

---

## 🔍 Dépannage Rapide

### ❌ Erreur : "Module not found"
**Solution** : `pip install -r requirements.txt`

### ❌ Erreur : "Cannot connect to database"
**Solution** : Vérifier les paramètres dans `.env`

### ❌ Erreur : "Email not sent"
**Solution** : Tester avec le bouton "Test Email"

### ❌ PowerPoint vide
**Solution** : Vérifier que `iqss_ll_ufum3.csv` existe dans `db/`

### ❌ Tâche planifiée ne s'exécute pas
**Solution** : Tester manuellement `python monthly_report.py`

➡️ **Guide complet** : Voir INSTALLATION.md section "Dépannage"

---

## 📞 Contacts & Support

### 👥 Utilisateurs Finaux
**Gaëlle Burdy** - Direction qualité  
📞 DECT 2105  
📧 gaelle.burdy@hopital-foch.com

### 🔧 Support Technique
**Service IT**  
📧 s.ben-yahia@hopital-foch.com

### 📚 Documentation
- Interface web : http://localhost:8000
- API Documentation : http://localhost:8000/docs
- README : README.md

---

## 🗺️ Architecture Simplifiée

```
┌─────────────────┐
│  Interface Web  │  ← Vous êtes ici
│  localhost:8000 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI App   │  ← main.py
│   (Backend)     │
└────────┬────────┘
         │
         ├─► 🗄️ BDD GAM (Oracle)    ← Séjours
         ├─► 🗄️ BDD ESL (SQL Server) ← Documents
         │
         ▼
┌─────────────────┐
│   Traitement    │  ← data_processing.py
│   Données       │
└────────┬────────┘
         │
         ├─► 📊 PowerPoint  ← pptx_generator.py
         ├─► 📈 Excel       ← pandas
         │
         ▼
┌─────────────────┐
│  Envoi Email    │  ← email_sender.py
│  (SMTP)         │
└─────────────────┘
```

---

## ✅ Checklist de Démarrage

### Installation
- [ ] Python 3.9+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichier `.env` créé et configuré
- [ ] Fichier `iqss_ll_ufum3.csv` dans `db/`
- [ ] Test d'installation passé (`python test_installation.py`)

### Configuration
- [ ] Connexion GAM testée
- [ ] Connexion ESL testée
- [ ] Email de test envoyé et reçu
- [ ] Premier rapport généré avec succès
- [ ] Tâche planifiée configurée

### Formation
- [ ] Utilisateurs formés (QUICKSTART.md)
- [ ] Administrateur formé (INSTALLATION.md)
- [ ] Documentation accessible
- [ ] Contacts de support communiqués

---

## 🎯 Objectifs du Système

### 🎯 Objectif Principal
Automatiser la génération et l'envoi mensuel des rapports sur les indicateurs de délai de validation et de diffusion des lettres de liaison.

### 📊 Indicateurs Suivis
- Taux de validation des LL
- Taux de validation à J0 (jour de sortie)
- Délai moyen de validation
- Taux de diffusion
- Délai moyen de diffusion

### 👥 Bénéficiaires
- **Direction Qualité** : Gain de temps, rapports automatisés
- **Services de soins** : Suivi de leur performance
- **Direction** : Indicateurs mensuels fiables

---

## 📈 Évolutions Futures

### Court terme (1-3 mois)
- Ajout de graphiques dans le PowerPoint
- Export PDF des rapports
- Gestion du calendrier des jours fériés

### Moyen terme (3-6 mois)
- Tableau de bord web interactif
- Alertes automatiques si seuils non atteints
- Comparaison avec périodes précédentes

### Long terme (6-12 mois)
- Prédictions avec Machine Learning
- Intégration avec d'autres systèmes hospitaliers
- Application mobile de consultation

➡️ Suggestions bienvenues à : s.ben-yahia@hopital-foch.com

---

## 🎉 Félicitations !

Vous avez maintenant accès à un système complet et automatisé pour le suivi des indicateurs de lettres de liaison.

**Prochaine étape** : Choisissez le document adapté à votre profil ci-dessus ⬆️

---

**Document INDEX créé le** : 27 novembre 2025  
**Version** : 1.0.0  
**Système** : Reporting Automatique Lettres de Liaison  
**Hôpital** : Foch

---

## 📁 Structure Complète du Projet

```
ReportingLL/
│
├── 📚 DOCUMENTATION
│   ├── INDEX.md (← vous êtes ici)
│   ├── QUICKSTART.md
│   ├── INSTALLATION.md
│   ├── PROJET_RECAP.md
│   └── README.md
│
├── 🐍 CODE SOURCE
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── data_processing.py
│   ├── pptx_generator.py
│   ├── email_sender.py
│   ├── monthly_report.py
│   ├── setup_scheduler.py
│   └── test_installation.py
│
├── ⚙️ CONFIGURATION
│   ├── .env (À CRÉER)
│   ├── requirements.txt
│   └── .gitignore
│
├── 📊 DONNÉES
│   └── db/
│       └── iqss_ll_ufum3.csv
│
├── 📁 SORTIES
│   ├── outputs/
│   │   └── monthly/
│   └── logs/
│
└── 🌐 INTERFACE WEB
    └── (générée automatiquement)
```

**Bonne utilisation ! 🚀**