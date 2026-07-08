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

conexion.commit()
conexion.close()

print("Contraseña admin actualizada correctamente")