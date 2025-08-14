from PIL import Image
from pdf2image import convert_from_path
import os
from PyPDF4 import PdfFileMerger

import zipfile

from FunctionalScripts import editPng

ouput_directory = "Local storage of images\\"



def merge_pdf(arrayPath,nameFile):
    merger = PdfFileMerger()
    for pdf_file in arrayPath:
        # Append PDF files
        merger.append(pdf_file)

    # Write out the merged PDF file_list
    merger.write(nameFile+".pdf")
    merger.close()
def create_zip(files, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            # Get the base name of the file
            base_name = os.path.basename(file)
            # Add the file to the ZIP
            zipf.write(file, arcname=base_name)

    #return zip_filename


# convert .png to .pdf (שדרוג קטן, לא חובה)
def png_to_pdf(sourcePath):
    out = os.path.splitext(sourcePath)[0] + ".pdf"
    with Image.open(sourcePath) as png:
        png.convert('RGB').save(out)
    return out

# Convert .pdf to .png and crop the begin and the end of the page
def pdf_to_png(pathSource, pathDest, dpi=150, margin_top=150, margin_bottom=150):
    # ודא שתיקיית היעד קיימת
    os.makedirs(pathDest, exist_ok=True)

    # רינדור תמונות מה-PDF – מהיר ויעיל יותר
    pages = convert_from_path(pathSource, dpi=dpi, fmt='png', thread_count=2)

    paths = []
    base = os.path.splitext(os.path.basename(pathSource))[0]

    for i, page in enumerate(pages, start=1):
        width, height = page.size

        # חיתוך שוליים בטוח לפי גובה הדף
        top = min(margin_top, height)
        bottom = min(margin_bottom, max(0, height - top))
        crop_box = (0, top, width, height - bottom)
        page = page.crop(crop_box)

        out = os.path.join(pathDest, f"{base}_page_{i}.png")
        page.save(out, 'PNG')

        # ניקוי רווחים בסוף התמונה (כמו שהיה אצלך)
        editPng.cropSpaceEndPng(out)

        paths.append(out)

    return paths

def delete_files(paths):
    for i in range(len(paths)):
        os.remove(paths[i])

def combineFiles(arrayPath,output_path):
    # Load the images
    images = [Image.open(path) for path in arrayPath]
    # Determine the total size of the combined image
    total_width = max(img.size[0] for img in images)
    total_height = sum(img.size[1] for img in images)

    # Create a new image to store the combined images
    result = Image.new("RGBA", (total_width, total_height))

    # Paste each image into the result
    y_offset = 0
    for img in images:
        result.paste(img, (0, y_offset))
        y_offset += img.size[1]

    # Save the result
    result.save(output_path+'.png')
    return output_path+'.png'


def getFilesPaths():
    return ouput_directory,os.listdir(ouput_directory)

def getOutputDirectoryPath():
    return ouput_directory


def zipPdf(array_paths,zip_path):
    create_zip(array_paths, zip_path)
