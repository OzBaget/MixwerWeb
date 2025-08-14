import os, re, time
import cv2

Qsign = "שאלה מספר"

from Logicalscripts import logicalList
from FunctionalScripts import functionalBox
from FunctionalScripts import functionalFiles

# === עזר ללוגים/התקדמות ===
def log(msg):
    print(str(msg), flush=True)

def pct(done, total):
    return int((done / max(total, 1)) * 100)

# ──────────────────────────────────────────────────────────────────────────────
# הוצאת שאלות (עם לוגי התקדמות)
def export_questions(array_path, ouput_directory):
    HEIGHT_BEGIN_Q = 140
    questions_paths = []
    general_num_Q = 1
    first_Q = False

    # Pre-pass: הערכת סה"כ שאלות ע"פ כמות המופעים של "שאלה מספר" בדפים
    total_q_est = 0
    per_page_counts = []
    for img in array_path:
        fw = logicalList.find_first_words(img, [Qsign], False)
        c = fw['text'].count(Qsign)
        per_page_counts.append(c)
        total_q_est += c
    log(f"[Q] expected markers (rough): {total_q_est} across {len(array_path)} page(s)")

    processed_q = 0  # נספר שאלות "אמיתיות" (לא כולל 'continue')

    for page_idx, img in enumerate(array_path, start=1):
        lastQ = False
        page_num_Q = 1
        open_img = cv2.imread(img)
        first_words = logicalList.find_first_words(img, [Qsign], False)

        if first_words['text'].count(Qsign) == 0:  # אין "שאלה מספר" בעמוד
            if not first_Q:
                continue
            else:
                lastQ = True

        while not lastQ:
            first_Q = True
            coordCurrent = functionalBox.wordToBox(Qsign, first_words, [Qsign], page_num_Q)

            if page_num_Q < first_words['text'].count(Qsign):
                coordNext = functionalBox.wordToBox(Qsign, first_words, [Qsign], page_num_Q + 1)
                cropped_image = open_img[coordCurrent[1]:coordNext[1] - 10, 0:open_img.shape[1]]
            else:
                lastQ = True  # last q in the page
                if coordCurrent[1] > 10:
                    cropped_image = open_img[coordCurrent[1] - 10:open_img.shape[0], 0:open_img.shape[1]]
                else:
                    cropped_image = open_img[coordCurrent[1]:open_img.shape[0], 0:open_img.shape[1]]

            out_path = os.path.join(ouput_directory, f"question_{general_num_Q}.png")
            cv2.imwrite(out_path, cropped_image)
            questions_paths.append(out_path)

            processed_q += 1
            log(f"[Q] page {page_idx}: saved question #{general_num_Q}  "
                f"progress {processed_q}/{total_q_est} ({pct(processed_q, total_q_est)}%)")

            general_num_Q += 1
            page_num_Q += 1

        # טיפול בקטע המשך למעלה של העמוד הבא
        if (first_words['text'].count(Qsign) != 0 and
            functionalBox.wordToBox(Qsign, first_words, [Qsign], 1)[1] > HEIGHT_BEGIN_Q and
            general_num_Q > page_num_Q) or first_words['text'].count(Qsign) == 0:

            if first_words['text'].count(Qsign) != 0:
                coordCurrent = functionalBox.wordToBox(Qsign, first_words, [Qsign], 1)
            else:
                coordCurrent = [0, open_img.shape[0], 0, 0]

            cropped_image = open_img[0:coordCurrent[1], 0:open_img.shape[1]]
            cont_path = os.path.join(ouput_directory, f"continue_question_{general_num_Q - page_num_Q}.png")
            cv2.imwrite(cont_path, cropped_image)

            merge_png = [
                os.path.join(ouput_directory, f"question_{general_num_Q - page_num_Q}.png"),
                cont_path
            ]
            functionalFiles.combineFiles(
                merge_png,
                os.path.join(ouput_directory, f"question_{general_num_Q - page_num_Q}")
            )
            log(f"[Q] merged continue for question #{general_num_Q - page_num_Q}")

    total_out = general_num_Q - 1
    log(f"[Q] finished: produced {total_out} question image(s)")
    return questions_paths, total_out

# ──────────────────────────────────────────────────────────────────────────────
# הוצאת תשובות לשאלה (עם לוגי התקדמות)
def export_answers(pathRoot, answersId, ouput_directory):
    image = cv2.imread(pathRoot)
    first_words = logicalList.find_first_words(pathRoot, answersId, False, True)

    # חילוץ מספר השאלה מתוך השם "question_<N>.png" בצורה עמידה
    halfPath = os.path.basename(pathRoot)
    m = re.search(r'question_(\d+)', halfPath)
    numQ = int(m.group(1)) if m else -1

    coordNext = []
    ans_total = max(len(answersId) - 1, 1)  # בלי הפריט הראשון (כותרת/סימן)
    ans_done = 0

    log(f"[A] Q{numQ}: extracting {ans_total} answer block(s)")

    try:
        for charAns in answersId[1:]:
            if charAns == answersId[1]:
                coordNext = [0, 10, 0, 0]
            coordCurrent = coordNext

            # האם זו לא התשובה האחרונה
            if charAns != answersId[-1]:
                try:
                    coordNext = functionalBox.wordToBox(charAns, first_words, answersId)
                except:
                    # Crop the image from the begin of the last A, in order to make OCR read better
                    cropped_image = image[coordCurrent[1] - 10:image.shape[0], 0:image.shape[1]]
                    cv2.imwrite(pathRoot, cropped_image)
                    image = cv2.imread(pathRoot)
                    first_words = logicalList.find_first_words(pathRoot, answersId, False)
                    coordNext = functionalBox.wordToBox(charAns, first_words, answersId)
            else:
                coordNext = [image.shape[1], image.shape[0], image.shape[1], image.shape[0]]

            cropped_image = image[coordCurrent[1] - 10:coordNext[1] - 10, 0:image.shape[1]]

            try:
                if charAns != answersId[1]:
                    ans_index = answersId.index(charAns) - 1  # 1..N
                    pathC = os.path.join(ouput_directory, f"question_{numQ}_answer_{ans_index}.png")
                    ans_done += 1
                    log(f"[A] Q{numQ}: saved answer {ans_done}/{ans_total} "
                        f"({pct(ans_done, ans_total)}%) -> answer_{ans_index}.png")
                else:
                    pathC = os.path.join(ouput_directory, f"question_{numQ}_prefix.png")
                    log(f"[A] Q{numQ}: saved prefix block")
                cv2.imwrite(pathC, cropped_image)
            except Exception:
                # fallback: שמירת פס לבן בגובה 30 פיקסלים
                safe_path = os.path.join(ouput_directory, f"question_{numQ}_answer_err.png")
                cv2.imwrite(safe_path, image[0:30, 0:image.shape[1]])
                log(f"[A] Q{numQ}: ERROR saving block (replaced with white strip)")
    except Exception:
        log(f"[A] Q{numQ}: ERROR while slicing answers – will fill with white")

    log(f"[A] Q{numQ}: done {ans_done}/{ans_total} ({pct(ans_done, ans_total)}%)")
