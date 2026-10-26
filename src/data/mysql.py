"""Strict real MySQL 8.4.10 execution adapter; credentials only from environment."""
import os
from contextlib import contextmanager

class MySQLExecutor:
    def __init__(self,schema_id):
        from .generate import DOMAINS
        if schema_id not in DOMAINS: raise ValueError('Esquema desconocido')
        import mysql.connector
        self.connection=mysql.connector.connect(host=os.getenv('MYSQL_HOST','127.0.0.1'),port=int(os.getenv('MYSQL_PORT','3306')),user=os.getenv('MYSQL_READONLY_USER','textsql_reader'),password=os.environ['MYSQL_READONLY_PASSWORD'],database='textsql_'+schema_id,connection_timeout=10,autocommit=True)
        cursor=self.connection.cursor()
        cursor.execute('SELECT VERSION(), @@SESSION.sql_mode')
        version,mode=cursor.fetchone()
        if version.split('-')[0]!='8.4.10': raise RuntimeError(f'Requiere MySQL 8.4.10, recibido {version}')
        if 'ONLY_FULL_GROUP_BY' not in mode.split(','): raise RuntimeError('ONLY_FULL_GROUP_BY debe estar activo')
        cursor.execute('SHOW GRANTS FOR CURRENT_USER()')
        grants=[row[0].upper() for row in cursor.fetchall()]
        for grant in grants:
            privileges=grant.split(' ON ')[0].removeprefix('GRANT ')
            if privileges not in ('USAGE','SELECT') or 'WITH GRANT OPTION' in grant:
                raise RuntimeError('Usuario no es exclusivamente de lectura; no use roles ni permisos adicionales')
        cursor.close()
        self.version=version
    def __call__(self,sql):
        from src.inference.safety import validate_sql
        cursor=None
        try:
            sql=validate_sql(sql)
            cursor=self.connection.cursor()
            cursor.execute('SET SESSION MAX_EXECUTION_TIME=5000')
            cursor.execute('START TRANSACTION READ ONLY')
            cursor.execute(sql)
            columns=[x[0] for x in cursor.description]
            rows=cursor.fetchmany(10001)
            if len(rows)>10000: raise RuntimeError('Resultado excede límite de 10000 filas')
            return {'ok':True,'columnas':columns,'filas':rows,'error':None}
        except Exception as exc:
            return {'ok':False,'columnas':[],'filas':[],'error':str(exc),'errno':getattr(exc,'errno',None)}
        finally:
            self.connection.rollback()
            if cursor: cursor.close()
    def close(self): self.connection.close()
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

def initialize():
    """Administrative fixture setup is separate from candidate SELECT execution."""
    import mysql.connector
    from .generate import DOMAINS,schema_sql,fixtures
    connection=mysql.connector.connect(host=os.getenv('MYSQL_HOST','127.0.0.1'),port=int(os.getenv('MYSQL_PORT','3306')),user='root',password=os.environ['MYSQL_ROOT_PASSWORD'])
    try:
        cursor=connection.cursor()
        cursor.execute('SELECT VERSION()')
        if cursor.fetchone()[0].split('-')[0]!='8.4.10': raise RuntimeError('Se requiere MySQL 8.4.10')
        user=os.getenv('MYSQL_READONLY_USER','textsql_reader')
        password=os.environ['MYSQL_READONLY_PASSWORD']
        cursor.execute('CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s',(user,'%',password))
        cursor.execute('ALTER USER %s@%s IDENTIFIED BY %s',(user,'%',password))
        cursor.execute('REVOKE ALL PRIVILEGES, GRANT OPTION FROM %s@%s',(user,'%'))
        for schema_id in DOMAINS:
            database='textsql_'+schema_id
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS `{database}`')
            cursor.execute(f'USE `{database}`')
            cursor.execute('SHOW TABLES')
            if cursor.fetchall(): raise RuntimeError(f'{database} no está vacío; no se sobrescriben datos existentes')
            for statement in (schema_sql(schema_id)+'\n'+fixtures(schema_id)).split(';'):
                if statement.strip(): cursor.execute(statement)
            cursor.execute(f'GRANT SELECT ON `{database}`.* TO %s@%s',(user,'%'))
        connection.commit()
    finally: connection.close()
