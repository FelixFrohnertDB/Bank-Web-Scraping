import requests
from bs4 import BeautifulSoup
import numpy as np

import traceback
import os

import csv
import PyPDF2
import tabula
import concurrent.futures
import re


# The function to get the data from the PDF data of the SPK is not yet implemented.
# The name of the accounts and the TAG is obtained directly from the name of the PDF.
# What needs to be implemented is an alg. that reads the tables and filters out price points with the invoices in the dat.
# The terms are, as I have seen so far, not identical to those of the VRB, but it can be well oriented.


# Funktion schreibt alle Namen von Konten aus einer PDF Datei heraus und gibt zusätzlich die Seite auf der der Name
# gefunden wurde an
def get_name(file):
    end = False
    names = []
    cnt = 1
    while not end:
        res = get_name_in_pdf(file, cnt)
        if res != None:
            names.append(res)
        else:
            end = True
        cnt += 1
    return names


# Take file and return iter name of account.
def get_name_in_pdf(file, iter):
    # Öffne PDF
    pdfFileObj = open(file, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    cntFound = 0
    # iteriere über alle Seiten der PDF
    for page in range(pdfReader.numPages):
        # if page < iter-1:
        #     continue
        # Seite mit der nummer "page" laden
        pageObj = pdfReader.getPage(page)
        try:
            # Text der Seite nehmen
            text = pageObj.extractText()
        except:
            # Bei Fehler abbrechen
            return None
        # Die PDFs sind so formatiert, dass du zwischen den Begriffen "Kontobezeichnung" und "Datum" den Namen hast.
        start = text.find("Kontobezeichnung")
        end = text.find("Datum")
        # .find() gibt -1 zurück wennn nichts in dem angegebenen Objekt gefunden wurde, in diesem Fall wird mit "continue" die Schleife von Vorner, mit der nächsten Seite, fortgesetzt
        if start == -1 or end == -1:
            continue
        else:
            # "Konotobezeichnung" ist 17 Zeichen lang, manchmal ist ein ":"
            name = text[start + 17:end].strip(":")
            # Teilweise laden die Banken "___________" als Kontobezeicnung hoch, das umgehe ich hier
            if "__" in name:
                continue

            cntFound += 1
            # Ich das mache ich um sagen zu können den wievielten Namen ich aus der Datei haben möchte, geht bestimmt auch einfacher
            if cntFound == iter:
                return [name, page + 1]
    return None


# Findet den Start einer Preisangabe in der PDF Datei
def find_start(content):
    # Mit KOntoführung beginnt die Preisanagebe immer
    if "Kontoführung" in content:
        # dann muss ich jedoch zwischen verschiedenen Fällen unterscheiden
        if "onatlich" in content:
            return [content.find("onatlich") + 8, 1]
        elif "rund" in content:
            return [content.find("rund") + 4, 1]
        elif "rundpreis" in content:
            return [content.find("rundpreis") + 9, 1]
        elif "auschale" in content:
            return [content.find("auschale") + 8, 1]
            # Wenn der Preis quartalsweise angegeben ist muss ich den Preis auf monatasbasis normieren
        elif "uartal" in content:
            return [content.find("uartal") + 6, 1 / 3]
        elif "_" in content:
            return [content.find("_"), 1]
        # Manchmal wird "kein turnusmäßiges Entgelt" benutzt, dann gebe ich 0 zurück
        elif "turnusmäßiges" in content:
            return [0, 1]

    else:
        return [-1, 1]


def find_end(content, start):
    if "EUR" in content:
        return content[start:].find("EUR")
    elif "Euro" in content:
        return content[start:].find("Euro")
    elif "\u20ac" in content:
        return content[start:].find("\u20ac")
    else:
        return -1


def find_num(str):
    cont = str.replace(",", ".")
    try:
        return re.findall("\d+\.\d+", cont)[0]
    except:

        return 0


def get_content_pdf_vr(file, currentPage, nextPage):
    pdfFileObj = open(file, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    for page in range(currentPage - 1, nextPage - 2):

        pageObj = pdfReader.getPage(page)
        text = pageObj.extractText()

        start = find_start(text)
        # print("start",start)
        if start == None:
            # print("yes")
            continue
        elif start[0] == -1:
            continue
        elif start[0] == 0:
            break

        end = find_end(text, start[0])

        if end == -1:
            return float(0)

        else:
            content = text[start[0]:start[0] + end]
            return find_num(content)

    return float(998)


def get_content_csv_vr(file, currentPage, nextPage):
    if currentPage == nextPage:
        tabula.convert_into(file, "temp.csv", output_format="csv", pages="{0}-{1}".format(currentPage, nextPage))
    else:
        # Die Seite die zu einem Konto gehört in CSV umwandeln
        tabula.convert_into(file, "temp.csv", output_format="csv", pages="{0}-{1}".format(currentPage, nextPage - 1))

    with open("temp.csv", 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=' ', quotechar='|')

        for row in reader:
            content = ''.join(row)

            start = find_start(content)

            if start == None:
                continue

            elif start[0] == -1:
                continue

            end = find_end(content, start[0])
            if end == -1:
                return float(0)

            else:
                content = content[start[0]:start[0] + end]
                return find_num(content)

    return float(404)


def extract_data(file):
    # os.chdir("filesVr")
    # print("Curretnly using this file:",file)
    # if isEmpty(file.replace(".pdf",".csv")) :
    #     print("empty")
    #     return [[file.replace(".pdf",""),"",float(888)]]
    names = get_name(file)
    ret = []
    cnt = 0
    for name in names:
        if cnt + 1 == len(names):
            # Letzter Name
            content = get_content_pdf_vr(file, name[1], PyPDF2.PdfFileReader(open(file, 'rb')).numPages)
            end = PyPDF2.PdfFileReader(open(file, 'rb')).numPages
        else:
            content = get_content_pdf_vr(file, name[1], names[cnt + 1][1])
            end = names[cnt + 1][1]
        if content == float(998):
            content = get_content_csv_vr(file, name[1], end)
        pos = file.find("_")
        instName = file.replace(".pdf", "")
        ret.append([instName[:pos], name[0], content])
        cnt += 1

    return ret


def remove_element(listPdf, sheet):
    isIn = []
    end = False
    cnt = 2
    while not end:
        data = sheet["A{}".format(cnt)].value
        if data != None:
            cnt += 1
            if data in isIn:
                continue
            else:
                isIn.append(data)
        else:
            end = True
    for remPdf in isIn:
        try:
            listPdf.remove(remPdf + ".pdf")
        except:
            0

    return [listPdf, cnt]


def get_all_content(dir):
    file2 = open(dir + "/pdf_data.csv", "w+")
    os.chdir(dir)
    filesPdf = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.pdf')]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start the operations and mark each future with its URL
        data_to_content = {executor.submit(extract_data, file): file for file in filesPdf}

        for future in concurrent.futures.as_completed(data_to_content):
            try:
                result = future.result()

            except:
                print("Fehler in Auswertung")
                traceback.print_exc()
                continue
            # print("result: ",result)

            for val in result:
                file2.write("{0}\n".format(val))
    file2.close()
    return 0
