from Logicalscripts import *
from FunctionalScripts import *
import os, time, traceback

successPdf = []
answersId = []

# ברירת מחדל—ב-API אנחנו ממילא נדרוס את זה לנתיב זמני
output_directory = "Local storage of images" + os.sep

# === עזר ללוגים ===
def log(msg):
    # הדפסה מיידית ללוגים של Render
    print(str(msg), flush=True)

def t():  # time now
    return time.time()


def blendPdf():
    """
    מריץ את כל הפייפליין על path_original_pdf (מוגדר בתוך main),
    ומחזיר נתיב-בסיס (ללא .pdf) של הקובץ הסופי.
    """
    fname = os.path.basename(path_original_pdf)
    log(f"[START] {fname}")
    t0 = t()

    # 1) המרת PDF -> PNG
    try:
        log("[1] pdf_to_png start")
        path_originial_pages_png = functionalFiles.pdf_to_png(path_original_pdf, output_directory)
        log(f"[1] done: pages={len(path_originial_pages_png)} in {t()-t0:.2f}s")
    except Exception:
        log("[1] ERROR in pdf_to_png\n" + traceback.format_exc())
        raise

    # 2) איחוד עמודים (אופציונלי)
    try:
        t2 = t(); log("[2] combineFiles start")
        functionalFiles.combineFiles(path_originial_pages_png, os.path.join(output_directory, 'result'))
        log(f"[2] done in {t()-t2:.2f}s")
    except Exception:
        log("[2] ERROR in combineFiles\n" + traceback.format_exc())
        raise

    # 3) הפקת שאלות
    try:
        t3 = t(); log("[3] export_questions start")
        arrayOfQuestions, numQ = exportPng.export_questions(path_originial_pages_png, output_directory)
        log(f"[3] done: numQ={numQ} in {t()-t3:.2f}s")
    except Exception:
        log("[3] ERROR in export_questions\n" + traceback.format_exc())
        raise

    # 4) הפקת תשובות לכל שאלה
    try:
        t4 = t(); log("[4] export_answers per question start")
        for pathQ in arrayOfQuestions:
            global answersId
            answersId = logicalList.findNumAnswers(pathQ)
            exportPng.export_answers(pathQ, answersId, output_directory)
            log(f"[4] answers for {os.path.basename(pathQ)} -> {answersId}")
        log(f"[4] done in {t()-t4:.2f}s")
    except Exception:
        log("[4] ERROR in export_answers\n" + traceback.format_exc())
        raise

    # 5) חיתוך תשובות
    try:
        t5 = t(); log("[5] cropAnswers start")
        logicalPng.cropAnswers()
        log(f"[5] done in {t()-t5:.2f}s")
    except Exception:
        log("[5] ERROR in cropAnswers\n" + traceback.format_exc())
        raise

    # 6) ערבוב תשובות
    try:
        t6 = t(); log("[6] mixfiles start")
        mixAnswers = logicalList.mixfiles()
        log(f"[6] done: groups={len(mixAnswers)} in {t()-t6:.2f}s")
    except Exception:
        log("[6] ERROR in mixfiles\n" + traceback.format_exc())
        raise

    # 7) בניית דפי PNG
    try:
        t7 = t(); log("[7] combineFilestoPages start")
        paths_of_pages = logicalPng.combineFilestoPages(mixAnswers, output_directory)
        log(f"[7] done: pages={len(paths_of_pages)} in {t()-t7:.2f}s")
    except Exception:
        log("[7] ERROR in combineFilestoPages\n" + traceback.format_exc())
        raise

    # 8) הוספת דף תשובות
    try:
        t8 = t(); log("[8] createAnswersPage start")
        answer_page_path, path_answers = logicalPng.createAnswersPage(mixAnswers)
        paths_of_pages = paths_of_pages + answer_page_path
        log(f"[8] done: +{len(answer_page_path)} page(s) in {t()-t8:.2f}s")
    except Exception:
        log("[8] ERROR in createAnswersPage\n" + traceback.format_exc())
        raise

    # 9) PNG -> PDF
    try:
        t9 = t(); log("[9] png_to_pdf start")
        paths_of_pages_pdf = [functionalFiles.png_to_pdf(p) for p in paths_of_pages]
        log(f"[9] done: pdf_pages={len(paths_of_pages_pdf)} in {t()-t9:.2f}s")
    except Exception:
        log("[9] ERROR in png_to_pdf\n" + traceback.format_exc())
        raise

    # 10) מיזוג ל-PDF סופי
    try:
        base, ext = os.path.splitext(os.path.basename(path_original_pdf))
        final_dir = os.path.join("Final PDFs")
        os.makedirs(final_dir, exist_ok=True)
        ouput_pdf_path = os.path.join(final_dir, f"{base} מעורבל")

        t10 = t(); log("[10] merge_pdf start")
        functionalFiles.merge_pdf(paths_of_pages_pdf, ouput_pdf_path)
        log(f"[10] done in {t()-t10:.2f}s")
    except Exception:
        log("[10] ERROR in merge_pdf\n" + traceback.format_exc())
        raise

    # 11) ניקוי קבצים זמניים
    try:
        t11 = t(); log("[11] cleanup temp files start")
        tmp_dir, files = functionalFiles.getFilesPaths()
        functionalFiles.delete_files(tuple(os.path.join(tmp_dir, fname) for fname in files))
        log(f"[11] cleanup done in {t()-t11:.2f}s")
    except Exception:
        log("[11] WARNING: cleanup failed\n" + traceback.format_exc())

    log(f"[END] {fname} total {t()-t0:.2f}s")
    return ouput_pdf_path


def main(array_paths):
    """
    מקבל רשימת נתיבי PDF, מריץ את הפייפליין לכל קובץ,
    ומחזיר (רשימת נתיבי PDF סופיים, דגל הצלחה).
    """
    global successPdf
    successPdf = []
    failPdf = []

    log(f"[MAIN] start on {len(array_paths)} file(s)")
    for pdf_file_path in array_paths:
        # הגדרת הקובץ הנוכחי כגלובלי ל-blendPdf
        global path_original_pdf
        path_original_pdf = pdf_file_path

        # שם לתצוגה/לוג
        base, ext = os.path.splitext(os.path.basename(path_original_pdf))
        fileNameEnd = f"{base} מעורבל{ext}"

        try:
            log(f"[MAIN] processing: {os.path.basename(pdf_file_path)}")
            # blendPdf מחזיר נתיב בלי סיומת; כאן מוסיפים ".pdf"
            successPdf.append(blendPdf() + ".pdf")
            log(f"[MAIN] SUCCESS {fileNameEnd}")
        except Exception as e:
            log(f"[MAIN] NOT SUCCESS {fileNameEnd}\n{traceback.format_exc()}")
            failPdf.append(pdf_file_path)

    log(f"[MAIN] done: success={len(successPdf)} fail={len(failPdf)}")
    return successPdf, successPdf != []


if __name__ == "__main__":
    # הפעלה ידנית (לא בשימוש בשרת)
    main([])


def get_ouput_directory():
    return output_directory
