from flask import render_template, request, url_for, redirect, flash, current_app, send_from_directory
from CTFd.admin import admin
from CTFd.utils.decorators import admins_only
from CTFd.models import db
import werkzeug.utils
import os
import pandas as pd
import random
import re
import requests
import time
from flask import jsonify
from datetime import datetime

# === Model untuk menyimpan history soal AI ===
class GeneratedQuestion(db.Model):
    __tablename__ = "generated_questions"
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    kategori = db.Column(db.String(80))
    filename = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=db.func.now())
    duration = db.Column(db.Float)

# === Konfigurasi API dan dataset ===
API_KEY = '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'
API_URL = 'https://openrouter.ai/api/v1/chat/completions'
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'dataset.csv')

df_dataset = pd.read_csv(DATASET_PATH)
few_shot_examples = df_dataset.to_dict(orient="records")

def create_few_shot_prompt(kategori, topik, jumlah=2):
    contoh_terpilih = [c for c in few_shot_examples if c['kategori'] == kategori]
    contoh = random.sample(contoh_terpilih if len(contoh_terpilih) >= jumlah else few_shot_examples, jumlah)

    return "\n\n".join(
        f"Kategori: {c['kategori']}\nTopik: {c['topik']}\nSoal: {c['soal']}\nHint: {c['hint']}\nTingkat Kesulitan: {c['tingkat']}\nNilai: {c['nilai']}\nCtf: {c['jawaban']}"
        for c in contoh
    )

def generate_ctf(kategori_input, topik_input):
    few_shot_prompt = create_few_shot_prompt(kategori_input, topik_input)

    ekstensi_map = {
        "web": "index.html",
        "pwn": "exploit.py",
        "crypto": "data.enc",
        "reverse": "reverse.asm",
        "forensics": "evidence.png",
        "general skills": "script.sh"
    }
    suggested_file = ekstensi_map.get(kategori_input.lower(), "file.txt")

    task_prompt = (
        f"{few_shot_prompt}\n\n---\n"
        f"Kategori: {kategori_input}\nTopik: {topik_input}\n"
        f"Buatkan satu soal CTF baru yang mengikuti format di atas.\n"
        f"Jika perlu, lampirkan file sesuai topik. Format:\n"
        f"---file:{suggested_file}---\n<isi>\n---"
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek/deepseek-chat:free",
        "messages": [
            {"role": "system", "content": "Kamu adalah pembuat soal CTF profesional."},
            {"role": "user", "content": task_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        response = requests.post(API_URL, json=data, headers=headers)
        if response.status_code != 200:
            return None, f"API Error: {response.status_code}"

        result = response.json()["choices"][0]["message"]["content"].replace("**", "").strip()

        file_match = re.search(r"---file:(.+?)---\s*([\s\S]+?)(?:---|$)", result)
        filename = None
        if file_match:
            filename = werkzeug.utils.secure_filename(file_match.group(1).strip())
            content = file_match.group(2).strip()

            output_dir = os.path.join(current_app.root_path, "generated_files")
            os.makedirs(output_dir, exist_ok=True)

            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            result = result.replace(file_match.group(0), "").strip()

        return result.strip(), filename
    except Exception as e:
        return None, f"Exception: {str(e)}"

@admin.route("/admin/generate", methods=["GET", "POST"], endpoint="generate")
@admins_only
def admin_generate_ai():
    output = None
    filename = None
    error = None
    history = GeneratedQuestion.query.order_by(GeneratedQuestion.created_at.desc()).limit(10).all()

    if request.method == "POST":
        kategori = request.form.get("kategori")
        topik = request.form.get("topik")

        start_time = time.time()
        output, filename_or_error = generate_ctf(kategori, topik)
        end_time = time.time()
        duration = end_time - start_time  # dalam detik (float)

        if output:
            filename = filename_or_error
            flash("Soal berhasil dihasilkan!", "success")

            # Simpan ke database
            new_entry = GeneratedQuestion(
                kategori=kategori,
                prompt="",  # jika kamu simpan prompt
                response=output,
                filename=filename,
                duration=duration
            )
            db.session.add(new_entry)
            db.session.commit()
        else:
            error = filename_or_error
            flash(error, "danger")

    return render_template("admin/generate.html", output=output, filename=filename, history=history)

@admin.route("/admin/download/<path:filename>")
@admins_only
def admin_download_file(filename):
    safe_filename = werkzeug.utils.secure_filename(filename)
    folder = os.path.join(current_app.root_path, "generated_files")
    return send_from_directory(folder, safe_filename, as_attachment=True)

@admin.route("/admin/history", methods=["GET"], endpoint="history")
@admins_only
def admin_history_ai():
    all_history = GeneratedQuestion.query.order_by(GeneratedQuestion.created_at.desc()).all()
    return render_template("admin/history.html", history=all_history)


@admin.route('/admin/generate/history/json')
@admins_only
def get_generate_history():
    data = GeneratedQuestion.query.order_by(GeneratedQuestion.created_at.desc()).all()
    output = []

    for item in data:
        output.append({
            "id": item.id,
            "kategori": item.kategori,
            "response": item.response,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "filename": item.filename,
            "duration": item.duration
        })

    return jsonify(output)


@admin.route('/admin/generate/export/excel')
@admins_only
def export_generate_history_excel():
    data = GeneratedQuestion.query.order_by(GeneratedQuestion.created_at.desc()).all()

    rows = []
    for item in data:
        rows.append({
            "ID": item.id,
            "Kategori": item.kategori,
            "Response": item.response,
            "File": item.filename,
            "Durasi (detik)": item.duration,
            "Waktu Dibuat": item.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(rows)

    # Simpan ke file sementara
    export_folder = os.path.join(current_app.root_path, "exports")
    os.makedirs(export_folder, exist_ok=True)
    export_path = os.path.join(export_folder, "history_soal_ctf.xlsx")
    df.to_excel(export_path, index=False)

    return send_from_directory(export_folder, "history_soal_ctf.xlsx", as_attachment=True)
