#!/bin/bash
./utils/fast_prepare_data.sh
./manage.py init
./manage.py runserver 0.0.0.0:8000
