#!/bin/bash
./utils/initdb.sh

./manage.py create_configuration
./manage.py import_tripitaka_list
./manage.py set_cut_ready
./manage.py loaddata ./data/initial_fixtures/demo_auth.json

./manage.py import_lqsutra
./manage.py create_lqreel LQ003100
./manage.py import_reel LQ003100

./manage.py import_cbeta_huayan60
./manage.py import_gl

./manage.py import_ocr_ready_list
