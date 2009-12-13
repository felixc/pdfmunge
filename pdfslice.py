#!/usr/bin/python

"""
pdfslice - Process PDFs to make them more legible on eBook readers.

Copyright (c) 2009 Felix Crux (www.felixcrux.com)
Available under the MIT License (included at end of file).

"""

usage_string = """
Usage: pdfslice [options]... input_file output_file
Options:
  -r  --rotate     Slice pages in half and rotate each half 90 degrees
                   counter-clockwise, creating a pseudo-landscape mode on
                   devices that don't do this automatically. Be warned that
                   this will double the size of your output file.
  -m  --margin     If using rotation/slicing, have each page overlap with the
                   previous one by this amount (helps with lines getting cut
                   off in the middle).
  -b  --bounds     Boundaries of visible area on each PDF page. Useful for
                   cropping off large margins. If this is given, cropping is
                   done automatically; otherwise it is not done. Boundaries
                   should be given as four comma-separated numbers, all
                   enclosed in quotation marks, like so: "10,20,100,120". Any
                   whitespace inside the quotation marks is ignored.
  -o  --oddbounds  For PDFs that have different margins on even and odd pages,
                   use these boundary values for odd numbered pages, with
                   --bounds applying to even numbered ones. If this is given,
                   --bounds is required.
  -e  --exclude    Numbers or ranges of pages to not include in the output PDF.
                   These should be given as a series of numbers or ranges
                   surrounded by quotation marks, and separated by commas. Any
                   whitespace is ignored. Ranges are given as two numbers
                   separated by a hyphen/minus sign (-), where the first number
                   must be smaller than the second. Example: "1,2,4-8,40".
                   This option takes precedence over --intact.
  -i  --intact     Leave these pages completely unchanged, ignoring
                   cropping, rotating, or anything else. Requires a set of
                   numbers or ranges like --exclude. Excluded pages are
                   ignored even if listed here.
"""


import getopt
import pyPdf
import sys


def main(argv):
  """  Process PDFs to make them more legible on eBook readers. """
  try:
    options = handle_options(argv)
  except getopt.GetoptError as err:
    print(str(err))
    print(usage_string)
    return 2

  # Get our inputs and outputs sorted out and opened.
  try:
    input_stream = file(options["infile"], "rb")
    input = pyPdf.PdfFileReader(input_stream)
    if options["rotate"] is True:
      input2 = pyPdf.PdfFileReader(input_stream)
  except IOError as err:
    print("Unable to open input file: %s" % str(err))
    return 1

  try:
    output_stream = file(options["outfile"], "wb")
    output = pyPdf.PdfFileWriter()
  except IOError as err:
    print("Unable to create output file: %s" % str(err))
    return 1

  # The meat of the program: go over every page performing the user's bidding.
  # This mess really, really, needs to be refactored.
  for pagenum in range(0, input.getNumPages()):
    if pagenum not in options["exclude"]:
      page = input.getPage(pagenum)
      if pagenum not in options["intact"]:
        if options["rotate"] is True:
          page2 = input2.getPage(pagenum)
          page.mediaBox = pyPdf.generic.RectangleObject(
            calculate_bounds(pagenum, options, True))
          page2.mediaBox = pyPdf.generic.RectangleObject(
            calculate_bounds(pagenum, options, False))
          page.rotateCounterClockwise(90)
          page2.rotateCounterClockwise(90)
          output.addPage(page)
          output.addPage(page2)
        else:
          if "bounds" in options:
            page.mediaBox = pyPdf.generic.RectangleObject(
              calculate_bounds(pagenum, options))
          output.addPage(page)
      else:
        output.addPage(page)

  # All right, we're done. Write the output, close up, go home.
  output.write(output_stream)

  input_stream.close()
  output_stream.close()

  return 0


def calculate_bounds(pagenum, options, top=False):
  """ Determine the appropriate page boundaries based on page
  odd/evenness and rotation.

  Note that the function expects to receive page numbers 0-indexed, but treats
  them as 1-indexed in order to satisfy user expectations. This means that page
  4 will be treated as odd, and 5 as even, because they are really pages 5 and
  6 to the user. Page 1 (i.e. value 0) is odd.

  Examples:
  >>> calculate_bounds(1, {'rotate': False, 'bounds': [4,4,10,10]})
  [4, 4, 10, 10]
  >>> calculate_bounds(1, {'rotate': False, 'bounds': [4,4,10,10], \
                           'oddbounds': [2,2,8,8]})
  [4, 4, 10, 10]
  >>> calculate_bounds(2, {'rotate': False, 'bounds': [4,4,10,10], \
                           'oddbounds': [2,2,8,8]})
  [2, 2, 8, 8]
  >>> calculate_bounds(1, {'rotate': True, 'bounds': [4,4,10,10], \
                           'margin': 0}, True)
  [4, 7, 10, 10]
  >>> calculate_bounds(1, {'rotate': True, 'bounds': [4,4,10,10], \
                           'margin': 2}, True)
  [4, 5, 10, 10]
  >>> calculate_bounds(1, {'rotate': True, 'bounds': [4,4,10,10], \
                           'margin': 0})
  [4, 4, 10, 7]
  >>> calculate_bounds(1, {'rotate': True, 'bounds': [4,4,10,10], \
                           'oddbounds': [2,2,8,8], 'margin': 0}, True)
  [4, 7, 10, 10]
  >>> calculate_bounds(1, {'rotate': True, 'bounds': [4,4,10,10], \
                           'oddbounds': [2,2,8,8], 'margin': 0})
  [4, 4, 10, 7]
  >>> calculate_bounds(2, {'rotate': True, 'bounds': [4,4,10,10], \
                           'oddbounds': [2,2,8,8], 'margin': 0}, True)
  [2, 5, 8, 8]
  >>> calculate_bounds(2, {'rotate': True, 'bounds': [4,4,10,10], \
                           'oddbounds': [2,2,8,8], 'margin': 0})
  [2, 2, 8, 5]

  """
  if options["rotate"] == True:
    if "oddbounds" in options and (pagenum % 2 == 0):
      bounds = options["oddbounds"][:]
    else:
      bounds = options["bounds"][:]
    if top:
      bounds[1] = (bounds[3] - bounds[1]) / 2 + bounds[1] - options["margin"]
    else:
      bounds[3] = (bounds[3] - bounds[1]) / 2 + bounds[1] + options["margin"]
    return bounds
  elif "oddbounds" in options and (pagenum % 2 == 0):
    return options["oddbounds"]
  else:
    return options["bounds"]


def handle_options(argv):
  """ Parse the comamnd-line arguments and populate the options dictionary.

  All options are optional (as the name tends to suggest), but two
  arguments are required: an input filename and an output filename.

  Examples:
  >>> handle_options(["infile", "outfile"]) == \
    {'rotate': False, 'exclude': [], 'intact': [], 'margin': 0,\
     'infile': 'infile', 'outfile':'outfile'}
  True

  >>> handle_options(["-r", "-b", "4,5,6,7", "-o", "2,3,4,5", \
                      "-e", "1,2,5-7,100-102", "-i", "1,15-16", \
                      "-m", "3", "infile","outfile"]) == \
    {'rotate': True, 'bounds': [4,5,6,7], 'oddbounds': [2,3,4,5], \
     'exclude': [0,1,4,5,6,99,100,101], 'intact': [0,14,15], \
     'margin': 3, 'infile': 'infile', 'outfile': 'outfile'}
  True

  >>> handle_options(["--rotate", \
                      "--bounds", "4,5,6,7", "--oddbounds", "2,3,4,5", \
                      "--exclude", "1,2,5-7,100-102", "--intact", "1,15-16", \
                      "--margin", 3, "infile", "outfile"]) == \
    {'rotate': True, 'bounds': [4,5,6,7], 'oddbounds': [2,3,4,5], \
     'exclude': [0,1,4,5,6,99,100,101], 'intact': [0,14,15], \
     'margin': 3, 'infile': 'infile', 'outfile': 'outfile'}
  True

  >>> handle_options(["-o", "2,3,4,5", "infile", "outfile"])
  Traceback (most recent call last):
    ...
  GetoptError: Boundaries for even pages required if odd page boundaries given.

  >>> handle_options(["infile"])
  Traceback (most recent call last):
    ...
  GetoptError: Missing input or output filename.

  """
  options = {"rotate": False, "exclude": [], "intact": [], "margin": 0}

  opts, args = getopt.getopt(argv,
                             "rb:o:e:i:m:",
                             ["rotate", "bounds=", "oddbounds=",
                              "exclude=", "intact=", "margin="])
  for opt, arg in opts:
    if opt in ("-r", "--rotate"):
      options["rotate"] = True
    elif opt in ("-b", "--bounds"):
      options["bounds"] = parse_bounds(arg)
    elif opt in ("-o", "--oddbounds"):
      options["oddbounds"] = parse_bounds(arg)
    elif opt in ("-e", "--exclude"):
      options["exclude"] = parse_range(arg)
    elif opt in ("-i", "--intact"):
      options["intact"] = parse_range(arg)
    elif opt in ("-m", "--margin"):
      options["margin"] = int(arg)
    else:
      assert False, "Unhandled Option"

  try:
    options["infile"], options["outfile"] = args[0], args[1]
  except IndexError:
    raise getopt.GetoptError("Missing input or output filename.")

  if "oddbounds" in options and "bounds" not in options:
    raise getopt.GetoptError("Boundaries for even pages required if odd "
                             "page boundaries given.")

  return options


def parse_bounds(bounds_string):
  """ Given a string representation of four boundary values, return a
  four-item list representing those numbers.

  Input values should be separated by commas, with whitespace being ignored.

  Examples:
  >>> parse_bounds("2,3,4,5")
  [2, 3, 4, 5]
  >>> parse_bounds("2,  3  , 4 , 5")
  [2, 3, 4, 5]

  """
  return [int(val) for val in bounds_string.split(",")]


def parse_range(range_string):
  """ Return a list of numbers representing the input ranges.

  Inputs can be individual numbers, or ranges, given by two numbers separated
  by a hyphen/minus sign (-), with each input separated by a comma. All
  whitespace is ignored. In range-type inputs, the second number must be
  larger than the first. Ranges are inclusive of both numbers.

  Because these numbers represent page numbers, which humans index from 1, but
  pyPdf indexes from 0, the *inputs* are 1-indexed, but the *outputs* are
  0-indexed.

  Examples:
  >>> parse_range("1")
  [0]
  >>> parse_range("1,2,3")
  [0, 1, 2]
  >>> parse_range("1-3")
  [0, 1, 2]
  >>> parse_range("1, 4-6, 14, 15, 30-31")
  [0, 3, 4, 5, 13, 14, 29, 30]

  """
  expanded_list = []
  ranges = range_string.split(",")
  for cur_range in ranges:
    if cur_range.find("-") > -1:
      start, end = cur_range.split("-")
      start, end = int(start) - 1, int(end)
      expanded_list.extend(list(range(start, end)))
    else:
      expanded_list.append(int(cur_range) - 1)
  return expanded_list


if __name__ == "__main__":
  args = sys.argv[1:]
  if len(args) > 0 and args[0] == "--test":
    import doctest
    doctest.testmod()
  else:
    exit(main(args))


license = """
Copyright (c) 2009 Felix Crux (www.felixcrux.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
