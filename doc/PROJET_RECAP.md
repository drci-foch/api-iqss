# 📊 Système de Reporting Automatique - Lettres de Liaison
## Hôpital Foch

---

## 🎯 Objectif du Projet

Automatiser la génération et l'envoi des rapports mensuels sur les indicateurs de délai de validation et de diffusion des lettres de liaison (LL) pour les séjours de plus de 24 heures.

**Remplace** : Le processus manuel de génération de PowerPoint par Gaëlle Burdy

**Conserve** : La requête de Bernard sur Easily (exportée en Excel pour vérification)

---

## ✨ Fonctionnalités Principales

### 1. Génération de Rapports

#### Par Période
- Sélectionner une date de début et de fin
- Génère automatiquement :
  - 📊 PowerPoint avec tableaux et statistiques
  - 📈 Excel avec données brutes (requête Bernard)

#### Par Liste de Séjours
- Entrer une liste de numéros de séjour
- Analyse spécifique sur ces séjours
- Mêmes exports (PowerPoint + Excel)

### 2. Interface Web Intuitive
- Accès via navigateur : http://localhost:8000
- Formulaires simples pour générer les rapports
- Téléchargement direct des fichiers
- Option d'envoi automatique par email

### 3. Envoi Automatique Mensuel
- **Fréquence** : 1er de chaque mois à 8h00
- **Destinataires** :
  - Principal : s.ben-yahia@hopital-foch.com
  - Copie : gaelle.burdy@hopital-foch.com
- **Contenu** :
  - Email HTML avec résumé des indicateurs
  - PowerPoint en pièce jointe
  - Excel (requête Bernard) en pièce jointe

---

## 🔄 Workflow

```
┌─────────────────┐
│  1er du mois    │
│     8h00        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Script Automatique     │
│  monthly_report.py      │
└────────┬────────────────┘
         │
         ├─► Connexion GAM (Oracle)
         ├─► Connexion ESL (SQL Server)
         │
         ▼
┌─────────────────────────┐
│  Extraction Données     │
│  - Séjours (GAM)        │
│  - Documents (ESL)      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Traitement             │
│  - Fusion données       │
│  - Calcul délais        │
│  - Statistiques         │
└────────┬────────────────┘
         │
         ├─► Génération PowerPoint
         ├─► Export Excel
         │
         ▼
┌─────────────────────────┐
│  Envoi Email            │
│  - Gaëlle Burdy         │
│  - Destinataire(s)      │
│  - Pièces jointes       │
└─────────────────────────┘
```

---

## 📋 Contenu du PowerPoint

### Diapositive 1 : Titre
- Titre principal
- Période du rapport
- Logo Hôpital Foch

### Diapositive 2 : Tableau Récapitulatif
Colonnes du tableau :
- Spécialité
- Nombre total de séjours
- LL Validées (nombre et %)
- Taux validation à J0
- Délai moyen validation
- Colonnes historiques (2022, Dec 2023, etc.)
- LL Diffusées (nombre et %)
- Délai diffusion/validation

**Code couleur automatique** :
- 🟢 Vert : Excellent (≥95%)
- 🟡 Jaune : Bon (≥85%)
- 🟠 Orange : Moyen (≥70%)
- 🔴 Rouge : Faible (<70%)

### Diapositive 3 : Instructions
- Processus de validation des LL
- Instructions pour les versions multiples
- Contact : Gaëlle Burdy

---

## 📊 Contenu de l'Excel

Données brutes issues de la requête de Bernard :
- IPP patient
- Numéro de séjour
- Dates d'entrée et sortie
- UF de sortie
- Spécialité
- ID document
- Dates de création et validation
- Délais calculés
- Classification (0j, 1j+, sansLL)

---

## 🛠️ Architecture Technique

### Backend
- **Framework** : FastAPI (Python)
- **Bases de données** :
  - Oracle (GAM) via JDBC
  - SQL Server (ESL) via JDBC
- **Génération PowerPoint** : python-pptx
- **Traitement données** : pandas

### Frontend
- **Interface Web** : HTML/CSS/JavaScript
- **Design** : Moderne et responsive
- **API REST** : Documentation automatique

### Email
- **Protocole** : SMTP (TLS)
- **Serveur** : Office365
- **Format** : HTML avec pièces jointes

---

## 📁 Structure des Fichiers

```
projet/
├── main.py                    # Application FastAPI
├── config.py                  # Configuration
├── database.py                # Connexions BDD
├── data_processing.py         # Traitement données
├── pptx_generator.py          # Génération PowerPoint
├── email_sender.py            # Envoi emails
├── monthly_report.py          # Script mensuel
├── setup_scheduler.py         # Configuration tâche planifiée
├── test_installation.py       # Tests
├── requirements.txt           # Dépendances Python
├── .env                       # Configuration (à créer)
├── README.md                  # Documentation complète
├── QUICKSTART.md              # Guide démarrage rapide
├── .gitignore                 # Fichiers à ignorer
├── outputs/                   # Fichiers générés
│   ├── monthly/               # Rapports mensuels
│   └── [autres rapports]
├── logs/                      # Logs d'exécution
└── db/                        # Fichiers de données
    └── iqss_ll_ufum3.csv      # Mapping UF/Spécialités
```

---

## 🔐 Sécurité

- **Credentials** : Stockés dans fichier .env (non versionné)
- **Connexions BDD** : Chiffrées (JDBC)
- **Emails** : SMTP avec TLS
- **Fichiers sensibles** : Exclus du contrôle de version

---

## 🚀 Déploiement

### Option 1 : Serveur dédié
- Installation sur serveur Windows/Linux
- Configuration tâche planifiée
- Exécution automatique

### Option 2 : Poste de travail
- Installation locale
- Lancement manuel ou planifié
- Peut rester en arrière-plan

### Prérequis
- Python 3.9+
- Accès réseau aux BDD GAM et ESL
- Accès SMTP pour envoi emails
- 500 MB espace disque

---

## 📈 Indicateurs Suivis

### Validation
- Nombre total de séjours
- Nombre de LL validées
- Taux de validation (%)
- Taux de validation à J0 (%)
- Délai moyen de validation (jours)

### Diffusion
- Nombre de LL diffusées
- % de LL diffusées / validées
- Taux de diffusion à J0 (%)
- Délai moyen diffusion/validation (jours)

### Par Spécialité
Tous les indicateurs ci-dessus déclinés par service :
- VASCULAIRE
- NEUROCHIRURGIE
- CARDIOLOGIE
- OBSTÉTRIQUE
- GÉRIATRIE
- [etc.]

---

## 🎓 Documentation

### Utilisateurs
- **QUICKSTART.md** : Démarrage en 5 minutes
- **README.md** : Documentation complète
- **Interface web** : Documentation interactive

### Développeurs
- **Code commenté** : Tous les fichiers Python
- **API Docs** : http://localhost:8000/docs
- **Architecture** : Voir ce document

---

## 📞 Contacts

### Utilisateurs Finaux
- **Gaëlle Burdy** (Direction qualité)
- DECT 2105
- Email : gaelle.burdy@hopital-foch.com

### Support Technique
- **Email** : s.ben-yahia@hopital-foch.com

---

## 🔮 Évolutions Futures Possibles

### Court terme
- [ ] Graphiques dans PowerPoint
- [ ] Export PDF
- [ ] Gestion jours fériés

### Moyen terme
- [ ] Tableau de bord web interactif
- [ ] Alertes par email si seuils non atteints
- [ ] Comparaison avec périodes précédentes

### Long terme
- [ ] Prédictions avec Machine Learning
- [ ] Intégration avec autres systèmes
- [ ] Application mobile

---

## ✅ Avantages de la Solution

### Pour Gaëlle (Direction Qualité)
- ⏱️ **Gain de temps** : Plus de génération manuelle
- 📧 **Automatisation** : Email envoyé automatiquement
- 🎯 **Fiabilité** : Calculs standardisés et vérifiables
- 📊 **Qualité** : PowerPoint professionnel et cohérent

### Pour Bernard (Requêtes)
- 💾 **Conservation** : Sa requête reste disponible en Excel
- 🔍 **Traçabilité** : Données brutes exportées pour vérification
- 🔄 **Compatibilité** : Peut toujours faire ses propres analyses

### Pour l'Hôpital
- 📈 **Suivi régulier** : Indicateurs suivis mensuellement
- 📋 **Conformité** : Respect du Décret n° 2016995
- 💰 **Économies** : Réduction du temps administratif
- 🎓 **Capitalisation** : Historique des performances

---

## 📊 Méthodologie (Conforme au Document de Référence)

### Séjours Inclus
- Séjours ≥ 24h (1 nuit et plus)
- UF de sortie non exclues
- Patient non décédé le jour de la sortie

### Séjours Exclus
- Décédés
- Chirurgie ambulatoire et HDJ
- Anesthésie, ophtalmologie, radiologie, ORL
- UF spécifiques (TEST99, 392A, etc.)

### Calcul Délais
- **Délai validation** = Date validation - Date sortie
- Version la plus proche de la sortie
- Validations J-3 à J+∞ considérées

### Indicateurs Diffusion
- Exclusion weekends et jours fériés
- Exclusion versions multiples avec dernière >J+1

---

**Document créé le** : 27 novembre 2025  
**Version** : 1.0.0  
**Auteur** : Système automatisé - Hôpital Foch  
**Mise à jour** : Mensuelle avec les rapports