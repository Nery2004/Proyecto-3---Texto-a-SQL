CREATE TABLE facultades (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT) COMMENT='Dominio universidad: facultades';
CREATE TABLE alumnos (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, edad INT, promedio DECIMAL(10,2), facultad_id INT, FOREIGN KEY (facultad_id) REFERENCES facultades(id)) COMMENT='Dominio universidad: alumnos';
CREATE TABLE cursos (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, creditos INT, costo DECIMAL(10,2)) COMMENT='Dominio universidad: cursos';
CREATE TABLE inscripciones (id INT PRIMARY KEY COMMENT 'Identificador único', alumno_id INT, curso_id INT, nota DECIMAL(10,2), fecha DATE, FOREIGN KEY (alumno_id) REFERENCES alumnos(id), FOREIGN KEY (curso_id) REFERENCES cursos(id)) COMMENT='Dominio universidad: inscripciones';
