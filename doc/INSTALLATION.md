# 📦 Guide d'Installation Pas à Pas

## Système de Reporting Lettres de Liaison - Hôpital Foch

---

## 🎯 Vue d'ensemble

Ce guide vous accompagne dans l'installation complète du système, depuis la configuration initiale jusqu'au premier rapport généré.

**Durée estimée** : 30-45 minutes

---

## ✅ Prérequis

Avant de commencer, assurez-vous d'avoir :

### Logiciels
- [ ] **Python 3.9 ou supérieur**
  - Télécharger : https://www.python.org/downloads/
  - Vérifier : `python --version`

- [ ] **pip** (gestionnaire de paquets Python)
  - Normalement inclus avec Python
  - Vérifier : `pip --version`

- [ ] **Drivers JDBC**
  - Oracle JDBC Driver (ojdbc8.jar ou supérieur)
  - Microsoft SQL Server JDBC Driver (mssql-jdbc.jar)

### Accès
- [ ] Accès réseau aux bases de données GAM et ESL
- [ ] Compte email avec accès SMTP
- [ ] Droits d'écriture sur le répertoire d'installation

### Fichiers
- [ ] Tous les fichiers Python du projet
- [ ] Fichier `iqss_ll_ufum3.csv` (mapping UF/Spécialités)

---

## 📥 Étape 1 : Installation de Python

### Windows

1. Télécharger l'installeur Python depuis python.org
2. Lancer l'installeur
3. ⚠️ **IMPORTANT** : Cocher "Add Python to PATH"
4. Cliquer sur "Install Now"
5. Vérifier l'installation :
   ```cmd
   python --version
   pip --version
   ```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip
python3 --version
pip3 --version
```

### macOS

```bash
# Avec Homebrew
brew install python3
python3 --version
pip3 --version
```

---

## 📂 Étape 2 : Préparation des Fichiers

### 2.1 Créer la structure de dossiers

```
ReportingLL/
├── config.py
├── database.py
├── data_processing.py
├── email_sender.py
├── main.py
├── monthly_report.py
├── pptx_generator.py
├── setup_scheduler.py
├── test_installation.py
├── requirements.txt
├── .env (à créer)
├── .gitignore
├── README.md
├── QUICKSTART.md
├── db/
│   └── iqss_ll_ufum3.csv
├── outputs/
├── logs/
└── static/
```

### 2.2 Copier tous les fichiers Python

Placez tous les fichiers `.py` à la racine du dossier `ReportingLL/`

### 2.3 Créer le fichier de mapping

Placez `iqss_ll_ufum3.csv` dans le dossier `db/`

**Format du CSV** :
```csv
sej_uf,doc_key,sej_spe
343,vasculaire,VASCULAIRE
296,neurochirurgie,NEUROCHIRURGIE
373,cardiologie,CARDIOLOGIE
...
```

---

## 🔧 Étape 3 : Installation des Dépendances

### 3.1 Ouvrir un terminal

- **Windows** : Rechercher "cmd" ou "PowerShell"
- **Linux/Mac** : Terminal

### 3.2 Naviguer vers le dossier du projet

```bash
cd chemin/vers/ReportingLL
```

### 3.3 Installer les dépendances

```bash
pip install -r requirements.txt
```

**Note** : Cette étape peut prendre 5-10 minutes selon votre connexion.

### 3.4 Vérifier l'installation

```bash
python test_installation.py
```

Tous les tests doivent être ✅ PASSÉ

---

## ⚙️ Étape 4 : Configuration

### 4.1 Créer le fichier .env

Dans le dossier `ReportingLL/`, créer un fichier nommé `.env` :

**Windows** :
```cmd
type nul > .env
```

**Linux/Mac** :
```bash
touch .env
```

### 4.2 Éditer le fichier .env

Ouvrir `.env` avec un éditeur de texte et ajouter :

```env
# ==============================================
# CONFIGURATION BASE DE DONNÉES GAM (ORACLE)
# ==============================================
GAM_DRIVER=oracle.jdbc.OracleDriver
GAM_URL=jdbc:oracle:thin:@//[SERVEUR]:[PORT]/[SERVICE]
GAM_USER=[VOTRE_UTILISATEUR]
GAM_PASSWORD=[VOTRE_MOT_DE_PASSE]

# Exemple :
# GAM_URL=jdbc:oracle:thin:@//192.168.1.100:1521/GAMDB
# GAM_USER=gam_user
# GAM_PASSWORD=SecurePass123

# ==============================================
# CONFIGURATION BASE DE DONNÉES ESL (SQL SERVER)
# ==============================================
ESL_DRIVER=com.microsoft.sqlserver.jdbc.SQLServerDriver
ESL_URL=jdbc:sqlserver://[SERVEUR]:[PORT];databaseName=EASILY
ESL_USER=[VOTRE_UTILISATEUR]
ESL_PASSWORD=[VOTRE_MOT_DE_PASSE]

# Exemple :
# ESL_URL=jdbc:sqlserver://192.168.1.101:1433;databaseName=EASILY
# ESL_USER=esl_user
# ESL_PASSWORD=SecurePass456

# ==============================================
# CONFIGURATION EMAIL (SMTP)
# ==============================================
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=[VOTRE_EMAIL@hopital-foch.com]
SMTP_PASSWORD=[VOTRE_MOT_DE_PASSE_EMAIL]
EMAIL_FROM=reporting@hopital-foch.com
EMAIL_TO=s.ben-yahia@hopital-foch.com
EMAIL_CC=gaelle.burdy@hopital-foch.com

# Exemple :
# SMTP_USER=reporting@hopital-foch.com
# SMTP_PASSWORD=EmailPass789

# ==============================================
# CONFIGURATION GÉNÉRALE
# ==============================================
APP_TITLE=Indicateurs Lettres de Liaison
APP_VERSION=1.0.0
```

### 4.3 Remplacer les valeurs

⚠️ **IMPORTANT** : Remplacer tous les `[...]` par vos vraies valeurs

**Pour obtenir les paramètres** :
- **GAM** : Contacter l'administrateur base de données Oracle
- **ESL** : Contacter l'administrateur base de données SQL Server
- **SMTP** : Contacter le service IT pour les paramètres email

### 4.4 Sécuriser le fichier .env

Le fichier `.env` contient des mots de passe. Assurez-vous que :
- Il n'est pas partagé
- Il n'est pas dans le contrôle de version (git)
- Les permissions sont restreintes

**Linux/Mac** :
```bash
chmod 600 .env
```

---

## 🧪 Étape 5 : Tests

### 5.1 Test de l'installation

```bash
python test_installation.py
```

**Attendu** : Tous les tests ✅ PASSÉ

### 5.2 Test de connexion aux bases de données

```python
# Créer un fichier test_db.py
from database import DatabaseConnector

db = DatabaseConnector()

# Test GAM
try:
    conn = db.connect_gam()
    print("✅ Connexion GAM réussie")
    db.disconnect_all()
except Exception as e:
    print(f"❌ Erreur GAM: {e}")

# Test ESL
try:
    conn = db.connect_esl()
    print("✅ Connexion ESL réussie")
    db.disconnect_all()
except Exception as e:
    print(f"❌ Erreur ESL: {e}")
```

```bash
python test_db.py
```

### 5.3 Test d'envoi d'email

Lancer l'application :
```bash
python main.py
```

Ouvrir le navigateur : http://localhost:8000

Cliquer sur "Envoyer un email de test"

**Vérifier** : Email reçu à l'adresse configurée

---

## 🚀 Étape 6 : Premier Rapport

### 6.1 Lancer l'application

```bash
python main.py
```

**Attendu** :
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6.2 Accéder à l'interface

Ouvrir : http://localhost:8000

### 6.3 Générer un rapport de test

Dans la section "Rapport par Période" :
1. Date début : `2025-01-01`
2. Date fin : `2025-07-31`
3. ❌ Ne pas cocher "Envoyer par email" (pour test)
4. Cliquer sur "Générer le rapport"

**Attendu** :
- ✅ Message de succès
- Statistiques affichées
- Liens de téléchargement PowerPoint et Excel

### 6.4 Vérifier les fichiers

Les fichiers sont dans : `outputs/`
- `LL_Rapport_*.pptx`
- `LL_Donnees_*.xlsx`

### 6.5 Ouvrir le PowerPoint

Vérifier :
- Diapositive 1 : Titre et période
- Diapositive 2 : Tableau avec données
- Diapositive 3 : Instructions

### 6.6 Ouvrir l'Excel

Vérifier :
- Colonnes : pat_ipp, sej_id, dates, délais, etc.
- Données cohérentes

---

## 📅 Étape 7 : Configuration du Rapport Mensuel

### 7.1 Test manuel

```bash
python monthly_report.py
```

**Attendu** :
- Génération du rapport pour le mois dernier
- Email envoyé automatiquement

### 7.2 Configuration de la tâche planifiée

```bash
python setup_scheduler.py
```

**Suivre les instructions affichées** selon votre système d'exploitation.

#### Sur Windows

1. Ouvrir "Planificateur de tâches"
2. Créer une nouvelle tâche
3. **Déclencheur** : Le 1er de chaque mois à 8h00
4. **Action** : Démarrer le programme
   - Programme : `python.exe`
   - Arguments : `chemin\vers\monthly_report.py`
   - Répertoire : `chemin\vers\ReportingLL`

#### Sur Linux

1. Ouvrir crontab :
   ```bash
   crontab -e
   ```

2. Ajouter :
   ```
   0 8 1 * * /usr/bin/python3 /chemin/vers/ReportingLL/monthly_report.py >> /chemin/vers/ReportingLL/logs/monthly_report.log 2>&1
   ```

3. Sauvegarder et quitter

### 7.3 Vérification

La tâche s'exécutera automatiquement le 1er du mois prochain.

Pour vérifier avant :
```bash
python monthly_report.py
```

---

## ✅ Étape 8 : Validation Finale

### Checklist de validation

- [ ] ✅ Python installé et fonctionnel
- [ ] ✅ Toutes les dépendances installées
- [ ] ✅ Fichier .env configuré correctement
- [ ] ✅ Connexion GAM opérationnelle
- [ ] ✅ Connexion ESL opérationnelle
- [ ] ✅ Test email réussi
- [ ] ✅ Premier rapport généré avec succès
- [ ] ✅ PowerPoint correct et professionnel
- [ ] ✅ Excel avec données complètes
- [ ] ✅ Tâche planifiée configurée
- [ ] ✅ Logs créés et lisibles

---

## 🎓 Étape 9 : Formation

### Pour les utilisateurs

**Documentation à lire** :
1. QUICKSTART.md (5 min)
2. README.md (15 min)

**Actions à maîtriser** :
- Générer un rapport par période
- Générer un rapport par séjours
- Télécharger les fichiers
- Envoyer par email

### Pour les administrateurs

**Documentation à lire** :
1. Tout ce qui précède
2. Code source (commenté)
3. API Documentation : http://localhost:8000/docs

**Actions à maîtriser** :
- Configuration du .env
- Dépannage connexions BDD
- Modification des seuils de couleur
- Personnalisation du PowerPoint

---

## 🔧 Dépannage

### Problème : "Module not found"

**Solution** :
```bash
pip install -r requirements.txt
```

### Problème : "Cannot connect to database"

**Vérifications** :
1. Paramètres dans .env corrects ?
2. Serveur de BDD accessible (ping) ?
3. Firewall autorise la connexion ?
4. Drivers JDBC installés ?

**Test** :
```bash
python test_db.py
```

### Problème : "Email not sent"

**Vérifications** :
1. Paramètres SMTP dans .env corrects ?
2. Compte email autorise SMTP ?
3. Pare-feu autorise le port 587 ?

**Test** :
Via l'interface web : bouton "Test Email"

### Problème : "Permission denied"

**Windows** :
Lancer le terminal en tant qu'administrateur

**Linux/Mac** :
```bash
chmod +x *.py
```

### Problème : PowerPoint vide ou incorrect

**Vérifications** :
1. Données récupérées depuis les BDD ?
2. Fichier iqss_ll_ufum3.csv présent dans db/ ?
3. Mapping UF/Spécialités correct ?

**Debug** :
Ajouter des prints dans pptx_generator.py

---

## 📞 Support

### Questions Utilisateurs
**Gaëlle Burdy**
- Direction qualité
- DECT 2105
- gaelle.burdy@hopital-foch.com

### Questions Techniques
**Support IT**
- s.ben-yahia@hopital-foch.com

### Documentation
- README.md : Documentation complète
- QUICKSTART.md : Démarrage rapide
- http://localhost:8000/docs : API interactive

---

## 🎉 Félicitations !

Votre système de reporting est maintenant opérationnel !

**Prochaines étapes** :
1. Informer Gaëlle Burdy de l'installation
2. Planifier une démo avec les utilisateurs
3. Configurer les sauvegardes des rapports
4. Documenter toute personnalisation locale

---

**Guide d'installation créé le** : 27 novembre 2025  
**Version** : 1.0.0  
**Dernière mise à jour** : 27 novembre 2025