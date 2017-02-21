#!/usr/bin/python

import argparse
import csv
import subprocess
import urllib
import glob
from os import path
from datetime import datetime, timedelta

myscript = path.realpath(__file__)
dirname = path.dirname(__file__)
basename = path.basename(__file__)

def parse_args():

    parser = argparse.ArgumentParser(description='Convert flrtvc.ksh output to html')
    parser.add_argument('-b', '--batch',  action="store_true", help="Parse all files")
    parser.add_argument('-s', '--skip-download', action="store_true", help="Skip downloading 'apar.csv'")
    parser.add_argument('-d', action="store", default='./', help="Directory containing files for mass processing")
    parser.add_argument('-o', '--output', action="store", default="/tmp/flrt2html", help="Output directory, default is /tmp/flrt2html")
    parser.add_argument('-l', '--lslpp', action="store", help="'lslpp -Lqc' output")
    parser.add_argument('-e', '--emgr', action="store", help="'emgr -lv3' output")
    parser.add_argument('--debug', action="store_true")

    return parser.parse_args()

def download_csv():

    print "Checking apar.csv"
    if (not path.isfile("apar.csv")
            or datetime.fromtimestamp(path.getctime("apar.csv")) < datetime.now() - timedelta(days=5)):
        print "apar.csv is more than 5 days old or missing"
        print "Downloading fresh one from IBM"
        urllib.urlretrieve('http://www-304.ibm.com/webapp/set2/flrt/doc?page=aparCSV', "apar.csv")


def main():

    args = parse_args()

    if args.debug:
        print args

    if args.skip_download:
        print("Skipping download of apar.csv")
    else:
        download_csv()

    listing = [file.strip("_lslpp.info") for file in glob.glob('*_lslpp.info')]

    for hostname in listing:
        lslpp = hostname + "_lslpp.info"
        emgr = hostname + "_emgr.info"
        htmlname = hostname + ".html"
        # run IBM's script, -s to skip download as we checked and downloaded the file above.

        kshout, ksherr = subprocess.Popen(['./flrtvc.ksh', '-s', '-l', lslpp, '-e', emgr],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()

        assert len(ksherr) == 0, "flrvc.ksh stderr it non-empty, aborting"

        kshcsv = csv.reader(kshout.splitlines(), delimiter='|')
        csvData = list(kshcsv)

        with open(htmlname, 'w') as html:
            html.write('''<!-- Latest compiled and minified CSS -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-table/1.8.1/bootstrap-table.min.css">

        <!-- Latest compiled and minified CSS -->
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
        ''')
            html.write('<title>' + hostname + '</title>\n')
            html.write('<table class = "table table-sm table-striped table-bordered" data-toggle = "table">\n')
            r = 0
            for row in csvData:
                if r == 0:
                    html.write('\t<thead class = "thead-inverse">\n\t\t<tr>\n')
                    for col in row:
                        html.write('\t\t\t<th data-sortable="true">' + col + '</th>\n')
                    html.write('\t\t</tr>\n\t</thead>\n')
                    html.write('\t<tbody>\n')
                else:
                    html.write('\t\t<tr>\n')
                    curcol = 0
                    for col in row:
                        if curcol == 9:
                            tdclass = "bg-active"
                            if len(col) > 0:
                                score = float(col)
                                if score >= 8:
                                    tdclass = "bg-danger"
                                elif score >= 5:
                                    tdclass = "bg-warning"
                            html.write('\t\t\t<td class="' + tdclass + '">' + col + '</td>\n')
                        elif curcol == 6:
                            if "IV" in col:
                                html.write('\t\t\t<td>' + '<a href="http://www-01.ibm.com/support/docview.wss?uid=isg1'
                                           + col + '"> ' + col + '</a></td>\n')
                            elif "CVE" in col:
                                html.write('\t\t\t<td>' + '<a href="https://web.nvd.nist.gov/view/vuln/detail?vulnId='
                                           + col + '"> ' + col + '</a></td>\n')
                        elif "://" in col:
                            html.write('\t\t\t<td>' + '<a href="' + col + '"> link </a></td>\n')
                        elif "YES" in col or "hiper" in col:
                            html.write('\t\t\t<td class="bg-danger">' + col + '</td>\n')
                        else:
                            html.write('\t\t\t<td>' + col + '</td>\n')
                        curcol += 1
                    html.write('\t\t</tr>\n')

                r += 1
            html.write('\t</tbody>\n')
            html.write('</table>\n')

            html.write('''
        <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.0/jquery.min.js"></script>

        <!-- Latest compiled and minified JavaScript -->
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>

        <!-- Latest compiled and minified JavaScript -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-table/1.8.1/bootstrap-table.min.js"></script>
        ''')
        print("written " + htmlname)

    with open('index.html', 'w') as f:
        htmllist = glob.glob('*.html')

        for file in htmllist:
            f.write('<p><a href="' + file + '"> ' + file.strip('.html') + '</a></p>\n')
        print("written index.html")


if __name__ == '__main__':
    main()