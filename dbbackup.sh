#!/bin/bash

# =============================================================================
# Script de backup quotidien de la base de données SQLite
# =============================================================================
#
# Politique de rétention :
#   - Les 10 derniers jours
#   - Les backups d'il y a 30, 60 et 120 jours
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
# Conserver : les 10 derniers jours + 30, 60 et 120 jours
cd "$DEST_DIR"

for file in db_*.sqlite3; do
    # Extraire la date du nom de fichier
    file_date=$(echo "$file" | sed 's/db_\(.*\)\.sqlite3/\1/')

    # Calculer l'âge en jours
    file_timestamp=$(date -d "$file_date" +%s 2>/dev/null)
    if [ -z "$file_timestamp" ]; then
        continue
    fi

    today_timestamp=$(date +%s)
    age_days=$(( (today_timestamp - file_timestamp) / 86400 ))

    # Décider si on garde le fichier
    keep=false

    # Garder les 10 derniers jours
    if [ "$age_days" -le 10 ]; then
        keep=true
    fi

    # Garder les backups de 30, 60 et 120 jours (avec une marge de +/- 1 jour)
    for retention_day in 30 60 120; do
        if [ "$age_days" -ge $((retention_day - 1)) ] && [ "$age_days" -le $((retention_day + 1)) ]; then
            keep=true
        fi
    done

    # Supprimer si on ne garde pas
    if [ "$keep" = false ]; then
        rm "$file"
    fi
done
