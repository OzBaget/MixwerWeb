from Logicalscripts import *
from FunctionalScripts import *
import os

successPdf = []
answersId = []

# ברירת מחדל—ב-API אנחנו ממילא נדרוס את זה לנתיב זמני
output_directory = "Local storage of images" + os.sep


def blendPdf():
    """
    מריץ את כל הפייפליין על path_original_pdf (מוגדר בתוך main),
    ומחזיר נתיב-בסיס (ללא .pdf) של הקובץ הסופי.
    """
    # Convert .pdf to page .png
    path_originial_pages_png = functionalFiles.pdf_to_png(path_original_pdf, output_directory)

    # (אופציונלי) איחוד עמודים לתוצאה ביניים
    functionalFiles.combineFiles(path_originial_pages_png, os.path.join(output_directory, 'result'))

    # הפקת שאלות
    arrayOfQuestions, numQ = exportPng.export_questions(path_originial_pages_png, output_directory)
    print("Success export Q\n")

    # הפקת תשובות לכל שאלה
    for pathQ in arrayOfQuestions:
        global answersId
        answersId = logicalList.findNumAnswers(pathQ)
        exportPng.export_answers(pathQ, answersId, output_directory)
        print(f"Success export A in Q {pathQ}\n")

    # חיתוך תשובות
    logicalPng.cropAnswers()
    print("Success Cropping\n")

    # ערבוב תשובות
    mixAnswers = logicalList.mixfiles()
    print("Success Mixing\n")

    # הרכבת דפי PNG סופיים
    paths_of_pages = logicalPng.combineFilestoPages(mixAnswers, output_directory)
    print("Success final pages\n")

    # הוספת דף תשובות
    answer_page_path, path_answers = logicalPng.createAnswersPage(mixAnswers)
    paths_of_pages = paths_of_pages + answer_page_path
    print("Success answer page\n")

    # המרת PNG ל-PDF
    paths_of_pages_pdf = [functionalFiles.png_to_pdf(p) for p in paths_of_pages]
    print("Success convert pages to .pdf\n")

    # יצירת שם קובץ סופי—נייד לכל מערכת
    base, ext = os.path.splitext(os.path.basename(path_original_pdf))
    final_dir = os.path.join("Final PDFs")
    os.makedirs(final_dir, exist_ok=True)
    ouput_pdf_path = os.path.join(final_dir, f"{base} מעורבל")

    # מיזוג לכל PDF אחד
    functionalFiles.merge_pdf(paths_of_pages_pdf, ouput_pdf_path)
    print("Success merge pages\n")

    # ניקוי קבצים זמניים
    tmp_dir, files = functionalFiles.getFilesPaths()
    functionalFiles.delete_files(tuple(os.path.join(tmp_dir, fname) for fname in files))

    return ouput_pdf_path


def main(array_paths):
    """
    מקבל רשימת נתיבי PDF, מריץ את הפייפליין לכל קובץ,
    ומחזיר (רשימת נתיבי PDF סופיים, דגל הצלחה).
    """
    global successPdf
    successPdf = []
    failPdf = []

    for pdf_file_path in array_paths:
        # הגדרת הקובץ הנוכחי כגלובלי ל-blendPdf
        global path_original_pdf
        path_original_pdf = pdf_file_path

        # שם לתצוגה/לוג
        base, ext = os.path.splitext(os.path.basename(path_original_pdf))
        fileNameEnd = f"{base} מעורבל{ext}"

        try:
            # blendPdf מחזיר נתיב בלי סיומת; כאן מוסיפים ".pdf"
            successPdf.append(blendPdf() + ".pdf")
            print(f"SUCCESS {fileNameEnd}")
        except Exception as e:
            print(f"NOT  SUCCESS {fileNameEnd} ERROR: {e}")
            failPdf.append(pdf_file_path)

    return successPdf, successPdf != []


if __name__ == "__main__":
    main([])  # הפעלה ידנית (לא בשימוש בשרת)


def get_ouput_directory():
    return output_directory
