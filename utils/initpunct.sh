#!/bin/bash
./utils/prepare_data.sh
./manage.py initpunct
./manage.py runserver 0.0.0.0:8000
