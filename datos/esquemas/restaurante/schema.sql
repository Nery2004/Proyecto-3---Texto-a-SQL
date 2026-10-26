CREATE TABLE mesas (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, capacidad INT) COMMENT='Dominio restaurante: mesas';
CREATE TABLE platos (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, precio DECIMAL(10,2), calorias INT) COMMENT='Dominio restaurante: platos';
CREATE TABLE ordenes (id INT PRIMARY KEY COMMENT 'Identificador único', mesa_id INT, total DECIMAL(10,2), fecha DATE, FOREIGN KEY (mesa_id) REFERENCES mesas(id)) COMMENT='Dominio restaurante: ordenes';
CREATE TABLE lineas (id INT PRIMARY KEY COMMENT 'Identificador único', orden_id INT, plato_id INT, cantidad INT, FOREIGN KEY (orden_id) REFERENCES ordenes(id), FOREIGN KEY (plato_id) REFERENCES platos(id)) COMMENT='Dominio restaurante: lineas';
