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

LatexIndentation = [
    "",                        # no indentation
    "    ",                    # 1-stop 
    "        ",                # 2-stop
    "            ",            # 3-stop
    "                ",        # 4-stop
    "                    "     # 5-stop
]

def countIndentations(textLine, indentationMark):
    indentation = 0
    while (textLine.startswith(indentationMark)):
        indentation += 1
        textLine = textLine[len(indentationMark):]
    return (indentation, textLine)


# for debug use
def printChapter(lines):
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


def generateSlideChapterTitle(f, line, indent):
    f.write(LatexIndentation[indent] + "\\begin{frame}[plain]\n")
    indent += 1
    f.write(LatexIndentation[indent] + "\\begin{LARGE}\n")
    indent += 1
    f.write(LatexIndentation[indent] + line + "\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "\\end{LARGE}\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "\\end{frame}\n")
    f.write("\n")


def generateSlideRegular(f, title, paragraphs, indent):
    f.write(LatexIndentation[indent] + "\\frame {\n")
    indent += 1
    f.write(LatexIndentation[indent] + "\\frametitle{" + title + "}\n")
    f.write(LatexIndentation[indent] + "\\begin{itemize}\n")
    indent += 1
    for para in paragraphs:
        f.write(LatexIndentation[indent] + "\\item " + para + "\n")
    indent  -= 1
    f.write(LatexIndentation[indent] + "\\end{itemize}\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "}\n")
    f.write("\n")


def processChapter(f, lines, indent):
    slideTitle = ""
    slideParagraphs = []
    for (indentation, line) in lines:
        line = trimTextLine(line)
        if 0 == len(line):
            # skip this line if it's empty
            continue
        if 0 == indentation:
            # this line is the chapter title
            generateSlideChapterTitle(f, line, indent)
        elif 1 == indentation:
            # this line is the beginning of a new slide (with slide title)
            if 0 != len(slideTitle):
                # we have collected slide title and slide paragraphs, now generate the slide
                generateSlideRegular(f, slideTitle, slideParagraphs, indent)
            # udpate the slide title for the next slide
            slideTitle = line
            # clear the slide paragraphs
            slideParagraphs.clear()
        elif 2 == indentation:
            # this line is a paragraph inside a slide
            slideParagraphs.append(line)
    # generate the last slide
    if len(slideTitle) > 0:
        generateSlideRegular(f, slideTitle, slideParagraphs, indent)


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

fout = open(args.o, 'w')
writeLatexHeading(fout)


chapterLines = []
prevIndentation = 0
indentationMark = "   "
texBodyIndent = 1
with open(args.filename) as fin:
    for line in fin:
        if len(line) == 0:
            continue
        (indentation, textLine) = countIndentations(line, indentationMark)

        if prevIndentation > 0 and indentation == 0:
            # this is the beginning of a new chapter.
            # process the current chapter before adding a new text line
            processChapter(fout, chapterLines, texBodyIndent)
            chapterLines.clear()

        chapterLines.append((indentation, textLine))
        prevIndentation = indentation
        
# process the last chapter
if len(chapterLines) > 0:
    processChapter(fout, chapterLines, texBodyIndent)


#fout.write("Hello world!\n")
writeLatexTailing(fout)
fout.close()
