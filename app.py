from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile, os, zipfile, time, uuid, logging

# לוודא שמודלי Tesseract זמינים גם אם ENV לא נטען מסיבה כלשהי
os.environ.setdefault('TESSDATA_PREFIX', '/usr/share/tesseract-ocr/5/tessdata/')

# ייבוא הקוד שלך
import Main
from FunctionalScripts import functionalFiles
from Logicalscripts import logicalList

app = Flask(__name__)
CORS(app)  # לאפשר קריאות מהאתר הסטטי שלך

# לוגים קריאים בקונסול של Render
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@app.get("/")
def root():
    return {"ok": True, "service": "mixwer", "endpoint": "/process"}

@app.get("/ping")
def ping():
    return {"pong": True}

@app.before_request
def _log_start():
    rid = uuid.uuid4().hex[:8]
    request.environ['RID'] = rid
    app.logger.info(f"[{rid}] {request.method} {request.path}")

@app.after_request
def _add_id(resp):
    rid = request.environ.get('RID')
    if rid:
        resp.headers['X-Request-ID'] = rid
    return resp

@app.post("/process")
def process():
    t0 = time.time()
    rid = request.environ.get('RID', 'noid')

    # תמיכה גם במפתח 'file' יחיד וגם 'files' מרובים
    files = request.files.getlist("files")
    if not files:
        f = request.files.get("file")
        if f:
            files = [f]
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
            safe_name = os.path.basename(f.filename) or "upload.pdf"
            p = os.path.join(workdir, safe_name)
            f.save(p)
            input_paths.append(p)

        app.logger.info(f"[{rid}] starting Main.main on {len(input_paths)} file(s): { [os.path.basename(p) for p in input_paths] }")

        # להריץ את הצינור הראשי
        try:
            pdf_paths, ok = Main.main(input_paths)
            app.logger.info(f"[{rid}] Main.main finished ok={ok} -> {pdf_paths}")
        except Exception as e:
            app.logger.exception(f"[{rid}] exception while processing")
            return jsonify({"error": f"processing exception: {e}"}), 500

        if not ok or not pdf_paths:
            app.logger.error(f"[{rid}] FAILED: no outputs from pipeline")
            return jsonify({"error": "processing failed"}), 500

        # לארוז ל־ZIP ולהחזיר
        zip_path = os.path.join(workdir, "results.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in pdf_paths:
                z.write(p, arcname=os.path.basename(p))

        dt = time.time() - t0
        app.logger.info(f"[{rid}] done: {len(pdf_paths)} pdf(s) in {dt:.1f}s")
        resp = send_file(zip_path, as_attachment=True, download_name="mixwer_results.zip")
        resp.headers['X-Request-ID'] = rid
        return resp

if __name__ == "__main__":
    # להרצה מקומית בלבד
    app.run(host="0.0.0.0", port=8000)
