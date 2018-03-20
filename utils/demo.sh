#!/bin/bash
./utils/prepare_data.sh

./manage.py init
./manage.py initjudge
./manage.py initpunct
./manage.py create_cut_task
./manage.py create_tasks LQ003100