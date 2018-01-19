#!/bin/bash
sudo -u postgres psql <<END
drop database tripitaka_platform;
END
sudo -u dzj createdb tripitaka_platform;

rm sutradata/migrations/000*
rm tasks/migrations/000*
./manage.py makemigrations sutradata
./manage.py makemigrations tasks
./manage.py migrate
./manage.py import_tripitaka_list
./manage.py init
./manage.py runserver 0.0.0.0:8000

