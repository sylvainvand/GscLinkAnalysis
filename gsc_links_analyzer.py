@@ -0,0 +1,115 @@
#récupère les liens issus du rapport Google Search Console
#parse la liste de BL, cherche le lien vers notre site sur la page, cherche l'ancre
#en sortie un rapport avec la répartition des ancres

import csv
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import namedtuple, defaultdict
from concurrent.futures import ThreadPoolExecutor

#on commence par récupérer les URL dans le fichier CSV
def csvtolist(gsc_csv_file) :
    with open(gsc_csv_file) as f :
        f_csv = csv.reader(f)
        next(f_csv) #on vire le header
        links = [line[0] for line in f_csv]  # liste qui va contenir les BL
        return links
def linktocrawl(liste_url):
    c = 0


#Fonction NoFollow
def isNofollow(link) :
    if 'nofollow' in str(link) or 'Nofollow' in str(link) :
        return True
    return False

#check des liens internes
def is_internal(url,start_url):
    u = urlparse(url)
    s = urlparse(start_url)
    if (u.netloc == s.netloc):
        return True
    return False

#Ecriture dans un CSV de sortie
def out_csv(url_property_list) :
    with open('out.csv', 'w', newline='') as f:
        f_writer = csv.writer(f)
        header = 'domain,link,anchor,is_no_follow,internal_outlinks,external_outlinks'
        f_writer.writerow(header.split(' '))
        for url_property in url_property_list:
            f_writer.writerow(url_property)

#Transformation de la fonction en class
class myGscCrawler(object) :
    def __init__(self,linklist, domain):
        self.linklist = linklist
        self.domain = domain
        self.count_timeout = 0
        self.count_connect_error = 0
        self.result = []
        self.Url_property = namedtuple('Url_property', 'domain, link, anchor, is_no_follow, internal_outlinks, external_outlinks')
    def check_link(self, url):
        # logique de check d'URL
        try:
            print('URL to crawl :', url)
            r = requests.get(url, verify=False)
        except requests.exceptions.Timeout:
            print('soucis de TimeOut')
            self.count_timeout += 1
        except requests.exceptions.ConnectionError:
            print('Erreur de Connection')
            self.count_connect_error += 1
        soup = BeautifulSoup(r.text, 'lxml')
        ndd = urlparse(url).netloc
        internalLinks = 0
        externalLinks = 0
        if r.status_code != 200:
            # On zappe les pages mortes
            pass
        list_links_ok = []
        for l in soup.body.find_all('a'):
            if not l.has_attr('href'):
                continue
            u = urljoin(url, l['href'])
            u_parse = urlparse(u)
            if is_internal(url, l['href']):
                internalLinks += 1
            else:
                externalLinks += 1
            list_links_ok.append(l)
        for l in list_links_ok :
            u = urljoin(url, l['href'])
            u_parse = urlparse(u)
            if domain in u_parse.netloc:
                print(url, l['href'])
                self.result.append(self.Url_property(ndd, url, l.string, isNofollow(l), internalLinks, externalLinks))

    def check_all(self):
        # on va gérer le pool ici
        pool = ThreadPoolExecutor(128)
        with pool as executor :
            jobs = [executor.submit(self.check_link, url) for url in self.linklist]
        print('timeout :', self.count_timeout, 'Erreur de Connexions :', self.count_connect_error)
        return self.result


if __name__ == "__main__":
    """On réalise un crawler avec requests et bs4 pour les liens dans la GSC"""

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--domain', required = True,
                        help = "Le domaine analysé")
    parser.add_argument('-l', '--list', required = True,
                        help ="le fichier exporté depuis GSC")

    args = parser.parse_args()
    domain = args.domain
    links = csvtolist(args.list)
    test = myGscCrawler(links, domain)
    gsclinks = test.check_all()
    out_csv(gsclinks)
