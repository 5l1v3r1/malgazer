# Script to calculate the entropy of a file already calculated with the batch script.
import argparse
import sqlite3
from library.files import FileObject
from library.plots import ScatterPlot
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from library.entropy import RunningEntropy

import numpy
import time


def main():
    # Capture the running time
    start_time = time.time()

    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Calculates the entropy of a malware file.')
    parser.add_argument('Malware',
                        help='The malware SQL file to analyze.')
    parser.add_argument("-w", "--window",
                        help="Window size, in bytes, for running entropy."
                             "Multiple windows can be identified as comma "
                             "separated values without spaces."
                             "", default='256', type=str, required=False)
    parser.add_argument("-preskip", "--plotrunningentropyskip",
                        help="Skip this number of bytes in running entropy "
                             "value plot for compression."
                             "", default=1, type=int, required=False)
    parser.add_argument("-prefilename", "--plotrunningentropyfilename",
                        help="The file name of the output file for a running "
                             "entropy plot (html).",
                        default="malgazer.html",
                        required=False)
    parser.add_argument("-a", "--anomaly", action='store_true',
                        help="Enable anomaly detection."
                             "", required=False)
    parser.add_argument("-c", "--contamination", type=float, default=0.1,
                        help="Outlier contamination factor."
                             "", required=False)
    parser.add_argument("-l", "--lofneighbors", type=int, default=300,
                        help="Local outlier factor neighbors."
                             "", required=False)

    args = parser.parse_args()

    # Find window sizes
    plot_windows = None
    if args.window:
        plot_windows = args.window.split(',')
        plot_windows = [x.strip() for x in plot_windows]
        plot_windows = [int(x) for x in plot_windows]

    f = FileObject(args.Malware)
    running_entropy = f.runningentropy

    # This will be our HTML output
    html = list()
    html.append("<h1>File Metadata</h1>")
    html.append("<b>Sample:</b> {0}".format(args.Malware))
    html.append("<br><b>File Type:</b> {0}".format(f.filetype))
    html.append("<br><b>File Size:</b> {0:,}".format(f.file_size))
    html.append("<br><b>MD5:</b> {0}".format(f.md5))
    html.append("<br><b>SHA256:</b> {0}".format(f.sha256))
    html.append("<h1>Plots</h1>")

    # Iterate through window sizes...
    for window in plot_windows:
        print('\tCalculating window {0:,}'.format(window))
        rwe = f.running_entropy(window)
        n = numpy.array(rwe)

        # Add annotations for file types
        annotations = list()

        # Parsed file processing...
        if f.parsedfile:
            # Annotations for PE files...
            if f.parsedfile['type'] == 'pefile':
                for section in f.parsedfile['sections']:
                    annotation = dict()
                    section_offset = f.parsedfile['sections'][section]['offset']
                    section_length = f.parsedfile['sections'][section]['length']
                    annotation['text'] = "{0} ({1:,}-{2:,})".format(section, section_offset, section_offset+section_length-1)
                    annotation['x'] = section_offset
                    annotation['y'] = rwe[section_offset]
                    annotations.append(annotation)

        # Setup the x axis as location information
        x = [i for i in range(0, len(rwe))
             if i % int(args.plotrunningentropyskip) == 0]
        # Setup the y axis values
        y = [round(rwe[i], 6)
             for i in range(0, len(rwe))
             if i % int(args.plotrunningentropyskip) == 0]

        # Generate the plot...
        title = ("Malgazer - Running Entropy Window Size {0} Bytes"
                 .format(window))
        xtitle = "Byte Location"
        ytitle = "Entropy Value"
        datatitle = ["Entropy"]
        mode = ["lines", "markers"]
        x_vals = [x]
        y_vals = [y]

        myplot = ScatterPlot(x=x_vals, datatitle=datatitle, xtitle=xtitle,
                             y=y_vals, ytitle=ytitle,
                             plottitle=title, mode=mode,
                             text=annotations)
        html.append(myplot.plot_div())

    # Output the HTML...
    with open(args.plotrunningentropyfilename, 'w') as m:
        m.write("<HTML><TITLE>Malgazer</TITLE><BODY>")
        for h in html:
            m.write(h)
        m.write("</BODY></HTML>")

    # Print the running time...
    print()
    print("Total running time: {0:.6f} seconds"
          .format(round(time.time() - start_time, 6)))
    print()


if __name__ == "__main__":
    main()