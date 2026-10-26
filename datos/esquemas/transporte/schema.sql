CREATE TABLE rutas (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, distancia DECIMAL(10,2)) COMMENT='Dominio transporte: rutas';
CREATE TABLE conductores (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, edad INT) COMMENT='Dominio transporte: conductores';
CREATE TABLE vehiculos (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, capacidad INT, costo DECIMAL(10,2)) COMMENT='Dominio transporte: vehiculos';
CREATE TABLE viajes (id INT PRIMARY KEY COMMENT 'Identificador único', ruta_id INT, conductor_id INT, vehiculo_id INT, pasajeros INT, fecha DATE, FOREIGN KEY (ruta_id) REFERENCES rutas(id), FOREIGN KEY (conductor_id) REFERENCES conductores(id), FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)) COMMENT='Dominio transporte: viajes';
