import traceback
import os
import tabula
import csv


#Go to the directory "filesSp" and convert all PDF files into csv files. The structure in the program is necessary, because it rarely comes to errors when converting.
def makecsv():
    os.chdir("filesSp")
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.pdf')]

    for file in files:
        try:
            tabula.convert_into(file, file.replace(".pdf",".csv"), output_format="csv", pages='all')
        except:
            print(file,"did not work")
    return 0
#print(makecsv())
