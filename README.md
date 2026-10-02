# Djawhara GRH — Logiciel de gestion des ressources humaines

Application développée pour **Mouassasat El Jawhara** (fabrication de confiseries),
sur la base du document de spécifications fourni. Elle couvre la première version
demandée : dossier employé, pointage quotidien, contrats, préparation de la paie,
rapports, gestion des accès par rôle, et traçabilité (journal des modifications).

- **Backend** : Django (Python)
- **Frontend** : HTML/CSS + JavaScript natif (pas de framework lourd), graphiques
  avec Chart.js, interface inspirée de la maquette fournie (thème bleu clair,
  cartes arrondies, barre latérale).
- **Base de données** : SQLite par défaut (fichier local `db.sqlite3`), facilement
  remplaçable par MySQL/PostgreSQL plus tard si besoin.

## 1. Installation

Prérequis : Python 3.10+ installé sur la machine (Windows, Linux ou Mac).

```bash
# 1. Se placer dans le dossier du projet
cd djawhara_grh

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate        # Sous Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer la base de données (tables)
python manage.py makemigrations
python manage.py migrate

# 5. (Optionnel mais conseillé) Générer des données de démonstration
python manage.py seed_demo

# 6. Créer votre propre compte administrateur si vous n'utilisez pas seed_demo
python manage.py createsuperuser

# 7. Lancer le serveur local
python manage.py runserver
```

Ouvrez ensuite votre navigateur à l'adresse : **http://127.0.0.1:8000/**

> L'application tourne en local sur le poste (ou serveur interne) de l'entreprise,
> exactement comme un logiciel "desktop" : aucune connexion internet n'est requise
> une fois les dépendances installées, tant que le serveur `runserver` est lancé.
> Pour un usage multi-postes sur le réseau local de l'usine, lancez plutôt :
> `python manage.py runserver 0.0.0.0:8000` puis accédez depuis les autres postes
> via `http://<adresse-ip-du-serveur>:8000/`.

## 2. Comptes de démonstration (si vous avez lancé `seed_demo`)

Mot de passe pour tous : `djawhara2026`

| Identifiant     | Rôle                              |
|-----------------|-----------------------------------|
| admin           | Superutilisateur (accès `/admin/`)|
| directeur       | Directeur Général                 |
| rh              | Responsable Ressources Humaines   |
| chef_bonbons    | Chef d'atelier (atelier Bonbons)  |
| comptable       | Comptable / Finance               |

**⚠️ Changez ces mots de passe avant toute utilisation réelle.**

## 3. Rôles et permissions (conformément au document de spécifications)

- **Directeur Général** : accès complet en lecture à tous les modules et rapports.
- **Responsable RH** : gestion complète des employés, contrats, pointages, paie,
  documents.
- **Chef d'atelier** : pointage quotidien limité aux employés de son propre atelier,
  sans accès aux salaires ni aux contrats.
- **Comptable** : consultation des éléments de paie, primes, retenues ; pas de
  modification des pointages.
- **Superutilisateur** : accès à l'interface d'administration Django (`/admin/`)
  pour une gestion technique avancée (utilisateurs, permissions fines, etc.).

Chaque création/modification est enregistrée dans un **journal de traçabilité**
(qui, quoi, quand) consultable dans `/admin/accounts/auditlog/`.

## 4. Modules inclus (version 1)

1. **Dossier employé** — informations personnelles, professionnelles, documents
   administratifs (carte d'identité, CNAS, diplômes, etc.).
2. **Pointage quotidien** — présent / absent (justifié ou non) / retard / sortie
   anticipée / congé annuel ou maladie / repos, par atelier, avec remarques du
   chef d'atelier. Saisie interactive en JavaScript (enregistrement automatique
   sans rechargement de page).
3. **Contrats** — CDI, CDD, période d'essai, temporaire ; alerte automatique
   30 jours avant la fin d'un contrat (paramétrable dans `settings.py` via
   `CONTRACT_ALERT_DAYS`).
4. **Préparation de la paie** — jours travaillés, absences, primes, retenues,
   avances, calcul du net à payer (calcul simplifié, à faire évoluer vers un
   moteur de paie complet si nécessaire).
5. **Suivi discipline/assiduité** — liste des employés cumulant des absences ou
   retards, avec possibilité d'enregistrer une action (observation, convocation,
   avertissement, mise sous suivi).
6. **Rapports** — journaliers, hebdomadaires, mensuels, et par employé ; export
   CSV (ouvrable directement dans Excel).
7. **Sauvegarde** — SQLite est un fichier unique (`db.sqlite3`) : une sauvegarde
   quotidienne automatique peut être mise en place très simplement en copiant ce
   fichier (voir section 5 ci-dessous).

## 5. Sauvegarde des données

Le plus simple pour une PME : copier automatiquement le fichier `db.sqlite3`
(et le dossier `media/` qui contient les documents/photos) chaque jour vers un
disque externe ou un dossier réseau. Exemple de tâche planifiée (Linux/Mac, à
placer dans une tâche cron quotidienne) :

```bash
cp db.sqlite3 /chemin/vers/sauvegardes/db_$(date +%F).sqlite3
cp -r media /chemin/vers/sauvegardes/media_$(date +%F)
```

Sous Windows, un script `.bat` similaire peut être planifié via le
Planificateur de tâches.

## 6. Points à valider avec la direction (issus du document de spécifications)

- Nombre d'utilisateurs simultanés prévus.
- Hébergement local (ce projet, tel quel) ou sur un serveur cloud plus tard.
- Passage à un pointage par badge/empreinte digitale (le système est conçu pour
  pouvoir brancher une source de pointage automatique plus tard, en remplaçant
  la saisie manuelle par un import).
- Liste définitive des ateliers/services (modifiable dans le menu "Ateliers").
- Formule exacte de calcul du salaire (le calcul actuel est volontairement
  simple : base + primes − retenues − avances).

## 7. Structure du projet

```
djawhara_grh/
├── accounts/       # utilisateurs, rôles, journal de traçabilité
├── core/           # tableau de bord, commande de données de démo
├── employees/      # ateliers, fiches employés, documents
├── attendance/     # pointage quotidien, suivi discipline
├── contracts/      # contrats de travail
├── payroll/        # éléments de paie, primes, retenues
├── reports/        # rapports journaliers/hebdo/mensuels + export CSV
├── templates/       # pages HTML (Django templates)
├── static/css, static/js  # styles et scripts JavaScript du frontend
└── manage.py
```
