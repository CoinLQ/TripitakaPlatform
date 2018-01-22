CREATE DATABASE tripitaka_platform;
CREATE USER lqzj WITH PASSWORD 'lqdzjsql';
ALTER ROLE lqzj SET client_encoding TO 'utf8';
ALTER ROLE lqzj SET default_transaction_isolation TO 'read committed';
ALTER ROLE lqzj SET timezone TO 'PRC';
GRANT ALL PRIVILEGES ON DATABASE tripitaka_platform TO lqzj;
\q
