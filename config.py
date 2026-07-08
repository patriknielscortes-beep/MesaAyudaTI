import os

class Config:
    # 🔐 Seguridad básica Flask
    SECRET_KEY = os.environ.get("SECRET_KEY") or "clave_super_secreta_123"

    # 🗄️ Base de datos (cámbiala si usas MySQL o PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///mesa_ayuda.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📧 CONFIGURACIÓN DE CORREO (GMAIL)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    # ⚠️ IMPORTANTE: usar contraseña de aplicación de Gmail
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or "tucorreo@gmail.com"
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or "tu_password_app"

    MAIL_DEFAULT_SENDER = MAIL_USERNAME