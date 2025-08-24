from flask import render_template, request, url_for, redirect, flash, current_app, send_from_directory, jsonify
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
from datetime import datetime

class GeneratedQuestion(db.Model):
    __tablename__ = "generated_questions"
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    kategori = db.Column(db.String(80))
    topik = db.Column(db.String(80))
    filename = db.Column(db.String(120))
    tingkat = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=db.func.now())
    duration = db.Column(db.Float)

API_KEY = ''
API_URL = ''
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'dataset.csv')

df_dataset = pd.read_csv(DATASET_PATH)
few_shot_examples = df_dataset.to_dict(orient="records")

def create_few_shot_prompt(kategori, topik, jumlah=2):
    contoh_terpilih = [c for c in few_shot_examples if c['kategori'].lower() == kategori.lower()]
    contoh = random.sample(contoh_terpilih if len(contoh_terpilih) >= jumlah else few_shot_examples, jumlah)

    return "\n\n".join(
        f"Kategori: {c['kategori']}\nTopik: {c['topik']}\nSoal: {c['soal']}\nHint: {c['hint']}\nTingkat Kesulitan: {c['tingkat']}\nNilai: {c['nilai']}\nCtf: {c['jawaban']}"
        for c in contoh
    )

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
        other_topik = request.form.get("other_topic")
        tingkat = request.form.get("tingkat")
        prompt_manual = request.form.get("prompt", "").strip()

        if topik == "Other" and other_topik:
            topik = other_topik

        pendekatan = ""
        if prompt_manual:
            prompt_used = prompt_manual
            if prompt_manual.lower().startswith("bahasa sederhana:"):
                pendekatan = "Bahasa Sederhana"
                task_prompt = prompt_manual.split(":", 1)[1].strip()
            elif prompt_manual.lower().startswith("keyword:"):
                pendekatan = "Keyword-Based"
                keyword_parts = prompt_manual.split(":", 1)[1].split(",")
                task_prompt = " ".join([part.strip() for part in keyword_parts])
            elif prompt_manual.lower().startswith("pertanyaan:") or prompt_manual.lower().startswith("tanya:"):
                pendekatan = "Interrogative"
                task_prompt = prompt_manual.split(":", 1)[1].strip()
            elif prompt_manual.lower().startswith("minimal:"):
                pendekatan = "Minimal Token"
                token_parts = prompt_manual.split(":", 1)[1].split(",")
                task_prompt = ", ".join([part.strip() for part in token_parts])
            elif prompt_manual.lower().startswith("komplit:") or prompt_manual.lower().startswith("structured:"):
                pendekatan = "Structured Prompt"
                task_prompt = prompt_manual.split(":", 1)[1].strip()
            else:
                task_prompt = prompt_manual
        else:
            few_shot_prompt = create_few_shot_prompt(kategori, topik)
            ekstensi_map = {
                "web": "index.html",
                "pwn": "exploit.py",
                "crypto": "data.enc",
                "reverse": "reverse.asm",
                "forensics": "evidence.png",
                "general skills": "script.sh"
            }
            suggested_file = ekstensi_map.get(kategori.lower(), "file.txt")

            task_prompt = (
                f"Silakan buat satu soal Capture The Flag (CTF) dalam Bahasa Indonesia berdasarkan informasi berikut:\n\n"
                f"- Kategori: {kategori}\n"
                f"- Topik: {topik}\n"
                f"- Tingkat Kesulitan: {tingkat}\n\n"
                f"Hasilkan soal dalam format **persis** seperti ini, dan jangan hapus atau ubah bagian mana pun:\n\n"
                f"Kategori: {kategori}\n"
                f"Topik: {topik}\n"
                f"Tingkat Kesulitan: {tingkat}\n"
                f"Soal: <isi soal>\n"
                f"Hint: <petunjuk>\n"
                f"Nilai: <angka>\n"
                f"Ctf: <flag dengan format PolinesCTF{{...}}>\n"
                f"Write-up: <langkah-langkah teknis menyelesaikan soal>\n\n"
                f"Ingat, *semua bagian di atas wajib ada*, dan jangan ubah nilai kategori/topik/tingkat yang sudah ditentukan."
                f"---file:{suggested_file}---\n"
                f"<isi file>\n"
                f"---\n"
                f"Jika tidak perlu file, jangan tampilkan bagian tersebut."
            )
            prompt_used = task_prompt

        system_messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah pembuat soal CTF profesional. Buat satu soal lengkap berbahasa Indonesia:\n"
                    "Format:\nKategori: <...>\nTopik: <...>\nTingkat Kesulitan: <...>\nSoal: <...>\nHint: <...>\n"
                    "Nilai: <...>\nCtf: <...>\nWrite-up: <...>\n"
                    "Jika ada file pendukung:\n---file:<nama_file>---\n<isi file>\n---\n"
                    "Jika tidak ada file, kosongkan bagian tersebut."
                )
            },
            {
                "role": "system",
                "content": (
                    f"Format soal CTF HARUS mengikuti pola di bawah ini secara PERSIS, TANPA tambahan penjelasan atau pengantar.\n"
                    f"Gunakan Bahasa Indonesia. Jika tidak sesuai format, hasil akan DITOLAK:\n\n"
                    f"Kategori: <kategori>\n"
                    f"Topik: <topik>\n"
                    f"Tingkat Kesulitan: <mudah/sedang/sulit>\n"
                    f"Soal: <deskripsi>\n"
                    f"Hint: <petunjuk>\n"
                    f"Nilai: <angka skor>\n"
                    f"Ctf: PolinesCTF{{...}}\n"
                    f"Write-up: <langkah-langkah teknis>\n"
                    f"---file:<nama_file>---\n<isi file>\n---\n\n"
                    f"Contoh:\nKategori: Web\nTopik: SQL Injection\nTingkat Kesulitan: mudah\nSoal: [...]"
                )
            }
        ]

        if pendekatan == "Bahasa Sederhana":
            system_messages.append({"role": "system", "content": "Prompt menggunakan bahasa sehari-hari, tapi hasilkan soal CTF yang utuh dan valid."})
        elif pendekatan == "Keyword-Based":
            system_messages.append({"role": "system", "content": "Prompt berupa keyword. Kamu harus tetap membuat soal CTF lengkap berdasarkan itu."})
        elif pendekatan == "Interrogative":
            system_messages.append({"role": "system", "content": "Prompt berupa pertanyaan. Jawaban harus tetap berupa soal CTF."})
        elif pendekatan == "Minimal Token":
            system_messages.append({"role": "system", "content": "Prompt sangat pendek. Kamu harus tetap buat soal CTF sesuai keyword."})
        elif pendekatan == "Structured Prompt":
            system_messages.append({"role": "system", "content": "Prompt sudah terstruktur. Buat soal CTF dengan format rapi dan jelas."})

        data = {
            "model": "deepseek-chat",
            "messages": system_messages + [{"role": "user", "content": task_prompt}],
            "temperature": 0.15,  # lebih deterministik
            "top_p": 0.9,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.1,
            "max_tokens": 2200
        }

        try:
            start_time = time.time()
            response = None

            for attempt in range(3):
                try:
                    response = requests.post(API_URL, json=data, headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    })
                    if response.status_code == 200:
                        break
                    else:
                        print(f"[Retry {attempt + 1}] Status: {response.status_code}")
                except Exception as e:
                    print(f"[Retry {attempt + 1}] Exception: {str(e)}")

            end_time = time.time()
            duration = end_time - start_time

            if response.status_code != 200:
                error = f"API Error: {response.status_code}"
                flash(error, "danger")
            else:
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

                output = result.strip()
                flash("Soal berhasil dihasilkan!", "success")

                new_entry = GeneratedQuestion(
                    kategori=kategori,
                    topik=topik,
                    prompt=prompt_used,
                    response=output,
                    filename=filename,
                    tingkat=tingkat,
                    duration=duration
                )
                db.session.add(new_entry)
                db.session.commit()
        except Exception as e:
            error = f"Exception: {str(e)}"
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
            "topik": item.topik,
            "prompt": item.prompt,
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
            "Topik": item.topik,
            "Prompt": item.prompt,
            "Response": item.response,
            "File": item.filename,
            "Durasi (detik)": item.duration,
            "Waktu Dibuat": item.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(rows)

    export_folder = os.path.join(current_app.root_path, "exports")
    os.makedirs(export_folder, exist_ok=True)
    export_path = os.path.join(export_folder, "history_soal_ctf.xlsx")
    df.to_excel(export_path, index=False)

    return send_from_directory(export_folder, "history_soal_ctf.xlsx", as_attachment=True)
