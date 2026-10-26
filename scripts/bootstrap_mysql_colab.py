"""MySQL 8.4.10 local en Colab Linux; sin sustituir por otra versión."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

URL='https://downloads.mysql.com/archives/get/p/23/file/mysql-8.4.10-linux-glibc2.17-x86_64-minimal.tar.xz'

def main():
    if sys.platform != 'linux':
        raise SystemExit('Este instalador es para Colab Linux. En Windows use Docker Compose.')
    from scripts.with_env import load_env
    load_env()
    root=Path('.runtime/mysql-colab').resolve()
    root.mkdir(parents=True,exist_ok=True)
    binary=root/'mysql/bin/mysqld'
    if not binary.exists():
        # Las imágenes Colab pueden usar nombres distintos para libaio.
        subprocess.run(['apt-get','update','-qq'],check=True)
        installed=subprocess.run(['apt-get','install','-y','-qq','libaio1','libnuma1'])
        if installed.returncode:
            subprocess.run(['apt-get','install','-y','-qq','libaio1t64','libnuma1'],check=True)
            compat=root/'compat';compat.mkdir(exist_ok=True)
            found=list(Path('/usr/lib/x86_64-linux-gnu').glob('libaio.so.1t64*'))
            if found and not (compat/'libaio.so.1').exists():
                (compat/'libaio.so.1').symlink_to(found[0])
            os.environ['LD_LIBRARY_PATH']=str(compat)+':'+os.environ.get('LD_LIBRARY_PATH','')
        archive=root/'mysql.tar.xz'
        urllib.request.urlretrieve(URL,archive)
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        with tarfile.open(archive) as tar:
            tar.extractall(root,filter='data')
        extracted=next(p for p in root.glob('mysql-*') if p.is_dir())
        extracted.rename(root/'mysql')
        archive.unlink()
        (root/'download.json').write_text(json.dumps({'url':URL,'sha256_descarga':digest}))
    else:
        compat=root/'compat'
        os.environ['LD_LIBRARY_PATH']=str(compat)+':'+os.environ.get('LD_LIBRARY_PATH','')
    env_path=Path('.env')
    if not env_path.exists():
        env_path.write_text('MYSQL_ROOT_PASSWORD='+secrets.token_hex(24)+'\nMYSQL_READONLY_PASSWORD='+secrets.token_hex(24)+'\nMYSQL_PORT=3306\n',encoding='utf-8')
        env_path.chmod(0o600)
    load_env()
    import mysql.connector
    def connect():
        return mysql.connector.connect(host='127.0.0.1',port=int(os.getenv('MYSQL_PORT','3306')),user='root',password=os.environ['MYSQL_ROOT_PASSWORD'],connection_timeout=2)
    try:
        connection=connect()
    except mysql.connector.Error:
        data=root/'data'
        options=[str(binary),'--no-defaults','--basedir='+str(root/'mysql'),'--datadir='+str(data),'--user=root']
        if not data.exists():
            subprocess.run(options+['--initialize-insecure'],check=True)
        secret=root/'init.sql'
        # Contraseñas generadas hex o caracteres escapados; nunca interpoladas en shell.
        password=os.environ['MYSQL_ROOT_PASSWORD'].replace('\\','\\\\').replace("'","''")
        secret.write_text("ALTER USER 'root'@'localhost' IDENTIFIED BY '"+password+"';\n",encoding='utf-8')
        secret.chmod(0o600)
        log=(root/'server.log').open('ab')
        subprocess.Popen(options+['--bind-address=127.0.0.1','--port='+os.getenv('MYSQL_PORT','3306'),'--socket='+str(root/'mysql.sock'),'--mysqlx=OFF','--innodb-buffer-pool-size=128M','--init-file='+str(secret)],stdout=log,stderr=log,start_new_session=True)
        for _ in range(60):
            try:
                connection=connect();break
            except mysql.connector.Error: time.sleep(1)
        else:
            raise RuntimeError('MySQL no arrancó; revise .runtime/mysql-colab/server.log')
        secret.unlink(missing_ok=True)
    cursor=connection.cursor();cursor.execute('SELECT VERSION(), @@sql_mode');version,mode=cursor.fetchone()
    cursor.close();connection.close()
    if version.split('-')[0]!='8.4.10' or 'ONLY_FULL_GROUP_BY' not in mode:
        raise RuntimeError('Motor/configuración incompatibles')
    print('MySQL '+version+' local listo. Credenciales solo en .env excluido de Git.')

if __name__=='__main__':main()
