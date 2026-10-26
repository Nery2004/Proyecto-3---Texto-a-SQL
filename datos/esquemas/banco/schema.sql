CREATE TABLE sucursales (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, presupuesto DECIMAL(10,2)) COMMENT='Dominio banco: sucursales';
CREATE TABLE clientes (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, edad INT) COMMENT='Dominio banco: clientes';
CREATE TABLE cuentas (id INT PRIMARY KEY COMMENT 'Identificador único', cliente_id INT, sucursal_id INT, saldo DECIMAL(10,2), FOREIGN KEY (cliente_id) REFERENCES clientes(id), FOREIGN KEY (sucursal_id) REFERENCES sucursales(id)) COMMENT='Dominio banco: cuentas';
CREATE TABLE movimientos (id INT PRIMARY KEY COMMENT 'Identificador único', cuenta_id INT, monto DECIMAL(10,2), fecha DATE, FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)) COMMENT='Dominio banco: movimientos';
