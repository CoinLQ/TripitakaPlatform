### 安装数据库
sudo apt install postgresql

### 创建数据库相关用户
sudo useradd -m dzj

sudo -u postgres createuser -d -P dzj

输入密码dzj

### 创建Python虚拟环境
virtualenv -p /usr/bin/python3 venv

source venv/bin/activate

### 在Python虚拟环境下安装python包
pip install django==2.0.1

pip install psycopg2 

pip install django-extensions

pip install django-bootstrap3

pip install -U pylint

pip install -U autopep8


### 修改配置为本机IP
sudo apt install net-tools

ifconfig

将utils/init.sh中的192.168.2.196改为本机IP

### 在Python虚拟环境下运行
./utils/init.sh
