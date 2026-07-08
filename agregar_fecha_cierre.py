import sqlite3

conexion = sqlite3.connect("mesaayuda.db")
cursor = conexion.cursor()

try:
    cursor.execute(
        "ALTER TABLE tickets ADD COLUMN fecha_cierre TEXT"
    )

    conexion.commit()
    print("Columna fecha_cierre agregada correctamente")

except Exception as e:
    print("Error:", e)

conexion.close()