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
./manage.py import_tripitaka_list
./manage.py set_cut_ready
./manage.py import_sutra_reel
./manage.py create_lqreel
./manage.py import_cbeta_huayan60
./manage.py import_reel
./manage.py generate_reel_path
./manage.py download_ready_ocrtext
./manage.py create_huayan60_tasks
