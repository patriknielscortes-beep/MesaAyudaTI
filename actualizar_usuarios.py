import sqlite3
from werkzeug.security import generate_password_hash

conexion = sqlite3.connect("mesaayuda.db")
cursor = conexion.cursor()

cursor.execute(
    """
    UPDATE usuarios
    SET password=?
    WHERE usuario='admin'
    """,
    (generate_password_hash("admin1234"),)
)

cursor.execute(
    """
    UPDATE usuarios
    SET password=?
    WHERE usuario='tecnico1'
    """,
    (generate_password_hash("tecnico1234"),)
)

cursor.execute(
    """
    UPDATE usuarios
    SET password=?
    WHERE usuario='usuario1'
    """,
    (generate_password_hash("usuario1234"),)
)

conexion.commit()
conexion.close()

print("Usuarios actualizados correctamente")