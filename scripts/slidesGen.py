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
import os
import glob
import copy

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

def extractChapterNumber(line):
    # assume the chapter number follows this pattern: "Chapter xx: ..."
    chapterTag = re.search("Chapter \\d+:", line).group()
    if len(chapterTag) > 0:
        indexTag = re.search("\\d+", chapterTag).group()
        if len(indexTag) > 0:
            return int(indexTag)
    return 0

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


def generateSlideRegular(f, title, paragraphs, indent, chIndex, slideIndex):
    # to ensure there is not too much text on each slide, we set the following limits:
    # 1. A maximum of **180** characters in the paragraphs, and
    # 2. No more than two paragraphs. 
    charLimit = 180
    paraLimit = 2

    subSlidesParagraphics = []
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
        #subSlidesParagraphics.append(paragraphs)
        generateSlideSummary(f, title, paragraphs, indent)
    else:
        # devide the paragraphs into multiple sub slides
        charCount = 0
        paraCount = 0
        parasPerSubSlide = []
        for para in paragraphs:
            paraLen = len(para)
            if (paraCount >= paraLimit or charCount + paraLen >= charLimit) and len(parasPerSubSlide) > 0:
                subSlidesParagraphics.append(copy.deepcopy(parasPerSubSlide))
                parasPerSubSlide.clear()
                charCount = 0
                paraCount = 0
            parasPerSubSlide.append(para)
            charCount += paraLen
            paraCount += 1
        # add the last sub slide
        if len(parasPerSubSlide) > 0:
            subSlidesParagraphics.append(parasPerSubSlide)
        generateSubSlidesRegular(f, title, graphicsName, subSlidesParagraphics, indent, chIndex, slideIndex)


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
    for p in subSlidesParagraphics:
        f.write(LatexIndentation[indent] + "\\frame {\n")
        indent += 1
        if subSlideTotal > 1:
            titleSuffix = " ({0}/{1})".format(subSlideIndex, subSlideTotal)
        f.write(LatexIndentation[indent] + "\\frametitle{" + title + titleSuffix + "}\n")

        # write tags for graphics
        if len(graphicsName) > 0:
            f.write(LatexIndentation[indent] + "\\begin{figure}\n")
            indent += 1
            f.write(LatexIndentation[indent] + "\\includegraphics[width=1.2\\textwidth,height=0.7\\textheight,keepaspectratio]{" + graphicsName + "}\n")
            indent  -= 1
            f.write(LatexIndentation[indent] + "\\end{figure}\n")

        # write tags for paragraphs
        if len(p) > 0:
            charCount = 0
            smallFont = False
            for para in p:
                charCount += len(para)
            if charCount > bulletSmallFontCharLimit:
                smallFont = True
            
            if smallFont:
                f.write(LatexIndentation[indent] + "\\begin{spacing}{0.8}\n")
                indent += 1

            f.write(LatexIndentation[indent] + "\\begin{itemize}\n")
            indent += 1
            for para in p:
                if smallFont:
                    f.write(LatexIndentation[indent] + "\\item {\\footnotesize " + para + "}\n")
                else:
                    f.write(LatexIndentation[indent] + "\\item " + para + "\n")
            indent  -= 1
            f.write(LatexIndentation[indent] + "\\end{itemize}\n")
            indent -= 1

            if smallFont:
                f.write(LatexIndentation[indent] + "\\end{spacing}\n")
                indent -= 1

        f.write(LatexIndentation[indent] + "}\n")
        f.write("\n")

        subSlideIndex += 1

def processChapter(f, lines, indent):
    slideTitle = ""
    slideParagraphs = []
    chIndex = 0
    slideIndex = 0
    for (indentation, line) in lines:
        line = trimTextLine(line)
        if 0 == len(line):
            # skip this line if it's empty
            continue
        if 0 == indentation:
            # this line is the chapter title
            chIndex = extractChapterNumber(line)
            generateSlideChapterTitle(f, line, indent)
        elif 1 == indentation:
            # this line is the beginning of a new slide (with slide title)
            if 0 != len(slideTitle):
                # we have collected slide title and slide paragraphs, now generate the slide
                generateSlideRegular(f, slideTitle, slideParagraphs, indent, chIndex, slideIndex)
            # udpate the slide title for the next slide
            slideTitle = line
            # clear the slide paragraphs
            slideParagraphs.clear()
            slideIndex += 1
        elif 2 == indentation:
            # this line is a paragraph inside a slide
            slideParagraphs.append(line)
    # generate the last slide
    if len(slideTitle) > 0:
        generateSlideRegular(f, slideTitle, slideParagraphs, indent, chIndex, slideIndex)


def trimTextLine(line):
    # trim the leading chars: "1. "
    line = line[3:]

    # trim the ending New Line char: '\n'
    if line.endswith('\n'):
        line = line[:-1]
        #line.rstrip('\n')

    line = line.replace("“", "\'\'")
    line = line.replace("”", "\'\'")
    line = line.replace("\"", "\'\'")

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
    condition = True
    lineLen = len(line)
    while condition:
        line = re.sub("\\[[^\\[]*?\\]", "", line)
        if len(line) != lineLen:
            lineLen = len(line)
        else:
            line = line.strip()
            condition = False
    return line


def writeLatexHeading(f):
    f.write("\\documentclass{beamer}\n")
    f.write("\n")
    f.write("\\usepackage{setspace}\n")
    f.write("\\usepackage{graphicx}\n")
    f.write("\\graphicspath{{./figures/}}\n")
    f.write("\DeclareGraphicsExtensions{.pdf,.jpg,.jpeg,.png}\n")
    f.write("\n")
    f.write("\\setbeamersize{text margin left=4pt, text margin right=4pt}\n")
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

bulletSmallFontCharLimit = 150

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


#fout.write("Hello world!\n")
writeLatexTailing(fout)
fout.close()
