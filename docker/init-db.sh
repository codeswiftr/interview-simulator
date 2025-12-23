#!/bin/bash
# =============================================================================
# PostgreSQL Initialization Script
# Runs on first container startup to configure database
# =============================================================================

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    -- Set timezone
    ALTER DATABASE $POSTGRES_DB SET timezone TO 'UTC';

    -- Performance tuning for staging (adjust based on available resources)
    ALTER SYSTEM SET shared_buffers = '256MB';
    ALTER SYSTEM SET effective_cache_size = '1GB';
    ALTER SYSTEM SET maintenance_work_mem = '64MB';
    ALTER SYSTEM SET checkpoint_completion_target = 0.9;
    ALTER SYSTEM SET wal_buffers = '16MB';
    ALTER SYSTEM SET default_statistics_target = 100;
    ALTER SYSTEM SET random_page_cost = 1.1;
    ALTER SYSTEM SET effective_io_concurrency = 200;
    ALTER SYSTEM SET work_mem = '4MB';
    ALTER SYSTEM SET min_wal_size = '1GB';
    ALTER SYSTEM SET max_wal_size = '4GB';

    -- Log configuration for debugging
    ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
    ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

    SELECT 'Database initialized successfully' AS status;
EOSQL

echo "PostgreSQL initialization complete"
