from __future__ import annotations
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from flask_app.models import Base, Tenant, User, Role
import os

app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
os.makedirs(app.instance_path, exist_ok=True)

# DB: SQLite en instance/app.db
db_url = "sqlite:///" + os.path.join(app.instance_path, "app.db")
engine = create_engine(db_url, echo=False, future=True)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id: str):
    with Session(engine) as s:
        return s.get(User, int(user_id))

@app.route("/")
def index():
    return redirect(url_for("register"))

# --------- INIT / SEED ----------
@app.route("/init_db")
def init_db():
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        # Si ya hay tenants, no duplicar
        if not s.scalars(select(Tenant)).first():
            boxfit = Tenant(name="BoxFit", slug="boxfit")
            zen = Tenant(name="Zen Pilates", slug="zenpilates")
            s.add_all([boxfit, zen])
            s.flush()

            # Dueñas (password: owner123)
            p = generate_password_hash("owner123")
            s.add_all([
                User(name="Dueña BoxFit", email="duena@boxfit.com", password_hash=p, role=Role.OWNER, tenant_id=boxfit.id),
                User(name="Dueña Zen", email="duena@zen.com", password_hash=p, role=Role.OWNER, tenant_id=zen.id),
            ])
            s.commit()
    return "DB inicializada con seed. Usuarios dueños: duena@boxfit.com / duena@zen.com (pass: owner123)"

# --------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    with Session(engine) as s:
        tenants = s.scalars(select(Tenant).order_by(Tenant.name)).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        tenant_id = request.form.get("tenant_id")

        if not name or not email or not password or not tenant_id:
            flash("Completá todos los campos", "error")
            return redirect(url_for("register"))

        try:
            validate_email(email)
        except EmailNotValidError as e:
            flash("Email inválido", "error")
            return redirect(url_for("register"))

        with Session(engine) as s:
            tenant = s.get(Tenant, int(tenant_id))
            if not tenant:
                flash("Gimnasio inválido", "error")
                return redirect(url_for("register"))

            # ¿Email ya existe?
            if s.scalars(select(User).where(User.email == email)).first():
                flash("Ese email ya está registrado", "error")
                return redirect(url_for("register"))

            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=Role.CLIENT,
                tenant_id=tenant.id
            )
            s.add(user)
            s.commit()

        return redirect(url_for("tenant_home", slug=tenant.slug))

    return render_template("register.html", tenants=tenants)

# --------- LOGIN / LOGOUT ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with Session(engine) as s:
            user = s.scalars(select(User).where(User.email == email)).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                if user.role == Role.OWNER:
                    return redirect(url_for("admin"))
                # Cliente: si tiene tenant, ir a home del tenant
                if user.tenant_id:
                    t = s.get(Tenant, user.tenant_id)
                    return redirect(url_for("tenant_home", slug=t.slug))
                return redirect(url_for("index"))
        flash("Credenciales inválidas", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# --------- VISTAS ----------
@app.route("/t/<slug>/home")
def tenant_home(slug: str):
    with Session(engine) as s:
        tenant = s.scalars(select(Tenant).where(Tenant.slug == slug)).first()
        if not tenant:
            return "Gimnasio no encontrado", 404
    return render_template("home.html", tenant=tenant)

@app.route("/admin")
@login_required
def admin():
    if current_user.role != Role.OWNER:
        return "No autorizado", 403
    with Session(engine) as s:
        t = s.get(Tenant, current_user.tenant_id) if current_user.tenant_id else None
    return render_template("admin.html", tenant=t)

if __name__ == "__main__":
    app.run(debug=True)
