from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from flask import flash
from flask import send_file
from werkzeug.security import generate_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO
from flask import Flask, render_template
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os
from datetime import datetime
import os
import pandas as pd
from datetime import datetime
import sqlite3

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "MesaAyudaTI2026"

def registrar_auditoria(usuario, accion):

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    fecha = datetime.now().strftime("%d-%m-%Y %H:%M")

    cursor.execute("""
    INSERT INTO auditoria(usuario, accion, fecha)
    VALUES (?, ?, ?)
    """, (usuario, accion, fecha))

    conexion.commit()
    conexion.close()
  

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        conexion = sqlite3.connect("mesaayuda.db")
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario=?",
            (usuario,)
        )

        resultado = cursor.fetchone()
        print(resultado)

        conexion.close()

        if resultado and check_password_hash(
            resultado[2],
            password
        ):

            session["usuario"] = resultado[1]
            session["rol"] = resultado[3]

            if session["rol"] == "admin":
                return redirect("/dashboard_admin")

            elif session["rol"] == "tecnico":
                return redirect("/dashboard_tecnico")

            else:
                return redirect("/dashboard_usuario")

        return "<h1>Usuario o contraseña incorrectos</h1>"

    return render_template("login.html")

@app.route("/perfil")
def perfil():

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT usuario, rol, foto
        FROM usuarios
        WHERE usuario = ?
    """, (session["usuario"],))

    usuario = cursor.fetchone()
    conexion.close()

    return render_template("perfil.html", usuario=usuario)


@app.route("/subir_foto", methods=["POST"])
def subir_foto():

    if "usuario" not in session:
        return redirect("/")

    file = request.files["foto"]

    if file.filename == "":
        return redirect("/perfil")

    filename = secure_filename(file.filename)

    ruta = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(ruta)

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET foto = ?
        WHERE usuario = ?
    """, (filename, session["usuario"]))

    conexion.commit()
    conexion.close()

    return redirect("/perfil")

@app.route("/cambiar_password", methods=["GET", "POST"])
def cambiar_password():

    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":

        password_actual = request.form["password_actual"]
        password_nueva = request.form["password_nueva"]

        conexion = sqlite3.connect("mesaayuda.db")
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT password FROM usuarios
            WHERE usuario=?
        """, (session["usuario"],))

        user = cursor.fetchone()

        if user and user[0] == password_actual:

            cursor.execute("""
                UPDATE usuarios
                SET password=?
                WHERE usuario=?
            """, (password_nueva, session["usuario"]))

            conexion.commit()
            conexion.close()

            flash("Contraseña actualizada", "success")
            return redirect("/dashboard_usuario")

        conexion.close()
        flash("Contraseña incorrecta", "danger")
        return redirect("/cambiar_password")

    return render_template("cambiar_password.html")

@app.route("/crear_ticket", methods=["GET", "POST"])
def crear_ticket():

    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":

        titulo = request.form["titulo"]
        descripcion = request.form["descripcion"]
        categoria = request.form["categoria"]   # <-- AGREGAR
        prioridad = request.form["prioridad"]
        tecnico = request.form["tecnico"]
        usuario = session["usuario"]

        imagen = request.files.get("imagen")

        nombre_imagen = ""

        if imagen and imagen.filename != "":

            nombre_imagen = secure_filename(imagen.filename)

            imagen.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nombre_imagen
                )
            )


        fecha = datetime.now().strftime("%d-%m-%Y %H:%M")


        conexion = sqlite3.connect("mesaayuda.db")
        cursor = conexion.cursor()


        cursor.execute(
            """
            INSERT INTO tickets
            (
                titulo,
                descripcion,
                categoria,
                prioridad,
                estado,
                fecha,
                imagen,
                tecnico,
                usuario,
                fecha_cierre
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                titulo,
                descripcion,
                categoria,
                prioridad,
                "Abierto",
                fecha,
                nombre_imagen,
                tecnico,
                usuario,
                None
            )
        )


        conexion.commit()
        conexion.close()


        registrar_auditoria(
            session["usuario"],
            f"Creó el ticket: {titulo}"
        )


        flash(
            "Ticket creado correctamente",
            "success"
        )


        return redirect("/ver_tickets")


    return render_template("crear_ticket.html")

@app.route("/cambiar_estado/<int:id>")
def cambiar_estado(id):

    if "usuario" not in session:
        return redirect("/")


    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()


    # Obtener información del ticket

    cursor.execute(
        """
        SELECT estado, usuario
        FROM tickets
        WHERE id=?
        """,
        (id,)
    )

    resultado = cursor.fetchone()


    if resultado is None:

        flash("El ticket no existe", "danger")

        conexion.close()

        return redirect("/ver_tickets")



    estado_actual = resultado[0]
    usuario_ticket = resultado[1]



    if estado_actual == "Abierto":


        nuevo_estado = "En Proceso"


        cursor.execute(
            """
            UPDATE tickets
            SET estado=?
            WHERE id=?
            """,
            (
                nuevo_estado,
                id
            )
        )



    elif estado_actual == "En Proceso":


        nuevo_estado = "Cerrado"


        fecha_cierre = datetime.now().strftime("%d-%m-%Y %H:%M")


        cursor.execute(
            """
            UPDATE tickets
            SET estado=?,
                fecha_cierre=?
            WHERE id=?
            """,
            (
                nuevo_estado,
                fecha_cierre,
                id
            )
        )



    else:


        nuevo_estado = estado_actual




    # Crear notificación para el usuario dueño del ticket

    if usuario_ticket:


        cursor.execute(
            """
            INSERT INTO notificaciones(usuario, mensaje, leida)
            VALUES (?, ?, 0)
            """,
            (
                usuario_ticket,
                f"Tu ticket #{id} cambió a estado {nuevo_estado}"
            )
        )



    conexion.commit()

    conexion.close()



    # Auditoría

    registrar_auditoria(
        session["usuario"],
        f"Cambió ticket #{id} a {nuevo_estado}"
    )



    return redirect("/ver_tickets")

@app.route("/ver_tickets")
def ver_tickets():

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    rol = session["rol"]
    usuario = session["usuario"]

    buscar = request.args.get("buscar", "")
    tecnico = request.args.get("tecnico","")
    usuario_filtro = request.args.get("usuario","")
    estado = request.args.get("estado", "")
    prioridad = request.args.get("prioridad", "")
    categoria = request.args.get("categoria", "")

    if rol == "admin":

        consulta = """
        SELECT * FROM tickets
        WHERE (titulo LIKE ? OR descripcion LIKE ?)
        """
        if categoria:
          consulta += " AND categoria=?"
          parametros.append(categoria)

        parametros = [
            f"%{buscar}%",
            f"%{buscar}%"
        ]

        if estado:
            consulta += " AND estado=?"
            parametros.append(estado)

        if prioridad:
            consulta += " AND prioridad=?"
            parametros.append(prioridad)

        if tecnico:
            consulta += " AND tecnico=?"
            parametros.append(tecnico)

        if usuario_filtro:
            consulta += " AND usuario=?"
            parametros.append(usuario_filtro)

        cursor.execute(consulta, parametros)

    elif rol == "tecnico":

        cursor.execute(
            """
            SELECT * FROM tickets
            WHERE tecnico=?
            """,
            (usuario,)
        )

    else:

        cursor.execute(
            """
            SELECT * FROM tickets
            WHERE usuario=?
            """,
            (usuario,)
        )

    tickets = cursor.fetchall()

    conexion.close()

    return render_template(
        "ver_tickets.html",
        tickets=tickets,
        buscar=buscar,
        estado=estado,
        prioridad=prioridad,
        categoria=categoria
    )

@app.route("/estadisticas")
def estadisticas():

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE estado='Abierto'"
    )
    abiertos = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE estado='En Proceso'"
    )
    proceso = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tickets WHERE estado='Cerrado'"
    )
    cerrados = cursor.fetchone()[0]

    conexion.close()

    return render_template(
        "estadisticas.html",
        abiertos=abiertos,
        proceso=proceso,
        cerrados=cerrados
    )

@app.route("/dashboard")
def dashboard():

    if "usuario" not in session:
        return redirect("/")

    return render_template(
        "dashboard.html",
        usuario=session["usuario"],
        rol=session["rol"]
    )

@app.route("/eliminar_ticket/<int:id>")
def eliminar_ticket(id):

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM tickets WHERE id=?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect("/ver_tickets")

@app.route("/editar_ticket/<int:id>", methods=["GET", "POST"])
def editar_ticket(id):

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        titulo = request.form["titulo"]
        descripcion = request.form["descripcion"]
        prioridad = request.form["prioridad"]

        cursor.execute(
            """
            UPDATE tickets
            SET titulo=?,
                descripcion=?,
                prioridad=?
            WHERE id=?
            """,
            (titulo, descripcion, prioridad, id)
        )

        conexion.commit()
        conexion.close()

        return redirect("/ver_tickets")

    cursor.execute(
        "SELECT * FROM tickets WHERE id=?",
        (id,)
    )

    ticket = cursor.fetchone()

    conexion.close()

    return render_template(
        "editar_ticket.html",
        ticket=ticket
    )

@app.route("/exportar_excel")
def exportar_excel():

    if "usuario" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "<h1>No autorizado</h1>"

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM tickets")

    tickets = cursor.fetchall()

    conexion.close()

    wb = Workbook()

    ws = wb.active

    ws.title = "Tickets"

    ws.append([
        "ID",
        "Titulo",
        "Descripcion",
        "Prioridad",
        "Estado",
        "Fecha",
        "Imagen",
        "Tecnico",
        "Usuario"
    ])

    for ticket in tickets:
        ws.append(ticket)

    archivo = "tickets.xlsx"

    wb.save(archivo)

    return send_file(
        archivo,
        as_attachment=True
    )

@app.route("/dashboard_admin")
def dashboard_admin():

    if "usuario" not in session:
        return redirect("/")


    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()


    cursor.execute("SELECT COUNT(*) FROM tickets")
    total = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE estado='Abierto'
    """)
    abiertos = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE estado='En Proceso'
    """)
    proceso = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE estado='Cerrado'
    """)
    cerrados = cursor.fetchone()[0]



    cursor.execute("""
        SELECT id, titulo, estado, prioridad
        FROM tickets
        ORDER BY id DESC
        LIMIT 5
    """)
    ultimos_tickets = cursor.fetchall()



    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE prioridad='Alta'
        AND estado!='Cerrado'
    """)
    tickets_urgentes = cursor.fetchone()[0]



    cursor.execute("""
        SELECT tecnico, COUNT(*) as total
        FROM tickets
        WHERE estado='Cerrado'
        AND tecnico IS NOT NULL
        AND tecnico != ''
        GROUP BY tecnico
        ORDER BY total DESC
    """)
    ranking_tecnicos = cursor.fetchall()



    # NUEVO: Tickets por prioridad

    cursor.execute("""
        SELECT prioridad, COUNT(*)
        FROM tickets
        GROUP BY prioridad
    """)
    tickets_prioridad = cursor.fetchall()



    # NUEVO: Tickets por estado

    cursor.execute("""
        SELECT estado, COUNT(*)
        FROM tickets
        GROUP BY estado
    """)
    tickets_estado = cursor.fetchall()

    # Tickets por categoría
    cursor.execute("""
    SELECT categoria, COUNT(*)
    FROM tickets
    GROUP BY categoria
    ORDER BY COUNT(*) DESC
    """)

    tickets_categoria = cursor.fetchall()

    
    # Tiempo promedio de resolución

    cursor.execute("""
        SELECT fecha, fecha_cierre
        FROM tickets
        WHERE estado='Cerrado'
        AND fecha_cierre IS NOT NULL
        """)    

    tickets_cerrados = cursor.fetchall()

    total_horas = 0
    cantidad = 0

    for ticket in tickets_cerrados:

        try:

            fecha_inicio = datetime.strptime(ticket[0], "%d-%m-%Y %H:%M")
            fecha_fin = datetime.strptime(ticket[1], "%d-%m-%Y %H:%M")

            diferencia = fecha_fin - fecha_inicio

            total_horas += diferencia.total_seconds() / 3600

            cantidad += 1

        except:
            pass

    if cantidad > 0:

        promedio_horas = round(total_horas / cantidad, 1)

    else:

        promedio_horas = 0

    # Promedio de satisfacción

    cursor.execute("""
        SELECT AVG(calificacion)
        FROM satisfaccion
    """)

    resultado_satisfaccion = cursor.fetchone()[0]


    if resultado_satisfaccion:

        promedio_satisfaccion = round(resultado_satisfaccion, 1)

    else:

        promedio_satisfaccion = 0


    # Satisfacción por mes

    cursor.execute("""
        SELECT 
            substr(fecha, 4, 7) AS mes,
            AVG(calificacion)
        FROM satisfaccion
        GROUP BY mes
        ORDER BY mes
    """)

    satisfaccion_mensual = cursor.fetchall()

        # TICKETS POR ESTADO
    cursor.execute("""
        SELECT estado, COUNT(*)
        FROM tickets
        GROUP BY estado
    """)

    tickets_estado = cursor.fetchall()



    # TICKETS POR PRIORIDAD
    cursor.execute("""
        SELECT prioridad, COUNT(*)
        FROM tickets
        GROUP BY prioridad
    """)

    tickets_prioridad = cursor.fetchall()



    # TICKETS POR CATEGORIA
    cursor.execute("""
        SELECT categoria, COUNT(*)
        FROM tickets
        GROUP BY categoria
    """)

    tickets_categoria = cursor.fetchall()

    print("ESTADOS:", tickets_estado)
    print("PRIORIDAD:", tickets_prioridad)
    print("CATEGORIA:", tickets_categoria)


    conexion.close()



    return render_template(
    "dashboard_admin.html",
    total=total,
    abiertos=abiertos,
    proceso=proceso,
    cerrados=cerrados,
    tickets_urgentes=tickets_urgentes,
    ultimos_tickets=ultimos_tickets,
    ranking_tecnicos=ranking_tecnicos,
    tickets_estado=tickets_estado,
    tickets_prioridad=tickets_prioridad,
    tickets_categoria=tickets_categoria,
    promedio_horas=promedio_horas,
    promedio_satisfaccion=promedio_satisfaccion,
    satisfaccion_mensual=satisfaccion_mensual
    )

@app.route("/dashboard_tecnico")
def dashboard_tecnico():

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM tickets
    WHERE tecnico=?
    AND estado='Cerrado'
    """, (session["usuario"],))

    tickets_cerrados = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM tickets
    WHERE tecnico=?
    AND estado!='Cerrado'
    """, (session["usuario"],))

    tickets_asignados = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
        WHERE tecnico=?
        AND prioridad='Alta'
        AND estado!='Cerrado'
        """, (session["usuario"],))

    tickets_urgentes = cursor.fetchone()[0]

    conexion.close()

    return render_template(
        "dashboard_tecnico.html",
        usuario=session["usuario"],
        tickets_asignados=tickets_asignados,
        tickets_cerrados=tickets_cerrados,
        tickets_urgentes=tickets_urgentes
    )


@app.route("/dashboard_usuario")
def dashboard_usuario():

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    usuario = session["usuario"]

    cursor.execute("""
    SELECT COUNT(*)
    FROM tickets
    WHERE usuario=?
    """, (usuario,))
    tickets_totales = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM tickets
    WHERE usuario=?
    AND estado='Abierto'
    """, (usuario,))
    tickets_abiertos = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM tickets
    WHERE usuario=?
    AND estado='Cerrado'
    """, (usuario,))

    tickets_cerrados = cursor.fetchone()[0]


    cursor.execute("""
    SELECT id, titulo, estado, fecha
    FROM tickets
    WHERE usuario=?
    ORDER BY id DESC
    LIMIT 5
    """, (usuario,))

    ultimos_tickets = cursor.fetchall()

    conexion.close()

    return render_template(
    "dashboard_usuario.html",
    usuario=usuario,
    tickets_totales=tickets_totales,
    tickets_abiertos=tickets_abiertos,
    tickets_cerrados=tickets_cerrados,
    ultimos_tickets=ultimos_tickets
    )

@app.route("/asignar_tecnico/<int:id>", methods=["GET", "POST"])
def asignar_tecnico(id):

    if "usuario" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "<h1>No autorizado</h1>"

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        tecnico = request.form["tecnico"]


        # Asignar técnico al ticket

        cursor.execute(
            """
            UPDATE tickets
            SET tecnico=?
            WHERE id=?
            """,
            (tecnico, id)
        )


        # Crear notificación para el técnico

        cursor.execute(
            """
            INSERT INTO notificaciones(usuario, mensaje, leida)
            VALUES (?, ?, 0)
            """,
            (
                tecnico,
                f"Se te asignó el ticket #{id}"
            )
        )


        # Registrar auditoría

        fecha = datetime.now().strftime("%d-%m-%Y %H:%M")

        cursor.execute(
            """
            INSERT INTO auditoria(usuario, accion, fecha)
            VALUES (?, ?, ?)
            """,
            (
                session["usuario"],
                f"Asignó ticket #{id} al técnico {tecnico}",
                fecha
            )
        )


        conexion.commit()
        conexion.close()

        return redirect("/ver_tickets")



    cursor.execute(
        "SELECT * FROM tickets WHERE id=?",
        (id,)
    )

    ticket = cursor.fetchone()



    cursor.execute(
        """
        SELECT usuario
        FROM usuarios
        WHERE rol='tecnico'
        """
    )

    tecnicos = cursor.fetchall()


    conexion.close()


    return render_template(
        "asignar_tecnico.html",
        ticket=ticket,
        tecnicos=tecnicos
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route("/historial/<int:id>", methods=["GET", "POST"])
def historial(id):

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        comentario = request.form["comentario"]
        fecha = datetime.now().strftime("%d-%m-%Y %H:%M")

        cursor.execute(
            """
            INSERT INTO historial
            (ticket_id, tecnico, comentario, fecha)
            VALUES (?, ?, ?, ?)
            """,
            (
                id,
                session["usuario"],
                comentario,
                fecha
            )
        )

        conexion.commit()

    cursor.execute(
        """
        SELECT tecnico, comentario, fecha
        FROM historial
        WHERE ticket_id=?
        ORDER BY id DESC
        """,
        (id,)
    )

    comentarios = cursor.fetchall()

    conexion.close()

    return render_template(
        "historial.html",
        ticket_id=id,
        comentarios=comentarios
    )

@app.route("/usuarios")
def usuarios():

    if "usuario" not in session:
        return redirect("/")


    if session["rol"] != "admin":
        return "<h1>No autorizado</h1>"



    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()



    buscar = request.args.get("buscar", "")

    rol_filtro = request.args.get("rol", "")



    consulta = """
        SELECT id, usuario, rol
        FROM usuarios
        WHERE usuario LIKE ?
    """



    parametros = [
        f"%{buscar}%"
    ]



    if rol_filtro:

        consulta += """
        AND rol=?
        """

        parametros.append(rol_filtro)



    cursor.execute(
        consulta,
        parametros
    )



    usuarios = cursor.fetchall()



    total_usuarios = len(usuarios)



    conexion.close()



    return render_template(
        "usuarios.html",
        usuarios=usuarios,
        buscar=buscar,
        rol_filtro=rol_filtro,
        total_usuarios=total_usuarios
    )


@app.route("/crear_usuario", methods=["GET", "POST"])
def crear_usuario():

    if "usuario" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "<h1>No autorizado</h1>"

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = generate_password_hash(
        request.form["password"]
        )
        rol = request.form["rol"]

        conexion = sqlite3.connect("mesaayuda.db")
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO usuarios(usuario,password,rol)
            VALUES(?,?,?)
            """,
            (usuario, password, rol)
        )

        conexion.commit()
        registrar_auditoria(
        session["usuario"],
        f"Creó el usuario: {usuario}"
)
        conexion.close()

        return redirect("/usuarios")

    return render_template("crear_usuario.html")

@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):

        if "usuario" not in session:
            return redirect("/")

        if session["rol"] != "admin":
            return "<h1>No autorizado</h1>"

        conexion = sqlite3.connect("mesaayuda.db")
        cursor = conexion.cursor()

        cursor.execute(
        """
        DELETE FROM usuarios
        WHERE id=?
        """,
        (id,)
    )

        conexion.commit()
        conexion.close()

        return redirect("/usuarios")


@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):

    if "usuario" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "<h1>No autorizado</h1>"

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        nombre_usuario = request.form["usuario"]
        password = request.form["password"]
        rol = request.form["rol"]

        if password.strip() == "":

            cursor.execute("""
                UPDATE usuarios
                SET usuario=?, rol=?
                WHERE id=?
            """, (
                nombre_usuario,
                rol,
                id
            ))

        else:

            password_hash = generate_password_hash(password)

            cursor.execute("""
                UPDATE usuarios
                SET usuario=?, password=?, rol=?
                WHERE id=?
            """, (
                nombre_usuario,
                password_hash,
                rol,
                id
            ))

        conexion.commit()

        registrar_auditoria(
            session["usuario"],
            f"Editó el usuario {nombre_usuario}"
        )

        conexion.close()

        flash("Usuario actualizado correctamente.", "success")

        return redirect("/usuarios")

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE id=?
    """, (id,))

    usuario = cursor.fetchone()

    conexion.close()

    return render_template(
        "editar_usuario.html",
        usuario=usuario
    )

@app.route("/grafico")
def grafico():

    if session["rol"] != "admin":
        return "No autorizado"

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT estado, COUNT(*)
    FROM tickets
    GROUP BY estado
    """)

    datos = cursor.fetchall()

    conexion.close()

    estados = [x[0] for x in datos]
    cantidades = [x[1] for x in datos]

    import matplotlib.pyplot as plt

    plt.figure(figsize=(6,4))
    plt.bar(estados, cantidades)

    plt.title("Tickets por Estado")

    plt.savefig("static/grafico.png")

    return render_template("grafico.html")

@app.route("/exportar_pdf")
def exportar_pdf():

    if session["rol"] != "admin":
        return "No autorizado"

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM tickets")

    tickets = cursor.fetchall()

    conexion.close()

    archivo = "tickets.pdf"

    pdf = canvas.Canvas(archivo)

    y = 800

    pdf.drawString(50, y, "REPORTE DE TICKETS")

    y -= 40

    for ticket in tickets:

        pdf.drawString(
            50,
            y,
            f"ID:{ticket[0]} - {ticket[1]} - {ticket[4]}"
        )

        y -= 20

        if y < 50:
            pdf.showPage()
            y = 800

    pdf.save()

    return send_file(
        archivo,
        as_attachment=True
    )

@app.route("/pdf_ticket/<int:id>")
def pdf_ticket(id):

    if "usuario" not in session:
        return redirect("/")

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT id,
           titulo,
           descripcion,
           prioridad,
           estado,
           fecha,
           tecnico,
           usuario,
           fecha_cierre
    FROM tickets
    WHERE id=?
    """, (id,))

    ticket = cursor.fetchone()

    conexion.close()

    nombre_pdf = f"ticket_{id}.pdf"

    doc = SimpleDocTemplate(nombre_pdf)

    estilos = getSampleStyleSheet()

    elementos = []

    elementos.append(
        Paragraph(f"<b>Ticket #{ticket[0]}</b>", estilos["Title"])
    )

    elementos.append(Spacer(1, 12))

    elementos.append(
        Paragraph(f"Título: {ticket[1]}", estilos["Normal"])
    )

    elementos.append(
        Paragraph(f"Descripción: {ticket[2]}", estilos["Normal"])
    )

    elementos.append(
        Paragraph(f"Prioridad: {ticket[3]}", estilos["Normal"])
    )

    elementos.append(
        Paragraph(f"Estado: {ticket[4]}", estilos["Normal"])
    )

    elementos.append(
        Paragraph(f"Fecha Creación: {ticket[5]}", estilos["Normal"])
    )

    elementos.append(
        Paragraph(f"Técnico: {ticket[6]}", estilos["Normal"])
    )

    elementos.append(
        Paragraph(f"Usuario: {ticket[7]}", estilos["Normal"])
    )

    elementos.append(
        Paragraph(f"Fecha Cierre: {ticket[8]}", estilos["Normal"])
    )

    doc.build(elementos)

    return send_file(
        nombre_pdf,
        as_attachment=True
    )

@app.route("/ver_ticket/<int:id>", methods=["GET", "POST"])
def ver_ticket(id):

    if "usuario" not in session:
        return redirect("/")


    conexion = sqlite3.connect("mesaayuda.db", timeout=10)
    cursor = conexion.cursor()


    if request.method == "POST":


        comentario = request.form["comentario"]

        fecha = datetime.now().strftime("%d-%m-%Y %H:%M")



        # Guardar comentario

        cursor.execute(
            """
            INSERT INTO historial(ticket_id, tecnico, comentario, fecha)
            VALUES (?, ?, ?, ?)
            """,
            (
                id,
                session["usuario"],
                comentario,
                fecha
            )
        )



        # Obtener dueño y técnico del ticket

        cursor.execute(
            """
            SELECT usuario, tecnico
            FROM tickets
            WHERE id=?
            """,
            (id,)
        )


        ticket_info = cursor.fetchone()



        usuario_ticket = ticket_info[0]
        tecnico_ticket = ticket_info[1]



        # Si responde el usuario, avisar al técnico

        if session["usuario"] == usuario_ticket and tecnico_ticket:


            cursor.execute(
                """
                INSERT INTO notificaciones(usuario, mensaje, leida)
                VALUES (?, ?, 0)
                """,
                (
                    tecnico_ticket,
                    f"El usuario {session['usuario']} respondió el ticket #{id}"
                )
            )



        # Si responde el técnico, avisar al usuario

        elif session["usuario"] == tecnico_ticket:


            cursor.execute(
                """
                INSERT INTO notificaciones(usuario, mensaje, leida)
                VALUES (?, ?, 0)
                """,
                (
                    usuario_ticket,
                    f"El técnico {session['usuario']} respondió tu ticket #{id}"
                )
            )



        # Guardar cambios antes de abrir otra conexión

        conexion.commit()


        # Auditoría

        registrar_auditoria(
            session["usuario"],
            f"Respondió el ticket #{id}"
    )

    conexion.commit()

    # Información del ticket

    cursor.execute(
        """
        SELECT *
        FROM tickets
        WHERE id=?
        """,
        (id,)
    )


    ticket = cursor.fetchone()



    # Historial del chat

    cursor.execute(
        """
        SELECT tecnico, comentario, fecha
        FROM historial
        WHERE ticket_id=?
        ORDER BY id DESC
        """,
        (id,)
    )


    comentarios = cursor.fetchall()

    conexion.close()



    return render_template(
        "ver_ticket.html",
        ticket=ticket,
        comentarios=comentarios
    )




@app.route("/satisfaccion/<int:id>", methods=["GET", "POST"])
def satisfaccion(id):

    if "usuario" not in session:
        return redirect("/")


    if request.method == "POST":

        calificacion = request.form["calificacion"]
        comentario = request.form["comentario"]


        conexion = sqlite3.connect("mesaayuda.db")
        cursor = conexion.cursor()


        cursor.execute("""
        INSERT INTO satisfaccion
        (ticket_id, usuario, calificacion, comentario, fecha)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            id,
            session["usuario"],
            calificacion,
            comentario,
            datetime.now().strftime("%d-%m-%Y")
        ))


        conexion.commit()
        conexion.close()


        flash(
            "Gracias por evaluar el servicio",
            "success"
        )


        return redirect("/dashboard_usuario")


    return render_template(
        "satisfaccion.html",
        id=id
    )


@app.route("/auditoria")
def auditoria():

    if "usuario" not in session:
        return redirect("/")


    if session["rol"] != "admin":
        return "<h1>No autorizado</h1>"


    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()


    buscar = request.args.get("buscar", "")


    cursor.execute("""
        SELECT usuario, accion, fecha
        FROM auditoria
        WHERE usuario LIKE ?
        OR accion LIKE ?
        ORDER BY id DESC
    """,
    (
        f"%{buscar}%",
        f"%{buscar}%"
    ))


    registros = cursor.fetchall()


    total_registros = len(registros)


    conexion.close()


    return render_template(
        "auditoria.html",
        registros=registros,
        buscar=buscar,
        total_registros=total_registros
    )

@app.route("/exportar_auditoria_pdf")
def exportar_auditoria_pdf():

    if "usuario" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "<h1>No autorizado</h1>"


    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()


    cursor.execute("""
        SELECT usuario, accion, fecha
        FROM auditoria
        ORDER BY id DESC
        LIMIT 100
    """)


    registros = cursor.fetchall()

    conexion.close()


    nombre_archivo = "auditoria_" + datetime.now().strftime("%d-%m-%Y") + ".pdf"


    ruta = os.path.join(
        "static",
        nombre_archivo
    )


    documento = SimpleDocTemplate(ruta)


    elementos = []


    estilos = getSampleStyleSheet()


    titulo = Paragraph(
        "Reporte de Auditoría - Mesa de Ayuda TI",
        estilos["Title"]
    )


    elementos.append(titulo)


    elementos.append(Paragraph(
        "Fecha de generación: " + datetime.now().strftime("%d/%m/%Y %H:%M"),
        estilos["Normal"]
    ))


    elementos.append(Paragraph(
        "<br/>",
        estilos["Normal"]
    ))



    tabla_datos = [
        ["Usuario", "Acción", "Fecha"]
    ]


    for registro in registros:

        tabla_datos.append([
            registro[0],
            registro[1],
            registro[2]
        ])



    tabla = Table(tabla_datos)


    tabla.setStyle(
        TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, None),
            ("BACKGROUND", (0,0), (-1,0), None),
        ])
    )


    elementos.append(tabla)


    documento.build(elementos)


    return send_file(
        ruta,
        as_attachment=True
    )


@app.context_processor
def notificaciones_globales():

    if "usuario" not in session:
        return {}

    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()


    cursor.execute("""
        SELECT COUNT(*)
        FROM notificaciones
        WHERE usuario=?
        AND leida=0
    """,
    (session["usuario"],))


    cantidad = cursor.fetchone()[0]


    conexion.close()


    return {
        "notificaciones": cantidad
    }

@app.route("/notificaciones")
def notificaciones():

    if "usuario" not in session:
        return redirect("/")


    conexion = sqlite3.connect("mesaayuda.db")
    cursor = conexion.cursor()


    cursor.execute("""
        SELECT id, mensaje, fecha, leida
        FROM notificaciones
        WHERE usuario=?
        ORDER BY id DESC
    """,
    (session["usuario"],))


    avisos = cursor.fetchall()


    # Marcar como leídas

    cursor.execute("""
        UPDATE notificaciones
        SET leida=1
        WHERE usuario=?
    """,
    (session["usuario"],))


    conexion.commit()
    conexion.close()


    return render_template(
        "notificaciones.html",
        avisos=avisos
    )


if __name__ == "__main__":
    app.run(debug=True)