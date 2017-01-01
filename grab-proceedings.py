#!/usr/bin/python

import sys, re, os, errno, requests, urllib
from BeautifulSoup import BeautifulSoup

BASEURL = "http://papers.nips.cc"

linkre = re.compile('([0-9]+)\.pdf')


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else: 
            raise


def lencheck(element, length=1):
    if len(element) < length:
        raise RuntimeError, "parse error %s" % (str(element))


def get_year_page(year):
    bpreq = requests.get(BASEURL)
    if not bpreq:
        raise RuntimeError, "could not download %s" % (BASEURL)
    soup = BeautifulSoup(bpreq.text)
    years = soup.findAll(u"a", 
                attrs={u"href": re.compile(r'.book.*?%i.*' % (year))})
    if len(years) < 1:
        raise RuntimeError, "year %i not found" % (year)
    yearurl = BASEURL + years[0][u"href"]
    yearpage = requests.get(yearurl)
    if not yearpage:
        raise RuntimeError, "could not download %s" % (yearurl)
    return yearpage.text


def get_all_papers_on_yearpage(yearpage):
    soup = BeautifulSoup(yearpage)
    links = soup.findAll(u"a")
    paperre = re.compile(r'(.*?paper.([0-9]+).*)')
    results = []
    for l in links:
        ret = paperre.match(l[u"href"])
        if ret:
            results.append(ret.groups())
    return results


def strip_slashes(x):
    return re.sub(r'/', '', x)


def download_pdf_from_paperpage(url):
    paperpage = requests.get(BASEURL + url)
    if not paperpage:
        raise RuntimeError, "could not download %s" % (BASEURL + url)

    fnret = re.search(r'.*?paper.([0-9]+.*)', url)
    if not fnret:
        raise RuntimeError, "error parsing paper url '%s'" % (url)

    basename = fnret.group(1)
    basename = strip_slashes(basename)
    pdf_file = basename + ".pdf"
    bib_file = basename + ".bib"

    soup = BeautifulSoup(paperpage.text)
    pdfurls = soup.findAll(u"meta", attrs={u"name": u"citation_pdf_url"})
    lencheck(pdfurls)
    pdfurl = pdfurls[0][u"content"]
    biburls = soup.findAll(u"a", attrs={u"href":
                                        re.compile(r'bibtex$')})
    lencheck(biburls)
    biburl = BASEURL + biburls[0][u"href"]
    print " downloading %s ..." % (basename),
    sys.stdout.flush()
    if not os.path.exists(pdf_file):
        urllib.urlretrieve(pdfurl, pdf_file)
    print "pdf",
    sys.stdout.flush()
    if not os.path.exists(bib_file):
        urllib.urlretrieve(biburl, bib_file)
    print "bib."
    sys.stdout.flush()


def download_single_paper(year, paper_number):
    yearpage = get_year_page(year)
    for url, pn in get_all_papers_on_yearpage(yearpage):
        try:
            pn = int(pn)
        except ValueError:
            raise RuntimeError, "error parsing yearpage"
        if pn == paper_number:
            download_pdf_from_paperpage(url)
            return
    raise RuntimeError, "paper %i not found" % (paper_number)


def download_all_papers(year):
    yearpage = get_year_page(year)
    for url, paper_number in get_all_papers_on_yearpage(yearpage):
        download_pdf_from_paperpage(url)


if __name__=='__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, \
        """usage: %s <year> [paper_number]
       if no paper number is supplied, all of that year
       will be downloaded""" \
                % (sys.argv[0])
        sys.exit(1)
    
    paper_number = None
    year = None
    if len(sys.argv) >= 2:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print >>sys.stderr, "could not parse year"
            sys.exit(1)
    if len(sys.argv) >= 3:
        try:
            paper_number = int(sys.argv[2])
        except ValueError:
            print >>sys.stderr, "could not parse paper number"
            sys.exit(1)
   
    print "Downloading from %i proceedings" % (year),
    if paper_number is not None:
        print "paper no. %i" % (paper_number)
        download_single_paper(year, paper_number)
    else:
        print "all papers"
        download_all_papers(year)

