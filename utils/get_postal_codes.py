import requests
from requests import get
from bs4 import BeautifulSoup
import concurrent.futures
import urllib.request
import numpy as np
import time
import pandas as pd
import json
import os
import traceback
from openpyxl import workbook
from openpyxl import load_workbook




#Nimmt URL und gibt Liste mit bestimmten Datenpunkten der Seite zurück
def get_data_sp(url,proxy=None):
    dataArraySp = np.array(["","",0,0,0,0],dtype="<U132")
    try:
        response = requests.get(url,proxy)
    except:
        response = False
    if str(response) != "<Response [200]>":
        # Aus dem Print bekommt man relativ viel Info raus. Link: https://de.wikipedia.org/wiki/HTTP-Statuscode
        print("{0}This url didnt time work: {1}".format(str(response),url) )
        return np.array(["","",0,0,0,0])
    soup = BeautifulSoup(response.text, "html.parser")
    try:
        # Suche nach dem Skript Tag, gehe an bestimmte Stelle vom Array, lade JSON Objekt
        data = json.loads(str(soup.findAll('script')[7])[35:-9])
    except:
        #Manchmal sind die Daten an einer anderen Stelle gespeichert..
        data = json.loads(str(soup.findAll('script')[9])[35:-9])
    #Name Institut
    dataArraySp[0] = data[0]["name"]
    #Name Filiale, manchmal nicht vorhanden
    try:
        dataArraySp[1] = data[1]["name"]
    except:
        #Teilweise steht der Name der Filiale nicht in dem Textblock aus dem ich die restlichen Informationen ziehe.
        dataArraySp[1] = data[0]["name"]
    #PLZ
    dataArraySp[2] = data[0]["address"]["postalCode"]
    try:
        #longitude
        dataArraySp[3] = data[0]["geo"]["longitude "]
        #latitude
        dataArraySp[4] = data[0]["geo"]["latitude"]
    except:
        #Falls nicht dort Mitte von DE, kam aber noch nicht vor
        dataArraySp[3] = 10.447683
        #latitude
        dataArraySp[4] = 51.163361
    try:
        #Die Blz ist in einem Button zur Sparkasse versteckt, deshalb suche ich nach der Klasse mit allen "data-blz" Attributen
        dataArraySp[5] = soup.find_all("button", attrs = {"data-blz":True})[0]["data-blz"]
    except:
        dataArraySp[5] = 0

    return dataArraySp




def get_data_vr(url,proxy=None):
    dataArrayVr = np.array([0,"",0], dtype="<U140")
    try:
        response = requests.get(url,proxy)
    except:
        response = False
    if str(response) != "<Response [200]>":
        print("{1} this url didnt work: {2}".format(str(response),url) )
        return np.array([0,"",0])
    soup = BeautifulSoup(response.text, "html.parser")
    data = soup.findAll('div', 'text')
    #Institut
    dataArrayVr[0] = str(data[0])[str(data[0]).find('BLZ')+5:str(data[0]).find('BLZ')+13]
    #Filiale
    dataArrayVr[1] = data[0].find('h1', 'branch-office-header__headline').get_text()
    #PLZ
    dataArrayVr[2] = data[0].findAll('span')[1].get_text()
    #Koordinaten sind leider nicht in den HTML Inf. enthalten, werden aber in der Excel nachgeschlagen.
    return dataArrayVr

#Hauptprogramm SPK. Kann sein, dass du geblockt wirst, durch das Threading werden viele Anfragen gestellt. In dem Fall nimmst du entweder Proxy oder wechselst zum 2.0 Progromm.
def mainsp(proxy=None):
    #Datei mit URLS öffnen
    file = open("UrlSpFiliale.txt","r")
    #Workbook öffnen
    wb = load_workbook("Postalcode Tool.xlsm", read_only=False, keep_vba=True)
    #Zweite Seite laden
    sheet = wb[wb.sheetnames[1]]
    #Ein paar Werte sind hardcoded in der Excel weil die nicht online stehen, deshalb starte ich erst bei Row 6
    cnt = 6

    #Liste mit URLS erstellen
    url_list = [0]*len( open( "UrlSpFiliale.txt").readlines())
    for i in range(len( open(   "UrlSpFiliale.txt").readlines())):
        url_list[i] = file.readline().replace('\n','')

    #Threading initiieren
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Das ist vielleicht ein bisschen schwer zu verstehen, ich würde mir das hier anschauen: https://docs.python.org/3/library/concurrent.futures.html
        # Folgendes passiert: Ich habe eine for-Schleife über die Liste der URLS. Jede URL gebe ich in die Auswertungsfunktion und speicher die Ausgabe in dem future_to_url objekt ab.
        # Die verschiedenen executor instanzen bearbeiten die Probleme parallel mit einer festen Anzahl an Threads die gleichzeitig laufen.
        # Weil ich viel Zeit mit warten auf Server verbringe spart das super viel Zeit.
        future_to_url = {executor.submit(get_data_sp, url, proxy): url for url in url_list}
        #Hier werte ich dann immer die threads die fertig sind aus und schriebe die Ergebnisse in die Excel.
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                sheet.cell(row = cnt, column = 1).value = future.result()[0]
                sheet.cell(row = cnt, column = 2).value = future.result()[1]
                sheet.cell(row = cnt, column = 3).value = float(future.result()[2])
                sheet.cell(row = cnt, column = 5).value = float(future.result()[3])
                sheet.cell(row = cnt, column = 4).value = float(future.result()[4])
                sheet.cell(row = cnt, column = 7).value = float(future.result()[5])
                cnt+=1
            except:
                traceback.print_exc()
                continue

            if "00" in str(cnt):
                print(len(url_list)-cnt)


    file.close()
    wb.save("Postalcode Tool.xlsm")
    return 0

#Non Thread Version
def mainsp2(proxy=None):
    file = open("UrlSpFiliale.txt","r")
    cnt = 6
    wb = load_workbook("Postalcode Tool.xlsm", read_only=False, keep_vba=True)
    sheet = wb[wb.sheetnames[1]]
    lenUrl = len( open(   "UrlSpFiliale.txt").readlines())
    for iter in range(lenUrl):

        data =  get_data_sp(file.readline().replace('\n',''))

        try:
            sheet.cell(row = cnt, column = 1).value = data[0]
            sheet.cell(row = cnt, column = 2).value = data[1]
            sheet.cell(row = cnt, column = 3).value = float(data[2])
            sheet.cell(row = cnt, column = 5).value = float(data[3])
            sheet.cell(row = cnt, column = 4).value = float(data[4])
            #BLZ
            sheet.cell(row = cnt, column = 7).value = float(data[5])
            cnt+=1

        except:
            traceback.print_exc()
            continue
        print(lenUrl-cnt)
        if "00" in str(cnt):
            print("save")
            #Zwischenstand speichern
            wb.save("Postalcode Tool.xlsm")


    wb.save("Postalcode Tool.xlsm")
    file.close()
    return 0




#########
#Bei den VR Banken hatte ich mit Threading bis jetzt keine Probleme, ggf. muss hier auch eine 2.0 Version erstellt werden.
def mainvr(proxy=None):
    file = open("UrlVrFiliale.txt","r")
    wb = load_workbook("Postalcode Tool.xlsm", read_only=False, keep_vba=True)
    sheet = wb[wb.sheetnames[2]]
    cnt = 2
    url_list = [0]*len( open( "UrlVrFiliale.txt").readlines())
    for i in range(len( open(   "UrlVrFiliale.txt").readlines())):
        url_list[i] = file.readline().replace('\n','')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(get_data_vr, url, proxy): url for url in url_list}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                sheet.cell(row = cnt, column = 7).value = float(future.result()[0])
                sheet.cell(row = cnt, column = 2).value = future.result()[1]
                sheet.cell(row = cnt, column = 3).value = float(future.result()[2])
                cnt += 1

            except Exception:
                  traceback.print_exc()
                  continue
            #print(len(url_list)-cnt)
    file.close()
    wb.save("Postalcode Tool.xlsm")
    return 0
#print(mainvr())


if __name__ == "__main__":


    try:
        file1 = open("UrlVrFiliale.txt","r")
        file2= open("UrlSpFiliale.txt","r")
        print("URL files found")
        input=int(input(" \n Choose input: \n For postal codes of SPK: '1' \n For postal codes of VR: '2' \n For postal codes of SPK without threading: '3' \n  "))
    except ValueError:
        input = 6
        print("No URL files found.")

    if input == 1:

        os.system("cls")
        print("Starting SPK")
        start = time.time()
        mainsp()
        end = time.time()
        print("Runtime mainsp {} seconds".format( round(end-start,1) ))

    elif input == 2:
        os.system("cls")
        print("Starting VR")
        start = time.time()
        mainvr()
        end = time.time()
        print("Runtime mainvr {} seconds".format( round(end-start,1) ))


    elif input == 3:
        os.system("cls")
        print("Starting SPK without threading")
        start = time.time()
        mainsp2()
        end = time.time()
        print("Runtime mainsp {} seconds".format(round(end-start,1)))



    else:
        os.system("cls")
        print("Invalid input")
