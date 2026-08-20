"""
app.py
Main Flask application: routes, auth wiring, security middleware.
Run with:  python app.py   (dev)   or   gunicorn app:app   (prod)
"""

import csv
import io
import os
from datetime import datetime

from flask import (Flask, Response, abort, flash, jsonify, redirect,
                    render_template, request, session, url_for)
from flask_login import (LoginManager, current_user, login_required,
                          login_user, logout_user)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, or_

from config import Config
from database import db, init_db
from forms import DetectForm, HistorySearchForm, LoginForm
from models import PredictionHistory, User
from predict import ModelNotTrainedError, get_metadata, predict_news
from utils import truncate

# --------------------------------------------------------------------------------
# App factory / initialization
# --------------------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

init_db(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access the admin dashboard."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --------------------------------------------------------------------------------
# Security headers (defense in depth against XSS/clickjacking/sniffing)
# --------------------------------------------------------------------------------
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# --------------------------------------------------------------------------------
# Public pages
# --------------------------------------------------------------------------------
@app.route("/")
def index():
    total = PredictionHistory.query.count()
    real_count = PredictionHistory.query.filter_by(prediction="REAL").count()
    fake_count = PredictionHistory.query.filter_by(prediction="FAKE").count()
    try:
        meta = get_metadata()
    except ModelNotTrainedError:
        meta = {}
    stats = {
        "total": total,
        "real": real_count,
        "fake": fake_count,
        "accuracy": round(meta.get("accuracy", 0) * 100, 1) if meta.get("accuracy") else None,
    }
    return render_template("index.html", stats=stats)


@app.route("/detector", methods=["GET", "POST"])
def detector():
    form = DetectForm()
    result = None

    if form.validate_on_submit():
        raw_text = form.news_text.data.strip()
        try:
            prediction = predict_news(raw_text)
        except ModelNotTrainedError:
            flash("The ML model hasn't been trained yet. Run 'python train_model.py' first.", "danger")
            return render_template("detector.html", form=form, result=None)

        entry = PredictionHistory(
            user_id=current_user.id if current_user.is_authenticated else None,
            news_title=truncate(raw_text, 120),
            news_text=raw_text,
            prediction=prediction["label"],
            confidence=prediction["confidence"],
            model_used=prediction["model_used"],
        )
        db.session.add(entry)
        db.session.commit()

        result = {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "model_used": prediction["model_used"],
            "id": entry.id,
        }

    return render_template("detector.html", form=form, result=result)


@app.route("/api/detect", methods=["POST"])
def api_detect():
    """JSON endpoint used by the AJAX 'Detect' button for a snappier UI."""
    form = DetectForm(meta={"csrf": True})
    if not form.validate_on_submit():
        errors = form.news_text.errors or ["Invalid input."]
        return jsonify({"ok": False, "errors": errors}), 400

    raw_text = form.news_text.data.strip()
    try:
        prediction = predict_news(raw_text)
    except ModelNotTrainedError:
        return jsonify({"ok": False, "errors": ["Model not trained yet. Run train_model.py."]}), 503

    entry = PredictionHistory(
        user_id=current_user.id if current_user.is_authenticated else None,
        news_title=truncate(raw_text, 120),
        news_text=raw_text,
        prediction=prediction["label"],
        confidence=prediction["confidence"],
        model_used=prediction["model_used"],
    )
    db.session.add(entry)
    db.session.commit()

    return jsonify({
        "ok": True,
        "label": prediction["label"],
        "confidence": prediction["confidence"],
        "model_used": prediction["model_used"],
        "id": entry.id,
        "created_at": entry.created_at.strftime("%Y-%m-%d %H:%M"),
    })


# --------------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------------
@app.route("/history")
def history():
    form = HistorySearchForm(request.args, meta={"csrf": False})
    page = request.args.get("page", 1, type=int)
    query = request.args.get("query", "", type=str).strip()

    q = PredictionHistory.query
    if query:
        like = f"%{query}%"
        q = q.filter(or_(PredictionHistory.news_title.ilike(like),
                          PredictionHistory.news_text.ilike(like)))

    pagination = q.order_by(PredictionHistory.created_at.desc()).paginate(
        page=page, per_page=Config.HISTORY_PAGE_SIZE, error_out=False
    )

    return render_template("history.html", pagination=pagination, form=form, query=query)


@app.route("/history/delete/<int:entry_id>", methods=["POST"])
def delete_history(entry_id):
    entry = db.session.get(PredictionHistory, entry_id)
    if not entry:
        abort(404)
    db.session.delete(entry)
    db.session.commit()
    flash("Entry deleted.", "success")
    return redirect(url_for("history", **request.args))


@app.route("/history/export")
def export_history():
    rows = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ID", "Date", "News Title", "Prediction", "Confidence (%)", "Model"])
    for r in rows:
        writer.writerow([r.id, r.created_at.strftime("%Y-%m-%d %H:%M"), r.news_title,
                          r.prediction, f"{r.confidence:.1f}", r.model_used])

    output = buffer.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=prediction_history.csv"},
    )


# --------------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            session.permanent = True
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin_dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------------
# Admin dashboard
# --------------------------------------------------------------------------------
@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    total = PredictionHistory.query.count()
    real_count = PredictionHistory.query.filter_by(prediction="REAL").count()
    fake_count = PredictionHistory.query.filter_by(prediction="FAKE").count()

    try:
        meta = get_metadata()
    except ModelNotTrainedError:
        meta = {}

    avg_confidence = db.session.query(func.avg(PredictionHistory.confidence)).scalar() or 0
    recent = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).limit(10).all()

    stats = {
        "total": total,
        "real": real_count,
        "fake": fake_count,
        "avg_confidence": round(avg_confidence, 1),
        "model_name": meta.get("best_model_name", "Not trained"),
        "model_accuracy": round(meta.get("accuracy", 0) * 100, 1) if meta.get("accuracy") else None,
        "trained_at": meta.get("trained_at", "N/A"),
        "all_model_results": meta.get("all_results", {}),
    }

    return render_template("admin.html", stats=stats, recent=recent)


# --------------------------------------------------------------------------------
# Error handlers
# --------------------------------------------------------------------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template("errors.html", code=403, message="Forbidden"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("errors.html", code=404, message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("errors.html", code=500, message="Server error"), 500


@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
