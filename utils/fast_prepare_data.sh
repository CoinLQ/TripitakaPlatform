#!/bin/bash
sid="LQ003100"
if [ "$1" != '' ]; then
    sid=$1
fi
echo prepare data for $sid
./utils/initdb.sh
mkdir -p logs log

./manage.py loaddata ./data/initial_fixtures/demo_auth.json
./manage.py loaddata ./data/initial_fixtures/cbeta_gl_60huayan.json

