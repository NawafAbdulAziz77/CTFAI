# CTFd/admin/generatesertif.py
from flask import render_template, request, url_for, redirect, flash, current_app, send_file, abort
from CTFd.admin import admin
from CTFd.utils.decorators import admins_only
from CTFd.models import db, Users
from CTFd.utils import get_config
from CTFd.utils.modes import TEAMS_MODE
from datetime import datetime
import os, hashlib, re

# ====== PDF: ReportLab ======
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import landscape as rl_landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import HexColor
from werkzeug.utils import secure_filename

# (opsional) untuk deteksi orientasi gambar
try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

# --------- Font opsional (DejaVuSans) ----------
try:
    font_path = os.path.join(os.path.dirname(__file__), "..", "static", "fonts", "DejaVuSans.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
        BASE_FONT = "DejaVuSans"
    else:
        BASE_FONT = "Helvetica"
except Exception:
    BASE_FONT = "Helvetica"

# ====== (opsional) nama tanda tangan default — ubah sesuai kebutuhan ======
LEFT_SIGN_NAME  = os.environ.get("CERT_LEFT_NAME",  "")
LEFT_SIGN_TITLE = os.environ.get("CERT_LEFT_TITLE", "")
RIGHT_SIGN_NAME  = os.environ.get("CERT_RIGHT_NAME",  "")
RIGHT_SIGN_TITLE = os.environ.get("CERT_RIGHT_TITLE", "")

# ====== Model ======
class CertificateIssue(db.Model):
    __tablename__ = "certificate_issues"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    user_name = db.Column(db.String(128))
    team_id = db.Column(db.Integer, index=True)
    team_name = db.Column(db.String(128))
    score = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    criteria = db.Column(db.String(64))       # e.g. "top_10" / "score>=500" / "manual"
    file_rel = db.Column(db.String(256))      # relative to app.root_path
    sha1 = db.Column(db.String(40), index=True)
    issued_at = db.Column(db.DateTime, default=db.func.now())

# ====== Utils ======
def _cert_dir():
    out_dir = os.path.join(current_app.root_path, "static", "certificates")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def _event_name():
    return get_config("ctf_name") or current_app.config.get("CTF_NAME") or "CTF"

def _parse_place(place):
    if place is None:
        return None
    try:
        return int(place)
    except (TypeError, ValueError):
        m = re.search(r"\d+", str(place))
        return int(m.group()) if m else None

def _safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        m = re.search(r"\d+", str(val))
        return int(m.group()) if m else default

def _user_score_place(user):
    if user and user.account:
        score = user.account.get_score(admin=True)
        place = user.account.get_place(admin=True)
        try:
            score_int = int(score or 0)
        except Exception:
            score_int = int(float(score or 0))
        return score_int, _parse_place(place)
    return 0, None

def _sha1_of_file(path:str)->str:
    h = hashlib.sha1()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def _draw_center_text(c, text, y, size=24, color=HexColor("#111111")):
    c.setFillColor(color)
    c.setFont(BASE_FONT, size)
    c.drawCentredString(c._pagesize[0]/2.0, y, text)

def _fit_text_width(text, font, base_size, max_width, min_size=14):
    size = base_size
    while size >= min_size:
        if stringWidth(text, font, size) <= max_width:
            return size
        size -= 1
    return min_size

def _wrap_lines(text, font, size, max_width):
    words = str(text or "").split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if stringWidth(test, font, size) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def _resolve_bg(background_path: str | None) -> str | None:
    if not background_path:
        return None
    bg = background_path.strip()
    # hapus prefix slash/backslash
    rel = bg.lstrip("/\\")
    candidates = [
        os.path.normpath(os.path.join(current_app.root_path, rel)),
        os.path.normpath(os.path.join(current_app.static_folder, rel.split("static",1)[-1].lstrip("/\\")))
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    current_app.logger.warning(f"BG not found. Tried: {candidates}")
    return None

def _gen_pdf(
    filename:str,
    *,
    user_name:str,
    team_name:str|None,
    score:int,
    rank:int|None,
    event_name:str,
    date_str:str,
    reason:str,
    background_path:str|None = None,
    extra_text:str|None = None,
    verify_sha1:str|None = None,
):
    """
    Render PDF A4; orientasi otomatis mengikuti gambar background.
    """
    full_path = os.path.join(_cert_dir(), filename)

    # --- tentukan orientasi dari gambar ---
    bg_abs = _resolve_bg(background_path)
    is_landscape = True  # default: landscape
    if bg_abs and PILImage:
        try:
            with PILImage.open(bg_abs) as im:
                is_landscape = im.width >= im.height
        except Exception:
            pass

    page_size = rl_landscape(A4) if is_landscape else A4
    c = canvas.Canvas(full_path, pagesize=page_size)
    W, H = page_size

    # ===== 1) Background =====
    if bg_abs:
        try:
            c.drawImage(ImageReader(bg_abs), 0, 0, width=W, height=H,
                        preserveAspectRatio=False, mask='auto')
        except Exception as e:
            current_app.logger.warning(f"Gagal render background: {bg_abs} -> {e}")
            _draw_center_text(c, f"[BG load failed: {os.path.basename(bg_abs)}]", H - 20, size=10, color=HexColor("#AA0000"))
    else:
        flash(f"Background tidak ditemukan. Cek path: {background_path}", "warning")
        _draw_center_text(c, "[Background NOT FOUND]", H - 20, size=10, color=HexColor("#AA0000"))

    # ===== 2) Teks dinamis =====
    # Layout portrait/landscape sedikit berbeda
    if is_landscape:
        # Nama di area dekat top (sesuaikan dengan template landscape)
        max_name_w = W - 180
        name_y = H - 265
        name_size = _fit_text_width(user_name, BASE_FONT, 34, max_name_w, min_size=18)
        _draw_center_text(c, user_name, name_y, size=name_size, color=HexColor("#0F2233"))
        if team_name:
            _draw_center_text(c, f"({team_name})", name_y - 20, size=12, color=HexColor("#3A4B5C"))

        para_top = H - 370
        para_max_w = W - 200
        body_size = 12
        body_color = HexColor("#333333")
        y = para_top
        for txt in (reason, extra_text):
            if txt:
                for ln in _wrap_lines(txt, BASE_FONT, body_size, para_max_w):
                    _draw_center_text(c, ln, y, size=body_size, color=body_color)
                    y -= 16
                y -= 6

        meta = []
        if score: meta.append(f"Skor: {score}")
        if rank:  meta.append(f"Peringkat: #{rank}")
        if meta:
            _draw_center_text(c, " • ".join(meta), y - 10, size=10, color=HexColor("#666666"))

        # tanda tangan
        # tanda tangan (digambar hanya jika ada isi)
        line_y = 95
        line_w = 210
        c.setStrokeColor(HexColor("#778899"))

        left_has_any = bool(LEFT_SIGN_NAME or LEFT_SIGN_TITLE)
        right_has_any = bool(RIGHT_SIGN_NAME or RIGHT_SIGN_TITLE)

        if left_has_any:
            c.line(90, line_y, 90 + line_w, line_y)
            if LEFT_SIGN_NAME:
                _draw_center_text(c, LEFT_SIGN_NAME, line_y - 14, size=11, color=HexColor("#0F2233"))
            if LEFT_SIGN_TITLE:
                _draw_center_text(c, LEFT_SIGN_TITLE, line_y - 28, size=9.5, color=HexColor("#5C6B78"))

        if right_has_any:
            c.line(W - 90 - line_w, line_y, W - 90, line_y)
            if RIGHT_SIGN_NAME:
                _draw_center_text(c, RIGHT_SIGN_NAME, line_y - 14, size=11, color=HexColor("#0F2233"))
            if RIGHT_SIGN_TITLE:
                _draw_center_text(c, RIGHT_SIGN_TITLE, line_y - 28, size=9.5, color=HexColor("#5C6B78"))

    else:
        max_name_w = W - 140
        name_y = 610
        name_size = _fit_text_width(user_name, BASE_FONT, 30, max_name_w, min_size=18)
        _draw_center_text(c, user_name, name_y, size=name_size, color=HexColor("#0F2233"))
        if team_name:
            _draw_center_text(c, f"({team_name})", name_y - 20, size=12, color=HexColor("#3A4B5C"))

        para_y_start = 420
        para_max_w = W - 140
        body_size = 11.5
        body_color = HexColor("#333333")

        y = para_y_start
        for txt in (reason, extra_text):
            if txt:
                for ln in _wrap_lines(txt, BASE_FONT, body_size, para_max_w):
                    _draw_center_text(c, ln, y, size=body_size, color=body_color)
                    y -= 16
                y -= 6

        meta = []
        if score: meta.append(f"Skor: {score}")
        if rank:  meta.append(f"Peringkat: #{rank}")
        if meta:
            _draw_center_text(c, " • ".join(meta), y - 10, size=10, color=HexColor("#666666"))

        line_y = 150
        line_w = 190
        c.setStrokeColor(HexColor("#778899"))

        left_has_any = bool(LEFT_SIGN_NAME or LEFT_SIGN_TITLE)
        right_has_any = bool(RIGHT_SIGN_NAME or RIGHT_SIGN_TITLE)

        if left_has_any:
            c.line(80, line_y, 80 + line_w, line_y)
            if LEFT_SIGN_NAME:
                _draw_center_text(c, LEFT_SIGN_NAME, line_y - 14, size=11, color=HexColor("#0F2233"))
            if LEFT_SIGN_TITLE:
                _draw_center_text(c, LEFT_SIGN_TITLE, line_y - 28, size=10, color=HexColor("#5C6B78"))

        if right_has_any:
            c.line(W - 80 - line_w, line_y, W - 80, line_y)
            if RIGHT_SIGN_NAME:
                _draw_center_text(c, RIGHT_SIGN_NAME, line_y - 14, size=11, color=HexColor("#0F2233"))
            if RIGHT_SIGN_TITLE:
                _draw_center_text(c, RIGHT_SIGN_TITLE, line_y - 28, size=10, color=HexColor("#5C6B78"))

    c.showPage()
    c.save()
    return full_path

# ====== ADMIN ROUTES ======

@admin.route("/admin/certificates", methods=["GET", "POST"])
@admins_only
def admin_certificates():
    if request.method == "POST":
        mode = request.form.get("mode", "top")
        top_n = _safe_int(request.form.get("top_n", 10), 10)
        threshold = _safe_int(request.form.get("threshold", 0), 0)

        # --- ambil pilihan background dari preset/custom ---
        bg_choice = (request.form.get("background_path") or "").strip()          # '', '/static/..', '__custom__'
        bg_manual = (request.form.get("background_manual") or "").strip() or None
        background_path_final = None
        if bg_choice == "__custom__":
            background_path_final = bg_manual
        else:
            background_path_final = bg_choice or None

        # --- override jika user upload file ---
        bg_file = request.files.get("background_file")
        if bg_file and getattr(bg_file, "filename", ""):
            try:
                ext = os.path.splitext(bg_file.filename)[1].lower()
                if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
                    flash("Format background harus PNG/JPG/WebP.", "warning")
                else:
                    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    safe = secure_filename(bg_file.filename)
                    # simpan ke static/certificates
                    save_dir = _cert_dir()  # memastikan folder ada
                    saved_name = f"bg_{ts}{ext}"
                    abs_save = os.path.join(save_dir, saved_name)
                    bg_file.save(abs_save)
                    background_path_final = f"/static/certificates/{saved_name}"
                    flash("Background berhasil diupload dan digunakan.", "success")
            except Exception as e:
                current_app.logger.warning(f"Gagal upload background: {e}")
                flash("Gagal upload background.", "danger")

        # --- teks sertifikat ---
        reason = (request.form.get("reason") or "").strip() or (
            "Telah mengikuti dan menyelesaikan Pelatihan Dasar Cybersecurity yang diselenggarakan dengan penuh dedikasi."
        )
        extra_text = (request.form.get("extra_text") or "").strip() or (
            "Pelatihan ini mencakup pemahaman mendasar tentang keamanan sistem informasi, praktik etis dalam pengujian keamanan, serta strategi pertahanan terhadap ancaman siber."
        )

        # --- ambil user & ranking ---
        users = Users.query.order_by(Users.id.asc()).all()
        scored = []
        for u in users:
            s, p = _user_score_place(u)
            scored.append((u, s, p))
        scored.sort(key=lambda t: t[1], reverse=True)

        rank_map, rank_counter = {}, 1
        for u, s, p in scored:
            rank_map[u.id] = (s, p if p else rank_counter)
            rank_counter += 1

        issued_count = 0
        today = datetime.utcnow().strftime("%Y-%m-%d")
        event_name = _event_name()

        for u, _, _ in scored:
            score, rank = rank_map[u.id]
            ok = (mode == "top" and rank <= top_n) or (mode == "score" and score >= threshold)
            if not ok:
                continue

            # hindari duplikasi untuk kriteria sama
            exists = CertificateIssue.query.filter_by(
                user_id=u.id,
                criteria=(f"top_{top_n}" if mode == "top" else f"score>={threshold}")
            ).first()
            if exists:
                continue

            fname = f"cert_u{u.id}_{today}.pdf"
            full = _gen_pdf(
                filename=fname,
                user_name=u.name,
                team_name=(getattr(u, "team", None).name
                           if (get_config("user_mode") == TEAMS_MODE and u.team)
                           else None),
                score=score,
                rank=rank,
                event_name=event_name,
                date_str=today,
                reason=reason,
                background_path=background_path_final,  # <== pakai path final
                extra_text=extra_text,
                verify_sha1=None,
            )
            sha1 = _sha1_of_file(full)

            rel = os.path.relpath(full, current_app.root_path).replace("\\", "/")
            issue = CertificateIssue(
                user_id=u.id,
                user_name=u.name,
                team_id=u.team_id if hasattr(u, "team_id") else None,
                team_name=(u.team.name if (get_config("user_mode") == TEAMS_MODE and u.team) else None),
                score=score,
                rank=rank,
                criteria=(f"top_{top_n}" if mode == "top" else f"score>={threshold}"),
                file_rel=rel,
                sha1=sha1,
            )
            db.session.add(issue)
            issued_count += 1

        db.session.commit()
        flash(f"Issued {issued_count} certificate(s).", "success")
        return redirect(url_for("admin.admin_certificates"))

    recent = CertificateIssue.query.order_by(CertificateIssue.issued_at.desc()).limit(50).all()
    return render_template("admin/certificates.html", issues=recent)


@admin.route("/admin/certificates/issue/<int:user_id>", methods=["POST"])
@admins_only
def admin_cert_issue_one(user_id):
    user = Users.query.filter_by(id=user_id).first_or_404()
    score, place = _user_score_place(user)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    event_name = _event_name()

    background_path = (request.form.get("background_path") or "").strip() or None
    reason = (request.form.get("reason") or "").strip() or (
        "Telah mengikuti dan menyelesaikan Pelatihan Dasar Cybersecurity yang diselenggarakan dengan penuh dedikasi."
    )
    extra_text = (request.form.get("extra_text") or "").strip() or (
        "Pelatihan ini mencakup pemahaman mendasar tentang keamanan sistem informasi, praktik etis dalam pengujian keamanan, serta strategi pertahanan terhadap ancaman siber."
    )

    fname = f"cert_u{user.id}_{today}.pdf"
    full = _gen_pdf(
        filename=fname,
        user_name=user.name,
        team_name=(getattr(user, "team", None).name
                   if (get_config("user_mode") == TEAMS_MODE and user.team)
                   else None),
        score=score,
        rank=place,
        event_name=event_name,
        date_str=today,
        reason=reason,
        background_path=background_path,
        extra_text=extra_text,
        verify_sha1=None,
    )
    sha1 = _sha1_of_file(full)
    rel = os.path.relpath(full, current_app.root_path).replace("\\", "/")

    issue = CertificateIssue(
        user_id=user.id,
        user_name=user.name,
        team_id=user.team_id if hasattr(user, "team_id") else None,
        team_name=(user.team.name if (get_config("user_mode") == TEAMS_MODE and user.team) else None),
        score=score,
        rank=place,
        criteria="manual",
        file_rel=rel,
        sha1=sha1,
    )
    db.session.add(issue)
    db.session.commit()

    flash("Certificate issued.", "success")
    return redirect(url_for("admin.users_detail", user_id=user.id))

@admin.route("/admin/certificates/download/<int:issue_id>")
@admins_only
def admin_cert_download(issue_id):
    issue = CertificateIssue.query.filter_by(id=issue_id).first_or_404()
    abs_path = os.path.join(current_app.root_path, issue.file_rel.lstrip("/"))
    if not os.path.exists(abs_path):
        abort(404)
    return send_file(
        abs_path,
        as_attachment=True,
        download_name=os.path.basename(abs_path),
        mimetype="application/pdf"
    )

@admin.route("/admin/certificates/delete/<int:issue_id>", methods=["POST"])
@admins_only
def admin_cert_delete(issue_id):
    issue = CertificateIssue.query.filter_by(id=issue_id).first_or_404()
    abs_path = os.path.join(current_app.root_path, issue.file_rel.lstrip("/"))
    try:
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except Exception as e:
        current_app.logger.warning(f"Gagal hapus file sertifikat: {e}")
    db.session.delete(issue)
    db.session.commit()
    flash("Certificate deleted.", "success")
    return redirect(url_for("admin.admin_certificates"))
