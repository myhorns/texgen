#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Usage: generate the Latex source from an text input file
    python texgen.py input.txt -o output.tex
'''

import argparse
import re
import os
import glob
import copy

LatexIndentation = [
    "",                                     # no indentation
    "    ",                                 # 1-stop 
    "        ",                             # 2-stop
    "            ",                         # 3-stop
    "                ",                     # 4-stop
    "                    ",                 # 5-stop
    "                        ",             # 6-stop
    "                            ",         # 7-stop
    "                                ",     # 8-stop
    "                                    ", # 9-stop
    "                                        " # 10-stop
]

def countIndentations(textLine, indentationMark):
    indentation = 0
    while (textLine.startswith(indentationMark)):
        indentation += 1
        textLine = textLine[len(indentationMark):]
    return (indentation, textLine)

def extractChapterIndex(line):
    # assume the chapter index follows this pattern: "Chapter xx: ..."
    chapterTag = re.search("Chapter \\d+:", line).group()
    if len(chapterTag) > 0:
        indexTag = re.search("\\d+", chapterTag).group()
        if len(indexTag) > 0:
            return int(indexTag)
    return 0

# Apply Latex syntax of boldface to ALLCAPs.
# ## BUG ALERT ##
# This method will cause undetermined behavior if the matches form the
# regex returns duplicated strings.
def boldfaceAllCaps(str):
    # regex = \b[A-Z]{2,}\b
    # \b is word boundary
    # this matches any A-Z substring whose length is at least 2
    allcaps = re.findall("\\b[A-Z]{2,}\\b", str)
    for ac in allcaps:
        str = str.replace(ac, "\\textbf{" + ac + "}")
    return str

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
    f.write(LatexIndentation[indent] + "\\centerline{" + line + "}\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "\\end{LARGE}\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "\\end{frame}\n")
    f.write("\n")


def generateSlideRegular(f, title, paragraphs, paraSubBullets, indent, chIndex, slideIndex):
    # to ensure there is not too much text, or too many text lines  on each slide, we set 
    # the following limits:
    # 1. A maximum of **220** characters in the paragraphs, and
    # 2. No more than two paragraphs (level-1 bullets).
    # 3. No more than one level-1 bullet if this one has level-2 bullets. 
    charLimit = 220
    paraLimit = 2

    subSlidesParagraphs = []
    isSumarySlide = summarySlideKeyword in title

    # check if a graphics file exists for this slide.
    # - a summary slide does not have an image
    # - a regular slide should have one (and only one) image
    # - if a graphic name for a regular slide is missing, use a placeholder image instead.
    graphicsName = "Gen{0:02d}_{1:02d}".format(chIndex, slideIndex)
    if not isSumarySlide and graphicsName not in allGraphicsFiles:
        graphicsName = placeholderGraphicsFile

    if isSumarySlide:
        # this is a slide without graphics. the rules defined above does not apply.
        # simply generate one slide for all paragraphs
        generateSlideSummary(f, title, paragraphs, indent)
    else:
        # devide the paragraphs into multiple sub slides
        charCount = 0
        paraCount = 0
        parasPerSubSlide = []
        #for para in paragraphs:
        for i in range(0, len(paragraphs)):
            para = paragraphs[i]
            subBullets = paraSubBullets[i]

            if len(subBullets) > 0:
                # apply rule #3
                if len(parasPerSubSlide) > 0: 
                    # previous left-over paragraphs need to be placed in an 
                    # individual sub slide.
                    subSlidesParagraphs.append(copy.deepcopy(parasPerSubSlide))
                    parasPerSubSlide.clear()
                # assign a new sub slide to this current paragraph
                parasPerSubSlide.append((para, subBullets))
                subSlidesParagraphs.append(copy.deepcopy(parasPerSubSlide))
                parasPerSubSlide.clear()
                charCount = 0
                paraCount = 0
            else:
                # apply rule #1 & #2
                paraLen = len(para)
                for sb in subBullets:
                    paraLen += len(sb)
                if (paraCount >= paraLimit or charCount + paraLen >= charLimit) and len(parasPerSubSlide) > 0:
                    subSlidesParagraphs.append(copy.deepcopy(parasPerSubSlide))
                    parasPerSubSlide.clear()
                    charCount = 0
                    paraCount = 0
                parasPerSubSlide.append((para, subBullets))
                charCount += paraLen
                paraCount += 1
        # add the last sub slide
        if len(parasPerSubSlide) > 0:
            subSlidesParagraphs.append(parasPerSubSlide)
        generateSubSlidesRegular(f, title, graphicsName, subSlidesParagraphs, indent, chIndex, slideIndex)


def generateSlideSummary(f, title, paragraphs, indent):
    # write a slide with title only (no bullets)
    f.write(LatexIndentation[indent] + "\\frame {\n")
    indent += 1
    f.write(LatexIndentation[indent] + "\\frametitle{" + title + "}\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "}\n")
    f.write("\n")

    # write a new slide with the same title, and bullets to be 
    # shown one-by-one 
    f.write(LatexIndentation[indent] + "\\frame {\n")
    indent += 1
    f.write(LatexIndentation[indent] + "\\frametitle{" + title + "}\n")

    # write tags for paragraphs
    f.write(LatexIndentation[indent] + "\\begin{itemize}[<+->]\n")
    indent += 1
    for para in paragraphs:
        para = boldfaceAllCaps(para)
        f.write(LatexIndentation[indent] + "\\item " + para + "\n")
    indent  -= 1
    f.write(LatexIndentation[indent] + "\\end{itemize}\n")
    indent -= 1

    f.write(LatexIndentation[indent] + "}\n")
    f.write("\n")


def generateSubSlidesRegular(f, title, graphicsName, subSlidesParagraphics, indent, chIndex, slideIndex):
    subSlideTotal = len(subSlidesParagraphics)
    subSlideIndex = 1
    titleSuffix = ""

    if 0 == len(subSlidesParagraphics):
        # this is a slide with title and graphics only (no body text)
        f.write(LatexIndentation[indent] + "\\frame {\n")
        indent += 1
        if subSlideTotal > 1:
            titleSuffix = " ({0}/{1})".format(subSlideIndex, subSlideTotal)
        f.write(LatexIndentation[indent] + "\\frametitle{" + title + titleSuffix + "}\n")

        # write tags for graphics
        if len(graphicsName) > 0:
            f.write(LatexIndentation[indent] + "\\begin{figure}\n")
            indent += 1
            f.write(LatexIndentation[indent] + "\\includegraphics[width=1.0\\textwidth,height=0.7\\textheight,keepaspectratio]{" + graphicsName + "}\n")
            indent  -= 1
            f.write(LatexIndentation[indent] + "\\end{figure}\n")
        
        indent  -= 1
        f.write(LatexIndentation[indent] + "}\n")
        f.write("\n")
        # we're done here
        return

    for subSlideParas in subSlidesParagraphics:
        f.write(LatexIndentation[indent] + "\\frame {\n")
        indent += 1
        if subSlideTotal > 1:
            titleSuffix = " ({0}/{1})".format(subSlideIndex, subSlideTotal)
        f.write(LatexIndentation[indent] + "\\frametitle{" + title + titleSuffix + "}\n")

        # write tags for graphics
        if len(graphicsName) > 0:
            f.write(LatexIndentation[indent] + "\\begin{figure}\n")
            indent += 1
            f.write(LatexIndentation[indent] + "\\includegraphics[width=1.0\\textwidth,height=0.7\\textheight,keepaspectratio]{" + graphicsName + "}\n")
            indent  -= 1
            f.write(LatexIndentation[indent] + "\\end{figure}\n")

        # write tags for paragraphs
        if len(subSlideParas) > 0:
            charCount = 0
            smallFont = False
            # apply small font size if:
            #  1. the total chars in this slide exceeds the limit, or;
            #  2. there are level-2 bullets in this slide.
            for (para, subBullets) in subSlideParas:
                if len(subBullets) > 0:
                    smallFont = True
                    break
                charCount += len(para)
                for sb in subBullets:
                    charCount += len(sb)
            if charCount > bulletSmallFontCharLimit:
                smallFont = True
            
            if smallFont:
                f.write(LatexIndentation[indent] + "\\begin{spacing}{0.8}\n")
                indent += 1

            f.write(LatexIndentation[indent] + "\\begin{itemize}\n")
            indent += 1
            for (para, subBullets) in subSlideParas:
                # write the level-1 bullets
                f.write(LatexIndentation[indent] + "\\item " \
                    + ("{\\footnotesize " if smallFont else "") \
                    + para \
                    + ("}\n" if smallFont else "\n"))
                if len(subBullets) > 0:
                    # write the level-2 bullets
                    writeLevel2Bullets(f, indent, smallFont, subBullets)
            indent  -= 1
            f.write(LatexIndentation[indent] + "\\end{itemize}\n")
            indent -= 1

            if smallFont:
                f.write(LatexIndentation[indent] + "\\end{spacing}\n")
                indent -= 1

        f.write(LatexIndentation[indent] + "}\n")
        f.write("\n")

        subSlideIndex += 1

def writeLevel2Bullets(f, indent, smallFont, subBullets):
    indent += 1
    f.write(LatexIndentation[indent] + "\\begin{itemize}\n")
    indent += 1

    singleColumnLinesMax = 3
    if len(subBullets) <= singleColumnLinesMax:
        # if the number of level-2 bullet items is less than 3, 
        # write all the bullets in a single column
        for sb in subBullets:
            f.write(LatexIndentation[indent] + "\\item " \
            + ("{\\scriptsize " if smallFont else "") \
            + sb \
            + ("}\n" if smallFont else "\n"))
    else:
        # write all the level-2 bullets in two columns

        # the 1st column
        f.write(LatexIndentation[indent] + "\\begin{minipage}[t]{0.4\\linewidth}\n")
        indent += 1
        f.write(LatexIndentation[indent] + "\\vspace{-0.6\\baselineskip}\n")
        sbIdx = 0
        while 2 * sbIdx < len(subBullets):
            f.write(LatexIndentation[indent] + "\\item " \
                + ("{\\scriptsize " if smallFont else "") \
                + subBullets[sbIdx] \
                + ("}\n" if smallFont else "\n"))
            sbIdx += 1
        indent -= 1
        f.write(LatexIndentation[indent] + "\\end{minipage}\n")

        # the 2nd column
        f.write(LatexIndentation[indent] + "\\begin{minipage}[t]{0.4\\linewidth}\n")
        indent += 1
        f.write(LatexIndentation[indent] + "\\vspace{-0.6\\baselineskip}\n")
        while sbIdx < len(subBullets):
            f.write(LatexIndentation[indent] + "\\item " \
                + ("{\\scriptsize " if smallFont else "") \
                + subBullets[sbIdx] \
                + ("}\n" if smallFont else "\n"))
            sbIdx += 1
        indent -= 1
        f.write(LatexIndentation[indent] + "\\end{minipage}\n")

    indent -= 1
    f.write(LatexIndentation[indent] + "\\end{itemize}\n")
    indent -= 1

# params:
#  f: the file instane
#  lines: a array of tuples: (indentation, line);
#  indent: the number of indents to be added to the beginning of each LaTeX output line.
def processChapter(f, lines, indent):
    slideTitle = ""
    slideParagraphs = []  # this array holds all the level-1 bullet text on a slide
    subParagraphs = []    # this array holds all the level-2 bullet text of each level-1 text. this array needs to by deep-copied 
    subBullets = []
    chIndex = 0
    slideIndex = 0
    prevIndentation = 0
    for (indentation, line) in lines:
        line = trimTextLine(line)
        if 0 == len(line):
            # skip this line if it's empty
            continue
        if 0 == indentation:
            # this line is the chapter title
            chIndex = extractChapterIndex(line)
            # generate a separate slide with chapter name only
            generateSlideChapterTitle(f, line, indent)
        elif 1 == indentation:
            # this line is the beginning of a new slide (with slide title)
            if 2 == prevIndentation or 3 == prevIndentation:
                subParagraphs.append(copy.deepcopy(subBullets))
            if 0 != len(slideTitle):
                # we have collected slide title and slide paragraphs, now generate the slide
                generateSlideRegular(f, slideTitle, slideParagraphs, subParagraphs, indent, chIndex, slideIndex)
            # udpate the slide title for the next slide
            slideTitle = line
            # clear the slide paragraphs
            slideParagraphs.clear()
            subParagraphs.clear()
            slideIndex += 1
        elif 2 == indentation:
            # this line is a paragraph inside a slide
            if 2 == prevIndentation or 3 == prevIndentation:
                subParagraphs.append(copy.deepcopy(subBullets))
            # clear all the level-2 bullets from previous paragraph
            subBullets.clear()
            slideParagraphs.append(line)
        elif 3 == indentation:
            subBullets.append(line)

        prevIndentation = indentation

    subParagraphs.append(copy.deepcopy(subBullets))
    # generate the last slide
    if len(slideTitle) > 0:
        generateSlideRegular(f, slideTitle, slideParagraphs, subParagraphs, indent, chIndex, slideIndex)


def trimTextLine(line):
    # trim the leading chars: "1. "
    line = line[3:]

    # trim the ending New Line char: '\n'
    if line.endswith('\n'):
        line = line[:-1]
        #line.rstrip('\n')

    # get rid of non-campatible unicode chars
    line = line.replace("…", "...")

    # remove anything enclosed by [ ] 
    #
    # The greedy regex (which maximize the content enclosed by the brackets) fails
    # when there are multiple matched brackets in each line. e.g.:
    # "I want to remove all words in brackets[ like [this] and [[this]] and [[even] this]]. How about [hello world] weeeee".
    # The greedy regex will return "I want to remove all words in brackets weeeee"
    #return re.sub("\\[.*\\]", "", line).strip()
    #
    # An alternative is to use a conservative regex which minimize the content within brackets, but to
    # run the regex match/removal repeatly until the match is found
    #
    # To better deal with the extra space after brackets removal, the regex was 
    # further refined to be applied in two stages: 
    # (1) to include the succeeding whitespace if there is an opening quotation 
    #     mark ahead of the bracket. e.g. 
    #     "[some words] I will ..." --> "I will ..."
    #     --------------                - 
    #          MATCH     -->         REPLACE
    # (2) to include the proceeding whitespace immediately before the bracket, 
    #     using "\s?": a whitespace appears zero or one time. e.g.
    #     "I will [some words] go to ... " --> "I will go to ..."
    #            -------------
    #               MATCH          -->       DELETED
    # NOTE: stage 1 has to be applied before stage 2 

    condition = True
    lineLen = len(line)
    while condition:
        # stage 1
        line = re.sub("\"\[[^\[]*?\]\s", "\"", line)
        line = re.sub("“\[[^\[]*?\]\s", "“", line)
        line = re.sub("‘\[[^\[]*?\]\s", "‘", line)
        # stage 2
        line = re.sub("\\s?\\[[^\\[]*?\\]", "", line)

        if len(line) != lineLen:
            lineLen = len(line)
        else:
            line = line.strip()
            condition = False

    # replace non-ascii chars with ascii
    line = line.replace("“", "{\\textquotedblleft}")  # \textquotedblleft == ``
    line = line.replace("”", "{\\textquotedblright}") # \textquotedblright == ''
    line = line.replace("‘", "{\\textquoteleft}")
    line = line.replace("’", "{\\textquoteright}")
    #line = line.replace("\"", "\\textquotedblright ")
    line = line.replace("\"", "\symbol{34}")
    line = line.replace("'", "\symbol{39}")
    return line.strip()


def writeLatexHeading(f):
    indent = 0
    f.write("\\documentclass{beamer}\n")
    f.write("\n")
    f.write("\\geometry{paperwidth=160mm,paperheight=120mm}\n")  # increase paper size (resolution) so that small fonts are still clear
    f.write("\n")
    f.write("\\usepackage{setspace}\n")        # to adjust line spacing
    f.write("\\usepackage{graphicx}\n")
    f.write("\\graphicspath{{./figures/}}\n")
    f.write("\\DeclareGraphicsExtensions{.pdf,.jpg,.jpeg,.png}\n")
    f.write("\n")
    f.write("\\usepackage[T1]{fontenc}\n")       # use a narrower font: Computer Modern family
    f.write("\\setbeamerfont{institute}{size=\\tiny}\n")
    f.write("\n")
    f.write("\\setbeamersize{text margin left=4pt, text margin right=4pt}\n")
    f.write("\n")
    f.write("\\title{Genesis}\n")
    f.write("\\subtitle{EBCSV Summer Retreat 2018}\n")
    f.write("\\institute{Evangel Bible Church of Silicon Valley}\n")
    f.write("\n")
    f.write("\\usetheme{lucid}\n")
    f.write("\\begin{document}\n")
    f.write("\n")

    indent += 1
    f.write(LatexIndentation[indent] + "\\frame {\n")
    indent += 1
    f.write(LatexIndentation[indent] +  "\\titlepage\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "}\n")
    indent -= 1

    f.write("\n")

def writeLatexTailing(f):
    indent = 0

    # insert an empty slide at the end of the presentation
    indent += 1
    f.write(LatexIndentation[indent] + "\\begin{frame}[plain]\n")
    indent += 1
    f.write(LatexIndentation[indent] + "\\centerline{ }\n")
    indent -= 1
    f.write(LatexIndentation[indent] + "\\end{frame}\n")
    indent -= 1

    f.write("\n")
    f.write("\\end{document}\n")

# given the path of a file, extract the file name (ignore the 
# folder name and the extension), then add the file name to a
# global hash set.
#   e.g. "figures/Gen01_3.jpg" -> "Gen01_3"
#   e.g. "figures/Gen01_4.png" -> "Gen01_4"
def collectFiles(filepaths):
    for path in filepaths:
        filename_w_ext = os.path.basename(path)
        filename, file_extension = os.path.splitext(filename_w_ext)
        allGraphicsFiles.add(filename)

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

# collect all the graphics files
graphicsFolder = "figures/"
allGraphicsFiles = set()
collectFiles(glob.glob(graphicsFolder + "*.jpg"))
collectFiles(glob.glob(graphicsFolder + "*.jpeg"))
collectFiles(glob.glob(graphicsFolder + "*.png"))

summarySlideKeyword = "Takeaway"
placeholderGraphicsFile = "placeholder"

bulletSmallFontCharLimit = 185

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
            #printChapter(chapterLines)
            chapterLines.clear()

        chapterLines.append((indentation, textLine))
        prevIndentation = indentation
        
# process the last chapter
if len(chapterLines) > 0:
    processChapter(fout, chapterLines, texBodyIndent)
    #printChapter(chapterLines)

writeLatexTailing(fout)
fout.close()
