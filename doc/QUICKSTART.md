# 🚀 Guide de Démarrage Rapide

## Installation en 5 minutes

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Configuration minimale

Créez un fichier `.env` :

```env
# Bases de données (À CONFIGURER)
GAM_URL=jdbc:oracle:thin:@//votre-serveur:1521/service
GAM_USER=votre_user
GAM_PASSWORD=votre_password

ESL_URL=jdbc:sqlserver://votre-serveur:1433;databaseName=EASILY
ESL_USER=votre_user
ESL_PASSWORD=votre_password

# Email (À CONFIGURER)
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=votre-email@hopital-foch.com
SMTP_PASSWORD=votre_password
EMAIL_FROM=reporting@hopital-foch.com
EMAIL_TO=s.ben-yahia@hopital-foch.com
EMAIL_CC=gaelle.burdy@hopital-foch.com
```

### 3. Fichier de mapping

Placez `iqss_ll_ufum3.csv` dans le dossier `db/`

### 4. Test de l'installation

```bash
python test_installation.py
```

### 5. Lancement

```bash
python main.py
```

Accédez à : **http://localhost:8000**

---

## 🎯 Utilisation Rapide

### Via l'Interface Web

1. Ouvrir http://localhost:8000
2. Choisir entre :
   - **Rapport par période** : Sélectionner dates début/fin
   - **Rapport par séjours** : Entrer les numéros de séjour
3. Cocher "Envoyer par email" si souhaité
4. Cliquer sur "Générer le rapport"
5. Télécharger le PowerPoint et l'Excel

### Via l'API

```bash
# Générer un rapport pour janvier-juillet 2025
curl -X POST "http://localhost:8000/api/report/by-date" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-07-31",
    "send_email": true
  }'
```

---

## 📅 Rapport Mensuel Automatique

### Configuration

```bash
python setup_scheduler.py
```

**Suivre les instructions pour :**
- Linux/Mac : Configuration cron
- Windows : Planificateur de tâches

### Test manuel

```bash
python monthly_report.py
```

Le rapport sera généré pour le mois précédent et envoyé automatiquement.

---

## 🔍 Vérifications

### Test email

```bash
curl -X POST "http://localhost:8000/api/test-email"
```

Ou via l'interface web : bouton "Envoyer un email de test"

### Santé de l'API

```bash
curl http://localhost:8000/api/health
```

---

## 📂 Fichiers Générés

- **PowerPoint** : `outputs/LL_Rapport_*.pptx`
- **Excel** : `outputs/LL_Donnees_*.xlsx`
- **Logs** : `logs/monthly_report.log`

---

## ⚠️ Problèmes Courants

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Cannot connect to database"
- Vérifier les paramètres dans `.env`
- Vérifier la connectivité réseau
- Vérifier les drivers JDBC

### "Email not sent"
- Vérifier les paramètres SMTP dans `.env`
- Vérifier que le compte email autorise SMTP
- Vérifier le pare-feu

---

## 📞 Support

**Direction qualité** : Gaëlle Burdy (DECT 2105)  
**Support technique** : s.ben-yahia@hopital-foch.com

---

## 🎓 Ressources

- **README complet** : `README.md`
- **Documentation API** : http://localhost:8000/docs (après lancement)
- **Code source** : Tous les fichiers `.py` sont commentés

---

**Dernière mise à jour** : Novembre 2025  
**Version** : 1.0.0