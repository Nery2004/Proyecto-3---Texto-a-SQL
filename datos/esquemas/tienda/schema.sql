CREATE TABLE categorias (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT) COMMENT='Dominio tienda: categorias';
CREATE TABLE productos (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, categoria_id INT, precio DECIMAL(10,2), stock INT, FOREIGN KEY (categoria_id) REFERENCES categorias(id)) COMMENT='Dominio tienda: productos';
CREATE TABLE compradores (id INT PRIMARY KEY COMMENT 'Identificador único', nombre TEXT, edad INT) COMMENT='Dominio tienda: compradores';
CREATE TABLE ventas (id INT PRIMARY KEY COMMENT 'Identificador único', comprador_id INT, total DECIMAL(10,2), fecha DATE, FOREIGN KEY (comprador_id) REFERENCES compradores(id)) COMMENT='Dominio tienda: ventas';
CREATE TABLE detalles (id INT PRIMARY KEY COMMENT 'Identificador único', venta_id INT, producto_id INT, cantidad INT, subtotal DECIMAL(10,2), FOREIGN KEY (venta_id) REFERENCES ventas(id), FOREIGN KEY (producto_id) REFERENCES productos(id)) COMMENT='Dominio tienda: detalles';
