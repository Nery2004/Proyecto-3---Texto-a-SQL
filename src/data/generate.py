"""Reproducible original schemas, fixtures and question/SQL candidates."""
from pathlib import Path
import json
import sqlglot
from itertools import combinations

# Each domain deliberately has its own relationship graph and domain vocabulary.
DOMAINS = {
 'universidad': [('facultades','nombre TEXT'),('alumnos','nombre TEXT, edad INT, promedio DECIMAL(10,2), facultad_id INT'),('cursos','nombre TEXT, creditos INT, costo DECIMAL(10,2)'),('inscripciones','alumno_id INT, curso_id INT, nota DECIMAL(10,2), fecha DATE')],
 'hospital': [('especialidades','nombre TEXT'),('medicos','nombre TEXT, especialidad_id INT, salario DECIMAL(10,2)'),('pacientes','nombre TEXT, edad INT, peso DECIMAL(10,2)'),('consultas','medico_id INT, paciente_id INT, costo DECIMAL(10,2), fecha DATE'),('recetas','consulta_id INT, dosis INT, precio DECIMAL(10,2)')],
 'banco': [('sucursales','nombre TEXT, presupuesto DECIMAL(10,2)'),('clientes','nombre TEXT, edad INT'),('cuentas','cliente_id INT, sucursal_id INT, saldo DECIMAL(10,2)'),('movimientos','cuenta_id INT, monto DECIMAL(10,2), fecha DATE')],
 'tienda': [('categorias','nombre TEXT'),('productos','nombre TEXT, categoria_id INT, precio DECIMAL(10,2), stock INT'),('compradores','nombre TEXT, edad INT'),('ventas','comprador_id INT, total DECIMAL(10,2), fecha DATE'),('detalles','venta_id INT, producto_id INT, cantidad INT, subtotal DECIMAL(10,2)')],
 'inventarios': [('almacenes','nombre TEXT, capacidad INT'),('proveedores','nombre TEXT, credito DECIMAL(10,2)'),('articulos','nombre TEXT, proveedor_id INT, costo DECIMAL(10,2)'),('existencias','almacen_id INT, articulo_id INT, unidades INT, fecha DATE')],
 'restaurante': [('mesas','nombre TEXT, capacidad INT'),('platos','nombre TEXT, precio DECIMAL(10,2), calorias INT'),('ordenes','mesa_id INT, total DECIMAL(10,2), fecha DATE'),('lineas','orden_id INT, plato_id INT, cantidad INT')],
 'biblioteca': [('autores','nombre TEXT, edad INT'),('libros','nombre TEXT, autor_id INT, paginas INT, valor DECIMAL(10,2)'),('lectores','nombre TEXT, edad INT'),('prestamos','lector_id INT, libro_id INT, dias INT, fecha DATE')],
 'transporte': [('rutas','nombre TEXT, distancia DECIMAL(10,2)'),('conductores','nombre TEXT, edad INT'),('vehiculos','nombre TEXT, capacidad INT, costo DECIMAL(10,2)'),('viajes','ruta_id INT, conductor_id INT, vehiculo_id INT, pasajeros INT, fecha DATE')],
 'rrhh': [('departments','nombre TEXT, presupuesto DECIMAL(10,2)'),('employees','nombre TEXT, department_id INT, salario DECIMAL(10,2), edad INT'),('projects','nombre TEXT, presupuesto DECIMAL(10,2)'),('assignments','employee_id INT, project_id INT, horas INT, fecha DATE'),('bonuses','employee_id INT, monto DECIMAL(10,2), fecha DATE')],
 'reservaciones': [('salones','nombre TEXT, capacidad INT, tarifa DECIMAL(10,2)'),('organizadores','nombre TEXT, credito DECIMAL(10,2)'),('eventos','salon_id INT, organizador_id INT, asistentes INT, fecha DATE')],
 'hoteleria': [('hoteles','nombre TEXT, estrellas INT'),('habitaciones','hotel_id INT, numero INT, tarifa DECIMAL(10,2)'),('huespedes','nombre TEXT, edad INT'),('estancias','habitacion_id INT, huesped_id INT, noches INT, fecha DATE')],
 'manufactura': [('plantas','nombre TEXT, capacidad INT'),('maquinas','planta_id INT, nombre TEXT, costo DECIMAL(10,2)'),('lotes','maquina_id INT, unidades INT, defectos INT, fecha DATE'),('inspecciones','lote_id INT, puntaje DECIMAL(10,2), fecha DATE')]
}
RELATIONS = {
 'facultad':'facultades','alumno':'alumnos','curso':'cursos','especialidad':'especialidades','medico':'medicos','paciente':'pacientes','consulta':'consultas','cliente':'clientes','sucursal':'sucursales','cuenta':'cuentas','categoria':'categorias','comprador':'compradores','venta':'ventas','producto':'productos','proveedor':'proveedores','almacen':'almacenes','articulo':'articulos','mesa':'mesas','orden':'ordenes','plato':'platos','autor':'autores','lector':'lectores','libro':'libros','ruta':'rutas','conductor':'conductores','vehiculo':'vehiculos','department':'departments','employee':'employees','project':'projects','salon':'salones','organizador':'organizadores','hotel':'hoteles','habitacion':'habitaciones','huesped':'huespedes','planta':'plantas','maquina':'maquinas','lote':'lotes'
}

def columns(definition):
    # Decimal's comma must not split column definitions.
    import re
    return [tuple(x.strip().split(' ',1)) for x in re.split(r', (?!\d)',definition)]

def schema_sql(schema_id):
    statements=[]
    for table,definition in DOMAINS[schema_id]:
        cols=columns(definition)
        fields=['id INT PRIMARY KEY COMMENT \'Identificador único\'']+[f'{name} {typ}' for name,typ in cols]
        fields += [f'FOREIGN KEY ({name}) REFERENCES {RELATIONS[name[:-3]]}(id)' for name,_ in cols if name.endswith('_id')]
        statements.append(f"CREATE TABLE {table} ("+', '.join(fields)+f") COMMENT='Dominio {schema_id}: {table}';")
    return '\n'.join(statements)

def fixtures(schema_id):
    statements=[]
    for table,definition in DOMAINS[schema_id]:
        cols=columns(definition)
        for i in range(1,13):
            vals=[str(i)]
            for column_index,(name,typ) in enumerate(cols):
                if name.endswith('_id'): val=str((i*5+column_index*3)%8+1)
                elif typ=='TEXT': val=f"'{table} grupo {(i%4)+1}'"
                elif typ=='DATE': val=f"'{2024+(i%2)}-{(i%12)+1:02d}-{(i%27)+1:02d}'"
                else: val=str(((i%6)*(17+column_index*3)+column_index*11)%97+1)
                vals.append(val)
            statements.append(f"INSERT INTO {table} VALUES ("+', '.join(vals)+');')
    return '\n'.join(statements)

def candidates(schema_id):
    ddl=schema_sql(schema_id)
    rows=[]
    def add(question,sql,difficulty,kind):
        ordered = sqlglot.parse_one(sql, read='mysql').args.get('order') is not None
        rows.append(dict(id=f'{schema_id}-{len(rows)+1:05d}',schema_id=schema_id,esquema=ddl,pregunta=question,sql=sql,dificultad=difficulty,tipo_consulta=kind,origen='Codex: plantilla semántica original v2; columnas explícitas',validado=False,revision_humana='pendiente',requiere_orden=ordered))
    for table,definition in DOMAINS[schema_id]:
        cols=columns(definition)
        numeric=[n for n,t in cols if t!='TEXT' and t!='DATE' and not n.endswith('_id')]
        for n in numeric:
            for op,label in [('>','mayor que'),('<','menor que'),('=','igual a')]:
                for threshold in [20,50,80]:
                    add(f'Lista id y {n} de {table} con {n} {label} {threshold}, ordenados por {n} y después id.',f'SELECT id, {n} FROM {table} WHERE {n} {op} {threshold} ORDER BY {n}, id','facil','filtro')
            for fn,word in [('AVG','promedio'),('SUM','suma'),('MAX','máximo'),('MIN','mínimo')]:
                add(f'¿Cuál es el {word} de {n} en {table}?',f'SELECT {fn}({n}) AS valor FROM {table}','media','agregacion')
                add(f'¿Cuál es el {word} de {n} entre los registros de {table} cuyo id es par?',f'SELECT {fn}({n}) AS valor FROM {table} WHERE MOD(id, 2) = 0','media','agregacion')
            for threshold in [20,50,80]:
                for fn,word in [('COUNT','cantidad'),('SUM','suma'),('AVG','promedio'),('MAX','máximo')]:
                    expr='*' if fn=='COUNT' else n
                    add(f'Calcula {word} de '+('registros' if fn=='COUNT' else n)+f' entre los registros de {table} donde {n} supera {threshold}.',f'SELECT {fn}({expr}) AS valor FROM {table} WHERE {n} > {threshold}','media','agregacion_filtrada')
            add(f'Muestra id y {n} de {table} por encima de su promedio.',f'SELECT id, {n} FROM {table} WHERE {n} > (SELECT AVG({n}) FROM {table})','dificil','subconsulta')
            add(f'Muestra exactamente id, {n} y un rango global de {table} calculado por {n} descendente: los empates comparten rango y no se dejan saltos entre rangos. No dividas los registros en grupos.',f'SELECT id, {n}, DENSE_RANK() OVER (ORDER BY {n} DESC) AS rango FROM {table}','dificil','ventana')
            add(f'Muestra exactamente id y la suma acumulada de {n} en {table}, calculada siguiendo el orden ascendente de id e incluyendo el registro actual.',f'SELECT id, SUM({n}) OVER (ORDER BY id ROWS UNBOUNDED PRECEDING) AS acumulado FROM {table}','dificil','ventana')
            add(f'Usando una CTE, lista id de {table} cuyo {n} supera su promedio.',f'WITH promedio AS (SELECT AVG({n}) AS valor FROM {table}) SELECT t.id FROM {table} t CROSS JOIN promedio p WHERE t.{n} > p.valor','dificil','cte')
        for n in numeric:
            for group,typ in cols:
                if group==n: continue
                for fn,word in [('AVG','promedio'),('SUM','suma'),('MAX','máximo'),('MIN','mínimo')]:
                    add(f'Devuelve exactamente {group} y el {word} de {n}, una fila por cada valor distinto de {group} en {table}.',f'SELECT {group}, {fn}({n}) AS valor FROM {table} GROUP BY {group}','media','agregacion_por_atributo')
                    add(f'Devuelve exactamente {group} y el {word} de {n} para los grupos de {table} cuyo {word} de {n} supera el promedio global de {n} de toda la tabla.',f'SELECT {group}, {fn}({n}) AS valor FROM {table} GROUP BY {group} HAVING {fn}({n}) > (SELECT AVG({n}) FROM {table})','dificil','having_subconsulta')
                add(f'Devuelve exactamente {group} y la cantidad de valores distintos de {n}, una fila por cada {group} en {table}.',f'SELECT {group}, COUNT(DISTINCT {n}) AS distintos FROM {table} GROUP BY {group}','media','conteo_distinto')
                add(f'Devuelve exactamente {group} y la diferencia entre máximo y mínimo de {n}, una fila por cada {group} en {table}.',f'SELECT {group}, MAX({n}) - MIN({n}) AS rango FROM {table} GROUP BY {group}','media','dispersion')
                add(f'Devuelve exactamente {group} y la desviación estándar poblacional de {n}, una fila por cada {group} en {table}.',f'SELECT {group}, STDDEV_POP({n}) AS desviacion FROM {table} GROUP BY {group}','dificil','dispersion')
        for a,b in combinations(numeric,2):
            for op,label in [('>','supera'),('<','es menor que')]:
                add(f'Lista id, {a} y {b} de {table} donde {a} {label} {b}.',f'SELECT id, {a}, {b} FROM {table} WHERE {a} {op} {b}','media','comparacion')
        for fk,typ in cols:
            if fk.endswith('_id'):
                parent=RELATIONS[fk[:-3]]
                add(f'Devuelve exactamente {fk} y la cantidad de registros de {table} por {fk}, incluyendo solo grupos con más de un registro.',f'SELECT {fk}, COUNT(*) AS cantidad FROM {table} GROUP BY {fk} HAVING COUNT(*) > 1','media','having')
                add(f'Muestra los id de {parent} sin registros relacionados en {table}.',f'SELECT p.id FROM {parent} p WHERE NOT EXISTS (SELECT 1 FROM {table} t WHERE t.{fk} = p.id)','dificil','subconsulta')
                add(f'Lista los id de {table} junto con los id relacionados de {parent}.',f'SELECT t.id, p.id AS relacionado_id FROM {table} t JOIN {parent} p ON t.{fk} = p.id','media','join')
                for n in numeric:
                    for fn,word in [('SUM','suma'),('AVG','promedio'),('MAX','máximo'),('MIN','mínimo')]:
                        add(f'Devuelve exactamente {fk} y el {word} de {n} de {table}, una fila por cada {fk}.',f'SELECT {fk}, {fn}({n}) AS valor FROM {table} GROUP BY {fk}','media','group_by')
                        add(f'Devuelve exactamente el id de {parent} y el {word} de {n} de sus registros relacionados en {table}; incluye todos los id de {parent}, con agregado NULL si no tienen registros.',f'SELECT p.id, {fn}(t.{n}) AS valor FROM {parent} p LEFT JOIN {table} t ON t.{fk} = p.id GROUP BY p.id','dificil','join_agregacion')
                    add(f'Devuelve exactamente id, {fk} y una posición consecutiva por registro dentro de cada {fk} en {table}, ordenando para calcularla por {n} descendente y, en empates, id ascendente.',f'SELECT id, {fk}, ROW_NUMBER() OVER (PARTITION BY {fk} ORDER BY {n} DESC, id) AS posicion FROM {table}','dificil','ventana')
            if typ=='DATE':
                add(f'Devuelve exactamente año, mes y cantidad de registros de {table}, agrupados por año y mes de {fk}.',f'SELECT YEAR({fk}) AS anio, MONTH({fk}) AS mes, COUNT(*) AS cantidad FROM {table} GROUP BY YEAR({fk}), MONTH({fk})','media','fecha')
                for month in range(1,13):
                    add(f'Lista todas las columnas de los registros de {table} cuya {fk} corresponde a {month:02d}/2025, en el orden de columnas del esquema.',f"SELECT * FROM {table} WHERE {fk} >= '2025-{month:02d}-01' AND {fk} < DATE_ADD('2025-{month:02d}-01', INTERVAL 1 MONTH)",'facil','fecha')
    # Literal-only variants are not separate training examples.
    import re
    unique=[];seen=set()
    for row in rows:
        key=re.sub(r"'[^']*'|\b\d+\b",'?',row['sql'])
        if key not in seen:
            row['id']=f'{schema_id}-{len(unique)+1:05d}'
            unique.append(row);seen.add(key)
    return unique

def write_jsonl(path,rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('w',encoding='utf-8') as f:
        for row in rows: f.write(json.dumps(row,ensure_ascii=False)+'\n')

def generate(root=Path('.')):
    root=Path(root); train=[]; validation=[]
    for idx,schema_id in enumerate(DOMAINS):
        folder=root/'datos/esquemas'/schema_id; folder.mkdir(parents=True,exist_ok=True)
        (folder/'schema.sql').write_text(schema_sql(schema_id)+'\n',encoding='utf-8')
        (folder/'seed.sql').write_text(fixtures(schema_id)+'\n',encoding='utf-8')
        (train if idx<10 else validation).extend(candidates(schema_id))
    write_jsonl(root/'datos/entrenamiento/candidatos.jsonl',train)
    write_jsonl(root/'datos/validacion/propuestas_revision_humana.jsonl',validation)
    write_jsonl(root/'datos/entrenamiento/aceptados.jsonl',[])
    write_jsonl(root/'datos/validacion/aceptados.jsonl',[])
    write_jsonl(root/'datos/descartes/descartes.jsonl',[])
    stats={'propuestos_entrenamiento':len(train),'propuestos_validacion':len(validation),'aceptados':0,'descartados':0,'estado':'pendiente de ejecución MySQL 8.4.10 y revisión semántica humana','por_esquema':{k:len(candidates(k)) for k in DOMAINS}}
    (root/'datos/fuentes/estadisticas.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    return stats
