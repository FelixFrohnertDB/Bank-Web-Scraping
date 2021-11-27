import traceback
import os
import tabula
import csv


#Gehe in das Verzeichnis "filesSp" und wandel dort alle PDF Dat in csv Dat um. Die Struktur im Programm ist notwenidg, da es selten zu fehlern beim umwandeln kommt.
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
