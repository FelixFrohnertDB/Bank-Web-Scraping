import requests
from requests import get
from bs4 import BeautifulSoup
import concurrent.futures
import urllib.request
import numpy as np


# Takes letter as string and returns list of urls of stores in locations with the letter. Link:
# https://www.sparkasse.de/service/filialsuche.html The proxy variable can be used to specify an IP address which
# allows access to websites if the own IP is blocked.

def get_url_sp_letter(letter, proxy=None):
    response = requests.get("https://www.sparkasse.de/filialen/" + letter + ".html", proxy)
    # Parse the HTML content of the page with the bs4 library to work with it. Doc:
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/
    soup = BeautifulSoup(response.text, "html.parser")
    # Search the now prepared HTML file for a specific HTML tag. Result is a list       with all matches.
    href = soup.findAll('a', 'object-link grey-link')
    # List to collect the upcoming data
    url_list = np.array([""] * len(href), dtype="<U165")
    for z in range(len(href)):
        # Save the URLS which will be used later.
        url_list[z] = "https://www.sparkasse.de/filialen/" + str(href[z]["href"])
    return url_list


def get_url_vr_letter(letter, proxy=None):
    response = requests.get("https://www.vr.de/service/filialen-a-z/" + letter + ".html", proxy)
    soup = BeautifulSoup(response.text, "html.parser")
    href = soup.findAll('a', 'more-info')
    url_list = np.array([""] * len(href), dtype="U166")
    cnt = 0
    for z in href:
        try:
            if z.get('href')[:28] == "https://www.vr.de/standorte/":
                url_list[cnt] = z.get('href')
                cnt += 1
        except:
            continue
    return url_list[:cnt]


# From SPL/VR banks all branches, which are online in the alphabetic listing, are written into a TXT file. I do this
# to keep the main program shorter, then only the lines must be read in and I save the time to wait for the creation
# of the URL lists at each execution.

def get_url_sp(save_as, proxy):
    file = open(save_as, "w+")
    alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
                "u", "v", "w", "x", "y", "z"]
    for i in alphabet:
        arr = get_url_sp_letter(i, proxy)
        for url in arr:
            file.write("{}\n".format(url))
    file.close()
    return 1


def get_url_vr(save_as, proxy):
    file = open(save_as, "w+")
    alphabet = ["a", "ba-bm", "bn-Bz", "c", "d", "e", "f", "g", "ha-hm", "hn-hz", "i", "j", "k", "l", "m", "n", "o",
                "p", "q", "r", "sa-sm", "sn-sz", "t", "u", "v", "wa-wm", "wn-wz", "x", "y", "z"]
    for i in alphabet:
        arr = get_url_vr_letter(i, proxy)
        for url in arr:
            file.write("{}\n".format(url))
    file.close()
    return 1


# On Wikipedia there are entries for all institutions of the Sparkasse with links to the website of the institution.
def get_url_sp_institute_temp():
    response = requests.get("https://de.wikipedia.org/wiki/Liste_der_Sparkassen_in_Deutschland")
    soup = BeautifulSoup(response.text, "html.parser")
    href = soup.findAll('td')
    cnt = 0
    for i in href:
        try:
            if "Sparkasse" in i.find('a')["href"] or "sparkasse" in i.find('a')["href"]:
                href[cnt] = "https://de.wikipedia.org{}".format(i.find('a')["href"])
                cnt += 1
        except:
            0

    return href[:cnt]


# The hyperlinks from the above function are called here, the HTML data of the resulting page is parsed and HREF to
# the institute is written out. In addition, I directly create a list for the charge information, since with the
# savings banks the URL always contains the same path.

def get_url_sp_institute(url_arr, save_as_entgelt, save_as_institute):
    file = open(save_as_entgelt, "w+")
    file2 = open(save_as_institute, "w+")
    cnt = 0
    cntarr = len(url_arr)
    for url in url_arr:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        # Ich filtere nach dem "a" Tag mit den Attributen "rel" und "class" mit den jeweilingen Werten.
        content = soup.findAll('a', attrs={'rel': 'nofollow', 'class': 'external text'})[0].get('href')
        # Manchmal ist schon ein "/" vorhanden, dann wird dieses nicht nochmal ans Ende angefügt
        if content[-1:] == "/":
            file2.write("{}\n".format(content))
            file.write("{}de/home/toolbar/preise-und-hinweise.html?n=true&stref=footer\n".format(content))
        else:
            file2.write("{}/\n".format(content))
            file.write("{}/de/home/toolbar/preise-und-hinweise.html?n=true&stref=footer\n".format(content))
        cnt += 1
        print(str(cntarr - cnt) + " to go ")
    file.close()
    file2.close()
    return 0


# With the VR banks this does not go unfortunately so simply, here I call all sides of the branches and write me so
# the linking out. This is inefficient, but goes because I can simply thread, clear from the runtime.
def get_url_vr_institute_temp(url):
    try:
        response = requests.get(url)
    except:
        # Ggf überprüfen, da es aber von jedem Institut mehrere Filialen gibt ist die wahrscheinlichkeit,
        # dass man ein ganzes Institut nicht mitbekommt gering.
        print("Cant connect", url)
        # traceback.print_exc()
        # print("Didnt work: ",url)
        return 1
    soup = BeautifulSoup(response.text, "html.parser")
    href = soup.findAll("span", "module-linklist__title")
    try:
        for i in href:
            if i.get_text()[:4] == "http":
                txt = i.get_text()
                end = txt.find(".de")
                return i.get_text()[:end + 3]
    except:
        print("Failed:", url)
        return 1


list = []


def get_url_vr_institute(url_filiale_txt, save_as_institute):
    file = open(url_filiale_txt, "r")
    file2 = open(save_as_institute, "w+")

    url_list = [0] * len(open().readlines())
    for i in range(len(open(url_filiale_txt).readlines())):
        url_list[i] = file.readline().replace('\n', '')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(get_url_vr_institute_temp, url): url for url in url_list}
        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            if result == 1:
                continue
            if result not in list:
                list.append(result)
                file2.write("{0}\n".format(result))

    file.close()
    file2.close()
    return 0
