'''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("square", type=int,
                    help="display a square of a given number")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity")
args = parser.parse_args()
answer = args.square**2
if args.verbose:
    print ("the square of {} equals {}".format(args.square, answer))
else:
    print (answer)
'''

import argparse
import re


def countIndentations(textLine, indentationMark):
    indentation = 0
    while (textLine.startswith(indentationMark)):
        indentation += 1
        textLine = textLine[len(indentationMark):]
    return (indentation, textLine)


def generateChapter(lines):
    for (indentation, line) in lines:
        printline = ""
        for i in range(indentation):
            printline += "--"
        line = trimTextLine(line)
        if len(line) > 0:
            printline += line
            print(printline)
    #print(lines)
    print("============================")


def trimTextLine(line):
    # trim the leading chars: "1. "
    line = line[3:]

    # trim the ending New Line char: '\n'
    if line.endswith('\n'):
        line = line[:-1]
        #line.rstrip('\n')

    # remove anything enclosed by [ ] 
    return re.sub("\\[.*?\\]", "", line)
    #return line

def writeLatexHeading(f):
    f.write("\\documentclass{beamer}\n")
    f.write("\n")
    f.write("\\title{Genesis}\n")
    f.write("\\subtitle{EBCSV Summer Retreat 2018}\n")
    f.write("\n")
    f.write("\\usetheme{lucid}\n")
    f.write("\\begin{document}\n")
    f.write("\n")
    f.write("    \\frame {\n")
    f.write("        \\titlepage\n")
    f.write("    }\n")
    f.write("\n")

def writeLatexTailing(f):
    f.write("\\end{document}\n")


parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str,
                    help="the filename of the input text file")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity")
parser.add_argument("-o", type=str,
                    help="the filename of output LaTeX file")
args = parser.parse_args()

#print ("The input text file: {}".format(args.filename))
#print ("The output LaTeX file: {}".format(args.o))

f = open(args.o, 'w')
writeLatexHeading(f)

'''
chapterLines = []
prevIndentation = 0
indentationMark = "   "
with open(args.filename) as f:
    for line in f:
        if len(line) == 0:
            continue
        (indentation, textLine) = countIndentations(line, indentationMark)

        if prevIndentation > 0 and indentation == 0:
            # this is the beginning of a new chapter.
            # process the current chapter before adding a new text line
            generateChapter(chapterLines)
            chapterLines.clear()

        chapterLines.append((indentation, textLine))
        prevIndentation = indentation
        
# process the last chapter
if len(chapterLines) > 0:
    generateChapter(chapterLines)
'''

f.write("Hello world!\n")
writeLatexTailing(f)
f.close()
