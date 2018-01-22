## 配置环境
### 安装数据库
sudo apt install postgresql

### 配置数据库
sudo -u postgres psql -f utils/setup_db.sql

### 创建Python虚拟环境
virtualenv -p /usr/bin/python3 venv

### 进入Python虚拟环境
source venv/bin/activate

### 在Python虚拟环境下安装python包
pip install -r requirements.txt

pip install ipython

### 下载static文件
./utils/download_static.sh

### 在Python虚拟环境下运行
./utils/init.sh
