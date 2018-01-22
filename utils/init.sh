#!/bin/bash
sudo -u postgres psql <<END
drop database if exists tripitaka_platform;
drop user if exists dzj;
END
sudo -u postgres psql -f utils/setup_db.sql

rm -f sutradata/migrations/000*
rm -f tasks/migrations/000*
./manage.py makemigrations sutradata
./manage.py makemigrations tasks
./manage.py migrate
./manage.py import_tripitaka_list
./manage.py init
./manage.py runserver 0.0.0.0:8000

