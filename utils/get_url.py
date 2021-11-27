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



#Nimmt Buchstabe als String entgegen und gibt Liste von Urls von Filialen in Orten mit dem Buchstaben zurück. Link: https://www.sparkasse.de/service/filialsuche.html
# Mit der proxy variable kann eine IP-Addresse angegeben werden, welche das zugreifen auf Websiten ermöglicht, falls die eigene IP geblockt sein sollte.
def findUrlSp(letter,proxy=None):
    #Sammeln von HTML Daten. Link: https://requests.readthedocs.io/en/master/
    response = requests.get("https://www.sparkasse.de/filialen/" + letter + ".html",proxy)
    #Parse den HTML Inhalt der Seite mit der bs4 Bibliothek um damit arbeiten zu können. link: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
    soup = BeautifulSoup(response.text, "html.parser")
    #Durchsuche die nun vorbereitete HTML Datei nach einem spezifischen HTML Tag. Ergenis ist eine Liste mit allen Matches.
    href = soup.findAll('a','object-link grey-link')
    #Liste zum Sammeln der kommenden Daten
    url_list = np.array([""]*len(href),dtype="<U165")
    for z in range(len(href)):
            #Speichern der URLS welche später verwendet werden.
            url_list[z] = "https://www.sparkasse.de/filialen/" + str(href[z]["href"])
    return url_list

#Die Funktionen für SPK/VR sind an sich immer ziemlich ähnlich.
def findUrlVr(letter,proxy=None):
    response = requests.get("https://www.vr.de/service/filialen-a-z/" + letter + ".html",proxy)
    soup = BeautifulSoup(response.text, "html.parser")
    href = soup.findAll('a','more-info')
    #dtype gibt an wie viel Speicher für das Array eingeplant werden muss, wenn dtype kleiner als die maximale Länge eines Datenpunktes welchen du im Array speichern möchtest ist, gehen Teilinformationen verloren.
    url_list = np.array([""] * len(href),dtype="U166")
    cnt = 0
    for z in href:
            try:
                if z.get('href')[:28] == "https://www.vr.de/standorte/":
                    url_list[cnt] = z.get('href')
                    cnt += 1
            except:
                continue
    return url_list[:cnt]



#Von SPL/VR Banken werden alle Filialen, welche online in der alpahabetischen Auflistung stehen, in eine TXT Datei geschrieben.
#Das mache ich um das Main-Programm kürzer zu halten, dort müssen dann nur noch die Zeilen eingelesen werden und ich spare mir die Zeit bei jeder Ausführung auf das Erstellen der URL Listen zu warten.
def urlToTxt(input,proxy=None):
    if "Vr" in input:
        file = open("UrlVrFiliale.txt","w+")
        #das alphabet is auf der Website so formatiert
        alphabet=["a","ba-bm","bn-Bz","c","d","e","f","g","ha-hm","hn-hz","i","j","k","l","m","n","o","p","q","r","sa-sm","sn-sz","t","u","v","wa-wm","wn-wz","x","y","z"]
        for i in alphabet:
            #Gibt Array an URLs zu einem Buchstaben zurück
            arr = findUrlVr(i,proxy)
            for url in arr:
                #Jede URL wird in eine Zeile geschrieben
                file.write("{}\n".format(url))
    elif "Sp" in input:
        file = open("UrlSpFiliale.txt","w+")
        alphabet=["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
        for i in alphabet:
            arr = findUrlSp(i,proxy)
            for url in arr:
                file.write("{}\n".format(url))
    else:
        return 0
    file.close()
    return 0




#Auf Wikipedia sind zu allen Instituten der Sparkasse Einträge auf denen zur Website des Instituts verlinkt wird.
def getInstitutUrlListWiki():
    response = requests.get("https://de.wikipedia.org/wiki/Liste_der_Sparkassen_in_Deutschland")
    soup = BeautifulSoup(response.text, "html.parser")
    #Filter für Hyperlinks in Tabelle
    href = soup.findAll('td')
    cnt = 0
    for i in href:
        try:
            #Wenn Hyperlinks Sparkasse enthalten, dann schreibe in Liste
            if "Sparkasse" in i.find('a')["href"] or "sparkasse" in i.find('a')["href"]:
                href[cnt] = "https://de.wikipedia.org{}".format(i.find('a')["href"])
                cnt += 1
        except:
            0

    return href[:cnt]

#Die Hyperlinks aus der obigen Funktion werden hier aufgerufen, die HTML Daten der resultierenden Seite werden geparst und HREF zum Institut herausgeschrieben.
#Zusäztlich erstelle ich direkt eine Liste für die Entgeltinformationen, da bei den Sparkassen die URL immer den selben Pfad enthält.
def findUrlSpInstitut(array):

    file = open("UrlSpEntgelt.txt","w+")
    file2 = open("UrlSpInstitut.txt","w+")
    cnt = 0
    cntarr = len(array)
    for url in array:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        #Ich filtere nach dem "a" Tag mit den Attributen "rel" und "class" mit den jeweilingen Werten.
        content = soup.findAll('a',attrs={'rel':'nofollow','class':'external text' })[0].get('href')
        #Manchmal ist schon ein "/" vorhanden, dann wird dieses nicht nochmal ans Ende angefügt
        if content[-1:]=="/":
            file2.write(     "{}\n".format(content))
            file.write(     "{}de/home/toolbar/preise-und-hinweise.html?n=true&stref=footer\n".format(content))
        else:
            file2.write(     "{}/\n".format(content))
            file.write(     "{}/de/home/toolbar/preise-und-hinweise.html?n=true&stref=footer\n".format(content))
        cnt += 1
        print(str(cntarr-cnt) +" to go ")
    file.close()
    file2.close()
    return 0





#Bei den VR Banken geht das leider nicht so einfach, hier rufe ich alle Seiten der Filialen auf und schreibe mir so die Verlinkung raus.
#Das ist zwar uneffizient, geht aber weil ich einfach threaden kann, von der Laufzeit her klar.
def getUrl(url):
        try:
            response = requests.get(url)
        except:
            #Ggf überprüfen, da es aber von jedem Institut mehrere Filialen gibt ist die wahrscheinlichkeit, dass man ein ganzes Institut nicht mitbekommt gering.
            print("Cant connect",url)
            #traceback.print_exc()
            #print("Didnt work: ",url)
            return 1
        soup = BeautifulSoup(response.text, "html.parser")
        href = soup.findAll("span","module-linklist__title")
        try:
            for i in href:
                if i.get_text()[:4]=="http":
                    txt = i.get_text()
                    end = txt.find(".de")
                    return i.get_text()[:end+3]
        except:
            print("Failed:",url)
            return 1




list = []

def findUrlVrInstitut():
    file = open("UrlVrFiliale.txt","r")
    file2 = open("UrlVrInstitut.txt","w+")

    url_list = [0]*len( open( "UrlVrFiliale.txt").readlines())
    for i in range(len( open(   "UrlVrFiliale.txt").readlines())):
        url_list[i] = file.readline().replace('\n','')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(getUrl, url): url for url in url_list}
        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            #Wenn Fehler in der getUrl Funktion
            if result == 1:
                continue
            #Wenn das Institut noch nicht in der Liste ist
            if result not in list:
                list.append(result)
                file2.write("{0}\n".format(result))
                #print(len(list))
    file.close()
    file2.close()
    return 0





if __name__ == "__main__":

    #Setup
    try:
        dec=int(input(" For URLs of SPK branches press '1' \n For URLs of VR branches press '2' \n For URLs of SPK institute and remuneration press '3' \n For URLs of VR institute press '4' \n" ))
    except ValueError:
        print("Invalid input")


    if dec == 1:
        os.system("cls")
        print("Starting Sp")
        start = time.time()
        urlToTxt("Sp",proxy=None)
        end = time.time()
        print("Runtime was {} seconds".format( round(end-start,1) ))


    elif dec == 2:
        os.system("cls")
        print("Starting Vr")
        start = time.time()
        urlToTxt("Sp",proxy=None)
        end = time.time()
        print("Runtime was {} seconds".format( round(end-start,1) ))

    elif dec == 3:
        os.system("cls")
        print("Starting Sp Institut")
        start = time.time()
        findUrlSpInstitut(getInstitutUrlListWiki())
        end = time.time()
        print("Runtime was {} seconds".format( round(end-start,1) ))
    elif dec == 4:
        os.system("cls")
        print("Starting Vr Institut")
        start = time.time()
        findUrlVrInstitut()
        end = time.time()
        print("Runtime was {} seconds".format( round(end-start,1) ))

    else:
        os.system("cls")
        print("Invalid input")
