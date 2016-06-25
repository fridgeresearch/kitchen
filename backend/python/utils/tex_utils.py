"""
The MIT License (MIT)

Copyright (c) 2016 Jake Lussier (Stanford University)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os, subprocess

def _getProps(kwargs):
    return ','.join(["%s=%s"%(k,v) if v else k for (k,v) in kwargs.items()])

class TexFile:
    def __init__(self, stem, packages=[]):
        self.stem = stem
        self.f = open("%s.tex"%self.stem, "w")
        self.f.write('''\\documentclass[12pt]{article}\n''')
    def close(self):
        self.f.close()
    def usePackage(self, package, **kwargs):
        self.f.write('''\\usepackage[%s]{%s}\n'''%(_getProps(kwargs),package))
    def paperWidth(self, width, units="in"):
        self.f.write('''\\paperwidth %f%s\n''' % (width, units))
    def paperHeight(self, height, units="in"):
        self.f.write('''\\paperheight %f%s\n''' % (height, units))
    def beginDocument(self):
        self.f.write('''\\begin{document}\n''')
    def endDocument(self):
        self.f.write('''\\end{document}\n''')
    def write(self, txt):
        self.f.write(txt)
    def beginTikzPicture(self, xscale="1cm", yscale="1cm"):
        self.f.write('''\\begin{tikzpicture}[x=%s,y=%s]\n''' % (xscale, yscale))
    def endTikzPicture(self):
        self.f.write('''\\end{tikzpicture}\n''')
    def drawLine(self, start, end, **kwargs):
        self.f.write('''\\draw[%s] %s -- %s;\n''' % (_getProps(kwargs), str(tuple(start)), str(tuple(end))))
    def drawEmptyRectangle(self, pos, height, width, **kwargs):
        self.f.write('''\\draw[%s] %s -- %s -- %s -- %s -- cycle;\n''' %\
                     (_getProps(kwargs), str((pos[0],pos[1])), str((pos[0]+width,pos[1])),\
                      str((pos[0]+width,pos[1]+height)), str((pos[0], pos[1]+height))))
    def drawRectangle(self, pos, height, width, **kwargs):
        self.f.write('''\\fill[%s] %s rectangle %s;\n''' %\
                     (_getProps(kwargs), str((pos[0],pos[1])),
                      str((pos[0]+width,pos[1]+height))))

    def drawCircle(self, pos, rad, **kwargs):
        self.f.write('''\\draw[%s] %s circle (%f);\n'''%(_getProps(kwargs), str(tuple(pos)), rad))
    def drawText(self, pos, text, **kwargs):
        self.f.write('''\\node[%s] at %s {%s};\n'''%(_getProps(kwargs), str(tuple(pos)), text))
    def includeGraphic(self, fname, width=None, height=None, border=None):
        props = ""
        if width != None: props = "width=%s"%width
        if height != None: props = "%sheight=%s"%("" if not props else props+",", height)
        if border == None:
            self.f.write('''\\includegraphics[%s]{%s}\n''' % (props, fname))
        else:
            self.f.write('''\\fboxsep=%s\n''' % border)
            self.f.write('''\\fboxrule=1pt\n''')
            self.f.write('''\\fcolorbox{black}{white}{\\includegraphics[%s]{%s}}\n''' % (props, fname))
    def compile(self):
        d = os.path.dirname(self.stem)
        if not d: d = "."
        f = os.path.basename(self.stem)
        cmd = "cd %s && pdflatex %s.tex && rm %s.aux %s.log" % (d, f, f, f)
        subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        #os.system(cmd)
