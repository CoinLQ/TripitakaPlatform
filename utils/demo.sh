#!/bin/bash
./utils/fast_prepare_data.sh

./manage.py init
./manage.py init_mark
./manage.py initjudge
./manage.py create_cut_task
