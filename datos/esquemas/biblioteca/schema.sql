CREATE TABLE autores (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, edad INT) COMMENT='Dominio biblioteca: autores';
CREATE TABLE libros (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, autor_id INT, paginas INT, valor DECIMAL(10,2), FOREIGN KEY (autor_id) REFERENCES autores(id)) COMMENT='Dominio biblioteca: libros';
CREATE TABLE lectores (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, edad INT) COMMENT='Dominio biblioteca: lectores';
CREATE TABLE prestamos (id INT PRIMARY KEY COMMENT 'Identificador único', lector_id INT, libro_id INT, dias INT, fecha DATE, FOREIGN KEY (lector_id) REFERENCES lectores(id), FOREIGN KEY (libro_id) REFERENCES libros(id)) COMMENT='Dominio biblioteca: prestamos';
