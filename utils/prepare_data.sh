#!/bin/bash
sid="LQ003100"
if [ "$1" != '' ]; then
    sid=$1
fi
echo prepare data for $sid
./utils/initdb.sh
mkdir -p logs

./manage.py create_configuration
./manage.py import_tripitaka_list
./manage.py set_cut_ready
./manage.py loaddata ./data/initial_fixtures/demo_auth.json
./manage.py create_xadmin_bookmark

./manage.py import_lqsutra $sid
./manage.py create_lqreel $sid
./manage.py import_reel $sid
 
./manage.py import_cbeta_text $sid

./manage.py import_ocr_ready_list
./manage.py import_gl
