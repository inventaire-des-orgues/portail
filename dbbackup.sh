#!/bin/bash

# =============================================================================
# Script de backup quotidien de la base de données SQLite
# =============================================================================
#
# Politique de rétention :
#   - Les 10 derniers jours
#   - Le backup du 1er de chacun des 5 mois précédents
#
# Installation :
#   1. Rendre le script exécutable :
#      chmod +x dbbackup.sh
#
#   2. Ajouter au cron (exécution quotidienne à 2h du matin) :
#      crontab -e
#      0 2 * * * dbbackup.sh
#
# =============================================================================

# Configuration
SOURCE="A_COMPLETER.sqlite3"
DEST_DIR="/chemin/vers/le/dossier/de/backup"
DATE=$(date +%Y-%m-%d)

# Créer le dossier de destination s'il n'existe pas
mkdir -p "$DEST_DIR"

# Copier la base avec la date du jour
cp "$SOURCE" "$DEST_DIR/db_$DATE.sqlite3"

# Nettoyer les anciens backups
# Conserver : les 10 derniers jours + le 1er de chacun des 5 mois précédents
cd "$DEST_DIR"

# Construire la liste des dates à conserver absolument (1er des 5 mois précédents)
keep_dates=()
for i in 1 2 3 4 5; do
    keep_dates+=( $(date -d "$(date +%Y-%m-01) - $i month" +%Y-%m-01) )
done

today_timestamp=$(date +%s)

for file in db_*.sqlite3; do
    # Extraire la date du nom de fichier
    file_date=$(echo "$file" | sed 's/db_\(.*\)\.sqlite3/\1/')

    # Calculer l'âge en jours
    file_timestamp=$(date -d "$file_date" +%s 2>/dev/null)
    if [ -z "$file_timestamp" ]; then
        continue
    fi

    age_days=$(( (today_timestamp - file_timestamp) / 86400 ))

    # Décider si on garde le fichier
    keep=false

    # Garder les 10 derniers jours
    if [ "$age_days" -le 10 ]; then
        keep=true
    fi

    # Garder les backups du 1er de chacun des 5 mois précédents
    for keep_date in "${keep_dates[@]}"; do
        if [ "$file_date" = "$keep_date" ]; then
            keep=true
        fi
    done

    # Supprimer si on ne garde pas
    if [ "$keep" = false ]; then
        rm "$file"
    fi
done
