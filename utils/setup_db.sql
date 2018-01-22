CREATE DATABASE tripitaka_platform;
CREATE USER dzj WITH PASSWORD 'dzj';
ALTER ROLE dzj SET client_encoding TO 'utf8';
ALTER ROLE dzj SET default_transaction_isolation TO 'read committed';
ALTER ROLE dzj SET timezone TO 'PRC';
GRANT ALL PRIVILEGES ON DATABASE tripitaka_platform TO dzj;
\q