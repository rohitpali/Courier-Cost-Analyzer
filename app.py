import os
import io
import joblib
import pandas as pd
from sqlalchemy import inspect
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

# ---------- App & DB setup ----------
app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = "please_change_me"  # change in production

os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Reset DB if needed
if os.environ.get("RESET_DB", "").lower() in {"1", "true", "yes"}:
    if os.path.exists(db_path):
        try:
            with app.app_context():
                db.session.close()
                db.engine.dispose()
            os.remove(db_path)
            print("⚠ Old database.db removed.")
        except Exception as e:
            print(f"Could not remove DB file: {e}")

# Create tables
with app.app_context():
    inspector = inspect(db.engine)
    if not inspector.has_table("user"):
        db.create_all()
        print("✅ Database tables created.")

# ---------- Flask-Login ----------
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id: str):
    try:
        return db.session.get(User, int(user_id))  # SQLAlchemy 2.x safe
    except Exception:
        return None

# ---------- ML Model Load ----------
MODEL = None
MODEL_PATH = os.path.join("models", "charge_predictor.pkl")
if os.path.exists(MODEL_PATH):
    try:
        MODEL = joblib.load(MODEL_PATH)
        print(f"✅ Loaded ML model: {MODEL_PATH}")
    except Exception as e:
        print(f"⚠ Model load failed: {e}")

# ---------- Helpers ----------
ALLOWED_EXTS = {".csv", ".xlsx", ".xls"}
RESULT_FILE = os.path.join(app.instance_path, "result_output.xlsx")

def _allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTS

def _read_dataframe(file_storage) -> pd.DataFrame:
    """Reads CSV/Excel upload without saving to disk."""
    filename = file_storage.filename or ""
    _, ext = os.path.splitext(filename.lower())
    raw = file_storage.read()
    file_storage.stream.seek(0)

    if ext == ".csv":
        return pd.read_csv(io.BytesIO(raw))
    elif ext in {".xlsx", ".xls"}:
        return pd.read_excel(io.BytesIO(raw))
    raise ValueError("Unsupported file type")

# ---------- Routes ----------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("signup.html")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or Email already exists.", "error")
            return render_template("signup.html")

        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        u = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(u)
        db.session.commit()

        flash("Signup successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = (request.form.get("password") or "")

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid credentials.", "error")
            return render_template("login.html")

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        username=current_user.username,
        model_ready=(MODEL is not None),
        merged_table=None,
        summary_table=None,
        chart_labels=[],
        chart_data=[],
        prediction=None
    )

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    if "files" not in request.files:
        flash("No files uploaded.", "error")
        return redirect(url_for("dashboard"))

    uploads = request.files.getlist("files")
    if not uploads or all(f.filename == "" for f in uploads):
        flash("Please select at least one file.", "error")
        return redirect(url_for("dashboard"))

    file_summaries = []
    dfs = []

    # --- Process each uploaded file separately ---
    for f in uploads:
        if f.filename == "" or not _allowed_file(f.filename):
            flash(f"Unsupported file type: {f.filename}", "error")
            continue

        try:
            df = _read_dataframe(f)

            # Clean column names
            df.columns = (
                df.columns.astype(str)
                .str.strip()
                .str.replace(r"[^\w\s]", "", regex=True)
                .str.replace(" ", "_")
                .str.lower()
            )

            dfs.append(df)

            # Quick stats for this file
            total_orders = len(df)
            avg_weight = (
                round(df["total_weight_as_per_x_kg"].astype(float).mean(), 3)
                if "total_weight_as_per_x_kg" in df.columns else "N/A"
            )
            total_cost = (
                round(df["charges_billed_by_courier_company_rs"].astype(float).sum(), 2)
                if "charges_billed_by_courier_company_rs" in df.columns else "N/A"
            )

            chart_labels, chart_data = [], []
            if "delivery_zone_as_per_x" in df.columns:
                grp = df["delivery_zone_as_per_x"].value_counts().head(10)
                chart_labels = list(grp.index)
                chart_data = [int(x) for x in grp.values]

            file_summaries.append({
                "filename": f.filename,
                "preview": df.head(10).to_dict(orient="records"),
                "total_orders": total_orders,
                "avg_weight": avg_weight,
                "total_cost": total_cost,
                "chart_labels": chart_labels,
                "chart_data": chart_data
            })

        except Exception as e:
            flash(f"Error in {f.filename}: {e}", "error")

    if not dfs:
        flash("No valid files processed.", "error")
        return redirect(url_for("dashboard"))

    # --- Merge all files together ---
    merged_df = pd.concat(dfs, ignore_index=True)

    required_cols = [
        "order_id", "awb_number",
        "total_weight_as_per_x_kg",
        "weight_slab_as_per_x_kg",
        "total_weight_as_per_courier_company_kg",
        "weight_slab_charged_by_courier_company_kg",
        "delivery_zone_as_per_x",
        "delivery_zone_charged_by_courier_company",
        "expected_charge_as_per_x_rs",
        "charges_billed_by_courier_company_rs",
    ]
    for col in required_cols:
        if col not in merged_df.columns:
            merged_df[col] = None

    merged_df["difference"] = (
        pd.to_numeric(merged_df["expected_charge_as_per_x_rs"], errors="coerce")
        - pd.to_numeric(merged_df["charges_billed_by_courier_company_rs"], errors="coerce")
    )

    # --- Summary (Output Data 2) ---
    summary = {
        "correct": {
            "count": int((merged_df["difference"] == 0).sum()),
            "amount": float(merged_df.loc[merged_df["difference"] == 0, "charges_billed_by_courier_company_rs"].sum())
        },
        "over": {
            "count": int((merged_df["difference"] < 0).sum()),
            "amount": float((merged_df.loc[merged_df["difference"] < 0, "difference"] * -1).sum())
        },
        "under": {
            "count": int((merged_df["difference"] > 0).sum()),
            "amount": float(merged_df.loc[merged_df["difference"] > 0, "difference"].sum())
        },
    }

    chart_labels = ["Correct", "Overcharged", "Undercharged"]
    chart_data = [summary["correct"]["count"], summary["over"]["count"], summary["under"]["count"]]

    # Save output
    merged_df.to_excel(RESULT_FILE, index=False)

    # --- Prediction ---
    prediction_text = "Model not loaded."
    if MODEL is not None:
        try:
            numeric_df = merged_df.select_dtypes(include=["number"])
            if not numeric_df.empty:
                preds = MODEL.predict(numeric_df)
                prediction_text = f"ML Insights: {len(preds)} predictions generated. Example: {preds[:3].tolist()}"
            else:
                prediction_text = "Prediction skipped (no numeric features)."
        except Exception as e:
            prediction_text = f"Prediction failed: {e}"

    return render_template(
        "dashboard.html",
        username=current_user.username,
        model_ready=(MODEL is not None),
        file_summaries=file_summaries,   # NEW (per file view)
        merged_table=merged_df.head(50).to_dict(orient="records"),
        summary_table=summary,
        chart_labels=chart_labels,
        chart_data=chart_data,
        prediction=prediction_text
    )


@app.route("/download")
@login_required
def download():
    if os.path.exists(RESULT_FILE):
        return send_file(RESULT_FILE, as_attachment=True)
    flash("No result file available.", "error")
    return redirect(url_for("dashboard"))

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)
