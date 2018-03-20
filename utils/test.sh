#!/bin/bash
./utils/initdb.sh

./manage.py create_configuration
./manage.py import_tripitaka_list
./manage.py set_cut_ready
./manage.py loaddata ./data/initial_fixtures/demo_auth.json

./manage.py import_lqsutra
./manage.py create_lqreel LQ003900
./manage.py import_reel LQ003900
 
./manage.py import_cbeta_text LQ003900
./manage.py import_gl

./manage.py import_ocr_ready_list

./manage.py download_ready_ocrtext LQ003900
./manage.py create_tasks LQ003900

./manage.py runserver 0.0.0.0:8000