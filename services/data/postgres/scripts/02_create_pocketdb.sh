#!/bin/bash
echo "Creating pocketdb database for user $POSTGRES_USER"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE pocketdb OWNER $POSTGRES_USER;"
psql -U "$POSTGRES_USER" -d "pocketdb" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"; CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";" 