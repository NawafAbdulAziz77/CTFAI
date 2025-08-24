import os
from flask import send_from_directory

def load(app):
    @app.route("/ads.txt")
    def ads_txt():
        static_dir = os.path.join(app.root_path, "static")
        return send_from_directory(static_dir, "ads.txt")
