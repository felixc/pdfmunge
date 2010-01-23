#!/usr/bin/python

"""
pdfmunge - Process PDFs to make them more legible on eBook readers.

Copyright (c) 2009, 2010 Felix Crux (www.felixcrux.com)
Available under the MIT License (see Readme).

"""

usage_string = """
Usage: pdfmunge [options]... input_file output_file
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
  page_nums = range(0, input.getNumPages())
  page_nums = [x for x in page_nums if x not in options["exclude"]]
  for page_num in page_nums:
    page = input.getPage(page_num)
    page2 = None if not options["rotate"] else input2.getPage(page_num)
    if page_num not in options["intact"]:
      if "bounds" in options:
        crop(page, page_num, options);
        crop(page2, page_num, options)

      if options["rotate"]:
        rotate(page, page2, options)

      output.addPage(page)
      if page2 is not None:
        output.addPage(page2)
    else:
      output.addPage(page)

  # All right, we're done. Write the output, close up, go home.
  output.write(output_stream)

  input_stream.close()
  output_stream.close()

  return 0


def crop(page, page_num, options):
  """ Apply user-specified bounds to the page. """
  # Note that (page_num % 2 == 0) is the correct test for odd numbered pages,
  # since we are using 0-indexed ones, where the user expects 1-indexed.
  if page is not None:
    if "oddbounds" in options and (page_num % 2 == 0):
      bounds = options["oddbounds"]
    else:
      bounds = options["bounds"]
    page.mediaBox = pyPdf.generic.RectangleObject(bounds)


def rotate(page, page2, options):
  """ Perform slicing and rotation on pages. """
  bounds = list(page.mediaBox.lowerLeft) + list(page.mediaBox.upperRight)
  bounds2 = list(page2.mediaBox.lowerLeft) + list(page2.mediaBox.upperRight)
  bounds[1] = (bounds[3] - bounds[1]) / 2 + bounds[1] - options["margin"]
  bounds2[3] = (bounds2[3] - bounds2[1]) / 2 + bounds2[1] + options["margin"]

  page.mediaBox = pyPdf.generic.RectangleObject(bounds)
  page2.mediaBox = pyPdf.generic.RectangleObject(bounds2)

  page.rotateCounterClockwise(90)
  page2.rotateCounterClockwise(90)


def handle_options(argv):
  """ Parse the comamnd-line arguments and populate the options dictionary.

  All options are optional (as the name tends to suggest), but two
  arguments are required: an input filename and an output filename.

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
  exit(main(sys.argv[1:]))
