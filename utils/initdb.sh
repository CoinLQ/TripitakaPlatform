sudo -u postgres psql <<END
drop database if exists tripitaka_platform;
drop user if exists lqzj;
END
sudo -u postgres psql -f utils/setup_db.sql 
# sudo -u postgres psql -f /home/xian/tripitakaplatform/restore.sql

# # ============ get the file name ===========    
# Folder_A="/home/xian/Downloads/tripidata"    
# for file_a in ${Folder_A}/*  
# do    
#     temp_file=`basename $file_a`    
#     sudo -u postgres psql -f /home/xian/Downloads/tripidata/$temp_file    
# done

./manage.py migrate
