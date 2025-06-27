#!/bin/sh

set -e  # Stoppe le script en cas d'erreur

# Variables de connexion (à adapter si besoin ou à passer en argument)
DB_HOST=${DB_HOST:-jobs-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-jobs_db}
DB_USER=${DB_USER:-dani}
DB_PASSWORD=${DB_PASSWORD:-motdepasse}

export PGPASSWORD="$DB_PASSWORD"

echo "Execution du script : schema.sql"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/schema.sql

echo "Execution du script : indexes.sql"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/indexes.sql

echo "Execution du script : triggers.sql"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/triggers.sql

echo "Tous les scripts ont été exécutés avec succès !"
