import os
import tabula


def make_csv(file_dir):
    os.chdir(file_dir)
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.pdf')]

    for file in files:
        try:
            tabula.convert_into(file, file.replace(".pdf",".csv"), output_format="csv", pages='all')
        except:
            print(file,"did not work")
    return 0

