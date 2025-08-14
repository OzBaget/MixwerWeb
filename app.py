from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile, os, zipfile

# ייבוא הקוד שלך
import Main
from FunctionalScripts import functionalFiles
from Logicalscripts import logicalList

app = Flask(__name__)
CORS(app)  # לאפשר קריאות מהאתר הסטטי שלך

@app.post("/process")
def process():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "no files provided"}), 400

    with tempfile.TemporaryDirectory() as workdir:
        outdir = os.path.join(workdir, "out")
        os.makedirs(outdir, exist_ok=True)

        # להפנות את מודולי הפרויקט לתיקיית פלט זמנית (Cross-platform)
        Main.output_directory = outdir + os.sep
        functionalFiles.ouput_directory = outdir + os.sep
        logicalList.ouput_directory = outdir + os.sep

        # לשמור את הקבצים שהועלו
        input_paths = []
        for f in files:
            safe_name = os.path.basename(f.filename)
            p = os.path.join(workdir, safe_name)
            f.save(p)
            input_paths.append(p)

        # להריץ את הצינור הראשי
        try:
            pdf_paths, ok = Main.main(input_paths)
        except Exception as e:
            return jsonify({"error": f"processing exception: {e}"}), 500

        if not ok or not pdf_paths:
            return jsonify({"error": "processing failed"}), 500

        # לארוז ל־ZIP ולהחזיר
        zip_path = os.path.join(workdir, "results.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in pdf_paths:
                z.write(p, arcname=os.path.basename(p))
        return send_file(zip_path, as_attachment=True, download_name="mixwer_results.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
