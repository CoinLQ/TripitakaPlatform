#!/bin/bash
sudo -u postgres psql <<END
drop database if exists tripitaka_platform;
drop user if exists lqzj;
END
sudo -u postgres psql -f utils/setup_db.sql

rm -f tdata/migrations/000*
rm -f tasks/migrations/000*
rm -f rect/migrations/000*
./manage.py makemigrations tdata
./manage.py makemigrations tasks
./manage.py makemigrations rect
cp rect/sql/*.py rect/migrations/.
./manage.py migrate
./manage.py create_configuration
./manage.py import_tripitaka_list
./manage.py import_cbeta_huayan60
./manage.py init
./manage.py initjudge
./manage.py initpunct
./manage.py create_cut_task
./manage.py loaddata ./data/initial_fixtures/demo_auth.json
./manage.py runserver 0.0.0.0:8000

