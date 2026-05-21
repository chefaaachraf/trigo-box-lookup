# TRIGO Box Lookup — Documentation Utilisateur

**Version 3.0** | Application de recherche d'emballages TRIGO

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Lancer l'application](#2-lancer-lapplication)
3. [Interface Web — Onglets](#3-interface-web--onglets)
   - [Onglet SCAN EMBALLAGE](#31-onglet-scan-emballage)
   - [Onglet BASE REFS](#32-onglet-base-refs)
   - [Onglet SAISIE MANUELLE](#33-onglet-saisie-manuelle)
4. [Accès mobile (iPhone / Android)](#4-accès-mobile-iphone--android)
5. [Gestion des photos](#5-gestion-des-photos)
6. [Historique des scans](#6-historique-des-scans)
7. [Application bureau (alternative)](#7-application-bureau-alternative)
8. [Déploiement cloud (Render)](#8-déploiement-cloud-render)
9. [Installation et dépendances](#9-installation-et-dépendances)
10. [Résolution de problèmes](#10-résolution-de-problèmes)

---

## 1. Présentation

**TRIGO Box Lookup** permet d'identifier instantanément l'UC (Unité de Conditionnement) correspondant à une référence produit ou un code-barres GALIA.

L'opérateur saisit ou scanne une référence → l'application affiche :
- Le code UC à utiliser
- La photo de l'emballage correspondant
- L'emplacement de stockage
- Les photos de l'emplacement

L'application fonctionne en **deux modes** :
| Mode | Stockage données | Stockage images |
|------|-----------------|-----------------|
| **Local** (PC) | Fichiers JSON + Excel | Dossier `box_images/` local |
| **Cloud** (Render) | PostgreSQL | Cloudinary CDN |

---

## 2. Lancer l'application

### Méthode 1 — Lanceur Windows (recommandé)

Double-cliquer sur `lancer_app.bat`

Ce script :
1. Démarre le serveur FastAPI dans une fenêtre
2. Ouvre un tunnel SSH vers serveo.net dans une autre fenêtre (accès iPhone)
3. Affiche l'URL du tunnel pour l'accès mobile

### Méthode 2 — Ligne de commande

```bash
python server.py
```

Le navigateur s'ouvre automatiquement sur `http://localhost:8000`.
L'IP locale du PC est affichée dans la console pour l'accès réseau.

### Méthode 3 — Application bureau Tkinter

```bash
python box.py
```

Interface native Windows avec les mêmes fonctionnalités.

---

## 3. Interface Web — Onglets

### 3.1 Onglet SCAN EMBALLAGE

C'est l'écran principal utilisé en production.

**Utilisation :**
1. Cliquer dans le champ de saisie (ou le scanner est déjà actif)
2. Scanner le code-barres produit **ou** taper la référence manuellement
3. Appuyer sur **Entrée**

**Résultats affichés :**
- Badge de statut coloré :
  - **TROUVÉ** (vert) — UC identifié
  - **INCOMPLET** (orange) — référence trouvée mais UC manquant
  - **ERREUR** (rouge) — référence inconnue
- Code UC en grand format
- Photo de l'emballage (si disponible)
- Emplacement de stockage
- Photos de l'emplacement (navigation par flèches si plusieurs photos)

**Options :**
- Bouton **Son** — active/désactive le bip sonore de retour
- Le champ se remet à zéro automatiquement après chaque scan

> **Note :** L'application accepte les codes-barres GALIA complets. Elle extrait automatiquement la référence produit par recherche de sous-chaîne.

---

### 3.2 Onglet BASE REFS

Permet de consulter et rechercher toutes les références disponibles.

**Utilisation :**
1. Taper un mot-clé dans la barre de recherche
2. La liste se filtre en temps réel (jusqu'à 300 résultats)
3. Cliquer sur une référence pour voir son détail

**Informations affichées par référence :**
- Référence produit
- Code UC associé
- Emplacement (si renseigné)

---

### 3.3 Onglet SAISIE MANUELLE

Permet d'ajouter, modifier ou supprimer des associations référence → UC qui ne figurent pas dans le fichier Excel.

**Ajouter une entrée :**
1. Renseigner la **Référence** (obligatoire)
2. Renseigner l'**UC** (obligatoire)
3. Renseigner l'**Emplacement** (optionnel)
4. Ajouter une **Description** (optionnel)
5. Cliquer sur **Enregistrer**

**Modifier une entrée existante :**
- Les entrées manuelles apparaissent dans la liste sous le formulaire
- Cliquer sur l'icône d'édition pour recharger dans le formulaire
- Modifier puis cliquer sur **Enregistrer**

**Supprimer une entrée :**
- Cliquer sur l'icône de suppression dans la liste

> **Important :** Les entrées manuelles complètent le fichier Excel `Liste emballages ref Trigo.xlsx`. En cas de doublon, l'entrée manuelle est prioritaire.

---

## 4. Accès mobile (iPhone / Android)

### Via QR Code

1. Sur le PC, accéder à `http://localhost:8000`
2. Un QR code s'affiche en bas de page (ou via l'URL `/api/qrcode.png`)
3. Scanner le QR code avec le téléphone
4. Le téléphone doit être sur le **même réseau Wi-Fi** que le PC

### Via tunnel SSH (accès distant)

Utiliser `lancer_app.bat` — l'URL du tunnel serveo.net s'affiche et est accessible depuis n'importe quel réseau.

### Installer comme PWA

Sur iPhone/Android, une fois l'URL ouverte dans le navigateur :
- **Safari (iPhone) :** Partager → "Sur l'écran d'accueil"
- **Chrome (Android) :** Menu → "Ajouter à l'écran d'accueil"

L'app s'installe et s'ouvre en mode plein écran sans barre d'adresse.

---

## 5. Gestion des photos

### Photos d'emballage (UC)

Les photos sont associées au **code UC** (ex: `BAC-O-1322.jpg`).

**Ajouter/remplacer une photo d'emballage :**
1. Aller dans l'onglet **SAISIE MANUELLE**
2. Sélectionner l'entrée concernée
3. Utiliser le bouton d'upload photo "Emballage"
4. Glisser-déposer l'image ou cliquer pour sélectionner

Formats acceptés : JPG, PNG, WebP

### Photos d'emplacement

Plusieurs photos peuvent être associées à une **référence produit** (ex: `REF_1.jpg`, `REF_2.jpg`…).

**Ajouter des photos d'emplacement :**
1. Aller dans l'onglet **SAISIE MANUELLE**
2. Sélectionner l'entrée concernée
3. Utiliser le bouton d'upload "Emplacement"
4. Plusieurs photos peuvent être ajoutées séquentiellement

**Navigation entre photos d'emplacement :**
Dans l'onglet SCAN EMBALLAGE, des flèches `<` `>` apparaissent sous la photo si plusieurs emplacements sont disponibles.

**Supprimer une photo :**
- Un bouton de suppression est disponible pour chaque photo dans le formulaire d'édition

---

## 6. Historique des scans

L'historique enregistre automatiquement chaque scan effectué (max 2 000 entrées en mode local).

**Accès :** Bouton **Historique** ou section dédiée dans l'interface

**Filtres disponibles :**
| Filtre | Options |
|--------|---------|
| Statut | Tous / TROUVÉ / ERREUR / INCOMPLET |
| Date | Sélecteur de date |
| Recherche | Texte libre (référence, UC, message) |

**Export CSV :**
- Bouton **Exporter CSV** — télécharge l'historique filtré en fichier `.csv`

**Vider l'historique :**
- Bouton **Vider** — supprime tous les enregistrements (action irréversible)

**Colonnes de l'historique :**
- Date / Heure
- Référence scannée (brute)
- Référence normalisée
- UC trouvé
- Statut (TROUVÉ / ERREUR / INCOMPLET)
- Message de résultat

---

## 7. Application bureau (alternative)

`box.py` est une interface Tkinter avec la même logique que l'interface web.

**Différences :**
- Fenêtre native Windows (760×840 px)
- Pas besoin d'un navigateur
- Images affichées directement dans la fenêtre
- Le bouton **Recharger références** relit le fichier Excel à chaud

**Utilisation :**
1. Le focus est automatiquement dans le champ de saisie au démarrage
2. Scanner ou taper la référence → Entrée
3. L'UC et la photo s'affichent immédiatement
4. L'onglet **Historique** liste les derniers scans
5. L'onglet **Saisie manuelle** fonctionne de la même façon que la version web

---

## 8. Déploiement cloud (Render)

### Variables d'environnement requises

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL PostgreSQL (fourni automatiquement par Render) |
| `CLOUDINARY_URL` | URL Cloudinary (format : `cloudinary://key:secret@cloud_name`) |

### Déploiement

1. Connecter le dépôt GitHub à Render
2. Render détecte automatiquement `render.yaml`
3. Les builds se déclenchent à chaque `git push` sur la branche principale
4. Commande de démarrage : `uvicorn server:app --host 0.0.0.0 --port $PORT`

### Comportement en cloud

- Les données sont stockées en **PostgreSQL** (pas de fichiers JSON)
- Les images sont hébergées sur **Cloudinary** (pas de dossier local)
- L'application détecte automatiquement le mode selon la présence des variables d'environnement

---

## 9. Installation et dépendances

### Prérequis

- Python 3.10 ou supérieur
- Fichier `Liste emballages ref Trigo.xlsx` présent à la racine du projet (feuille `Feuil3`)

### Installation

```bash
pip install -r requirements.txt
```

### Dépendances principales

| Librairie | Rôle |
|-----------|------|
| `fastapi` | Serveur web API |
| `uvicorn` | Serveur ASGI |
| `pandas` + `openpyxl` | Lecture du fichier Excel |
| `Pillow` | Traitement des images |
| `qrcode[pil]` | Génération du QR code réseau |
| `psycopg2-binary` | Connexion PostgreSQL (cloud) |
| `cloudinary` | CDN images (cloud) |
| `ttkbootstrap` | Thème UI pour `box.py` |

### Structure des dossiers

```
TRIGO_BoxApp/
├── server.py                          # Serveur FastAPI (point d'entrée web)
├── box.py                             # Application bureau Tkinter
├── database.py                        # Module PostgreSQL (cloud)
├── cloudstore.py                      # Module Cloudinary (cloud)
├── Liste emballages ref Trigo.xlsx    # Base de données références (OBLIGATOIRE)
├── requirements.txt                   # Dépendances Python
├── render.yaml                        # Config déploiement Render
├── lancer_app.bat                     # Lanceur Windows
├── manual_entries.json                # Entrées manuelles (mode local)
├── scan_history.json                  # Historique des scans (mode local)
├── box_images/                        # Photos emballages (mode local)
├── placement_images/                  # Photos emplacements (mode local)
└── static/
    ├── index.html                     # Interface web
    ├── app.js                         # Logique frontend
    ├── style.css                      # Styles TRIGO
    ├── manifest.json                  # Config PWA
    └── logo.png                       # Logo TRIGO
```

---

## 10. Résolution de problèmes

### Le navigateur ne s'ouvre pas automatiquement
Ouvrir manuellement `http://localhost:8000` dans le navigateur.

### "Référence non trouvée" pour une référence qui devrait exister
- Vérifier que la référence est bien dans le fichier `Liste emballages ref Trigo.xlsx`, feuille `Feuil3`
- S'assurer que la référence est dans la colonne correcte
- Redémarrer le serveur pour recharger le fichier Excel

### Aucune photo ne s'affiche
- Vérifier que le fichier image est dans le dossier `box_images/` avec le nom exact du code UC (ex: `BAC-O-1322.jpg`)
- Les formats supportés sont : `.jpg`, `.jpeg`, `.png`, `.webp`

### L'accès depuis le téléphone ne fonctionne pas
- Vérifier que le PC et le téléphone sont sur le même réseau Wi-Fi
- Désactiver temporairement le pare-feu Windows pour tester
- Utiliser l'URL avec l'IP locale affichée dans la console (ex: `http://192.168.1.x:8000`)

### Le tunnel serveo.net ne se connecte pas
- Vérifier la connexion Internet
- Relancer `lancer_app.bat`
- En cas d'échec persistant, utiliser directement l'IP locale sur le réseau Wi-Fi

### Erreur au démarrage : fichier Excel introuvable
- S'assurer que `Liste emballages ref Trigo.xlsx` est présent à la racine du projet
- Vérifier que la feuille s'appelle bien `Feuil3`

---

*Documentation générée pour TRIGO Box Lookup v3.0 — TRIGO SAS*
