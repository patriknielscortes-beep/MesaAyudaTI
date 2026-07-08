import sqlite3

conexion = sqlite3.connect("mesaayuda.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA table_info(tickets)")

for columna in cursor.fetchall():
    print(columna)

conexion.close()

conexion = sqlite3.connect("mesaayuda.db")
cursor = conexion.cursor()

try:

    cursor.execute("""
        ALTER TABLE tickets
        ADD COLUMN categoria TEXT DEFAULT 'Software'
    """)

    conexion.commit()

    print("Columna categoria agregada correctamente")

except Exception as e:

    print("Error:", e)


conexion.close()