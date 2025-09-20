-- Database initialization script for production deployment
-- This script will be executed when the PostgreSQL container starts

-- Create the monitoring database if it doesn't exist
-- (This is handled by POSTGRES_DB environment variable)

-- Create additional indexes for better performance
-- These will be created after Alembic migrations run

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE monitoring TO monitoring_user;

-- Create extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Log the initialization
\echo 'Database initialization completed successfully'