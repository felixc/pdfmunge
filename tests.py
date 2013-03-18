#!/usr/bin/python3

"""
Test cases for pdfmunge.

Copyright Felix Crux (www.felixcrux.com)
Available under the MIT License (see Readme).

"""

import unittest
import getopt
import pdfmunge


class ParseBoundsTest(unittest.TestCase):
  def testUnspacedItems(self):
    self.assertEqual(pdfmunge.parse_bounds("2,3,4,5"), [2, 3, 4, 5])

  def testSpacedItems(self):
    self.assertEqual(pdfmunge.parse_bounds("2, 3 , 4,   5"), [2, 3, 4, 5])


class ParseRangeTest(unittest.TestCase):
  def testSingleItem(self):
    self.assertEqual(pdfmunge.parse_range("1"), [0])

  def testCommaSeparatedItems(self):
    self.assertEqual(pdfmunge.parse_range("1,2,3"), [0, 1, 2])

  def testHyphenatedRangeItems(self):
    self.assertEqual(pdfmunge.parse_range("1-3"), [0, 1, 2])

  def testCombinedItems(self):
    self.assertEqual(pdfmunge.parse_range("1, 4-6, 14, 15, 30-31"),
                     [0, 3, 4, 5, 13, 14, 29, 30])


class HandleOptionsTest(unittest.TestCase):
  def testDefaults(self):
    self.assertEqual(pdfmunge.handle_options(["infile", "outfile"]),
                     {'rotate': False, 'exclude': [], 'intact': [],
                      'margin': 0, 'infile': 'infile', 'outfile':'outfile'})

  def testShortOtions(self):
    self.assertEqual(pdfmunge.handle_options(["-r", "-b", "4,5,6,7",
                                              "-o", "2,3,4,5",
                                              "-e", "1,2,5-7,100-102",
                                              "-i", "1,15-16",
                                              "-m", "3", "infile","outfile"]),
                     {'rotate': True, 'bounds': [4,5,6,7],
                      'oddbounds': [2,3,4,5], 'exclude': [0,1,4,5,6,99,100,101],
                      'intact': [0,14,15], 'margin': 3, 'infile': 'infile',
                      'outfile': 'outfile'})

  def testLongOptions(self):
    self.assertEqual(pdfmunge.handle_options(["--rotate", "--bounds", "4,5,6,7",
                                              "--oddbounds", "2,3,4,5",
                                              "--exclude", "1,2,5-7,100-102",
                                              "--intact", "1,15-16",
                                              "--margin", 3,
                                              "infile", "outfile"]),
                     {'rotate': True, 'bounds': [4,5,6,7],
                      'oddbounds': [2,3,4,5], 'exclude': [0,1,4,5,6,99,100,101],
                      'intact': [0,14,15], 'margin': 3, 'infile': 'infile',
                      'outfile': 'outfile'})

  def testFailOnMissingBounds(self):
    self.assertRaises(getopt.GetoptError,
                      pdfmunge.handle_options, ["-o", "2,3,4,5",
                                                "infile", "outfile"])

  def testFailOnMissingOutputFile(self):
    self.assertRaises(getopt.GetoptError,
                      pdfmunge.handle_options, ["infile"])


if __name__ == '__main__':
  unittest.main()
