CREATE TABLE hoteles (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, estrellas INT) COMMENT='Dominio hoteleria: hoteles';
CREATE TABLE habitaciones (id INT PRIMARY KEY COMMENT 'Identificador único', hotel_id INT, numero INT, tarifa DECIMAL(10,2), FOREIGN KEY (hotel_id) REFERENCES hoteles(id)) COMMENT='Dominio hoteleria: habitaciones';
CREATE TABLE huespedes (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, edad INT) COMMENT='Dominio hoteleria: huespedes';
CREATE TABLE estancias (id INT PRIMARY KEY COMMENT 'Identificador único', habitacion_id INT, huesped_id INT, noches INT, fecha DATE, FOREIGN KEY (habitacion_id) REFERENCES habitaciones(id), FOREIGN KEY (huesped_id) REFERENCES huespedes(id)) COMMENT='Dominio hoteleria: estancias';
