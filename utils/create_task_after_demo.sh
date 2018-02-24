#!/bin/bash
./manage.py set_cut_ready
./manage.py import_reel
./manage.py create_lqreel
./manage.py generate_reel_path
#./manage.py download_ready_ocrtext
./manage.py create_huayan60_tasks
