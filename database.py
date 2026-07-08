import sqlite3
from werkzeug.security import generate_password_hash


conexion = sqlite3.connect("mesaayuda.db")
cursor = conexion.cursor()



# ==========================
# TABLA USUARIOS
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    rol TEXT NOT NULL
)
""")




# ==========================
# TABLA TICKETS
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    categoria TEXT,
    prioridad TEXT NOT NULL,
    estado TEXT NOT NULL,
    fecha TEXT NOT NULL,
    imagen TEXT,
    tecnico TEXT,
    usuario TEXT,
    fecha_cierre TEXT
)
""")



# Agregar categoria si la base antigua no la tiene

cursor.execute("""
PRAGMA table_info(tickets)
""")

columnas = [columna[1] for columna in cursor.fetchall()]


if "categoria" not in columnas:

    cursor.execute("""
    ALTER TABLE tickets
    ADD COLUMN categoria TEXT
    """)

    print("Columna categoria agregada")





# ==========================
# TABLA HISTORIAL
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS historial(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    tecnico TEXT NOT NULL,
    comentario TEXT NOT NULL,
    fecha TEXT NOT NULL
)
""")





# ==========================
# TABLA AUDITORIA
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS auditoria(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    accion TEXT,
    fecha TEXT
)
""")





# ==========================
# TABLA NOTIFICACIONES
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS notificaciones(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    mensaje TEXT NOT NULL,
    leida INTEGER DEFAULT 0,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP
)
""")





# ==========================
# TABLA SATISFACCION
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS satisfaccion(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,
    usuario TEXT,
    calificacion INTEGER,
    comentario TEXT,
    fecha TEXT
)
""")


# Agregar fecha si la tabla ya existía sin esa columna

cursor.execute("""
PRAGMA table_info(satisfaccion)
""")

columnas = [columna[1] for columna in cursor.fetchall()]


if "fecha" not in columnas:

    cursor.execute("""
    ALTER TABLE satisfaccion
    ADD COLUMN fecha TEXT
    """)

    print("Columna fecha agregada a satisfaccion")






# ==========================
# USUARIOS INICIALES
# ==========================


cursor.execute("""
INSERT OR IGNORE INTO usuarios(usuario,password,rol)
VALUES (?,?,?)
""",
(
    "admin",
    generate_password_hash("admin1234"),
    "admin"
))



cursor.execute("""
INSERT OR IGNORE INTO usuarios(usuario,password,rol)
VALUES (?,?,?)
""",
(
    "tecnico1",
    generate_password_hash("tecnico1234"),
    "tecnico"
))



cursor.execute("""
INSERT OR IGNORE INTO usuarios(usuario,password,rol)
VALUES (?,?,?)
""",
(
    "usuario1",
    generate_password_hash("usuario1234"),
    "usuario"
))





# ==========================
# CALCULO TIEMPO PROMEDIO
# ==========================

cursor.execute("""
SELECT fecha, fecha_cierre
FROM tickets
WHERE estado='Cerrado'
AND fecha_cierre IS NOT NULL
""")

tickets_cerrados = cursor.fetchall()



from datetime import datetime


total_horas = 0
cantidad = 0



for ticket in tickets_cerrados:

    try:

        fecha_inicio = datetime.strptime(
            ticket[0],
            "%d-%m-%Y %H:%M"
        )


        fecha_fin = datetime.strptime(
            ticket[1],
            "%d-%m-%Y %H:%M"
        )


        diferencia = fecha_fin - fecha_inicio


        total_horas += diferencia.total_seconds() / 3600

        cantidad += 1


    except:

        pass




if cantidad > 0:

    promedio_horas = round(
        total_horas / cantidad,
        1
    )

else:

    promedio_horas = 0


cursor.execute("""
PRAGMA table_info(satisfaccion)
""")

columnas = [columna[1] for columna in cursor.fetchall()]


if "usuario" not in columnas:

    cursor.execute("""
    ALTER TABLE satisfaccion
    ADD COLUMN usuario TEXT
    """)

    print("Columna usuario agregada a satisfaccion")


if "fecha" not in columnas:

    cursor.execute("""
    ALTER TABLE satisfaccion
    ADD COLUMN fecha TEXT
    """)

    print("Columna fecha agregada a satisfaccion")




conexion.commit()

conexion.close()



print("Base de datos creada y actualizada correctamente")