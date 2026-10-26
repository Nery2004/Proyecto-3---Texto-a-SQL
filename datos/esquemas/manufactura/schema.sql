CREATE TABLE plantas (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, capacidad INT) COMMENT='Dominio manufactura: plantas';
CREATE TABLE maquinas (id INT PRIMARY KEY COMMENT 'Identificador único', planta_id INT, nombre TEXT, costo DECIMAL(10,2), FOREIGN KEY (planta_id) REFERENCES plantas(id)) COMMENT='Dominio manufactura: maquinas';
CREATE TABLE lotes (id INT PRIMARY KEY COMMENT 'Identificador único', maquina_id INT, unidades INT, defectos INT, fecha DATE, FOREIGN KEY (maquina_id) REFERENCES maquinas(id)) COMMENT='Dominio manufactura: lotes';
CREATE TABLE inspecciones (id INT PRIMARY KEY COMMENT 'Identificador único', lote_id INT, puntaje DECIMAL(10,2), fecha DATE, FOREIGN KEY (lote_id) REFERENCES lotes(id)) COMMENT='Dominio manufactura: inspecciones';
