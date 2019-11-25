# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test the functionality of the bisector.py module.

This will test the following
  1. if the bisector.py is able to infer the main repo from the project name. 
  2. Clone the main repo to a local directory
  3. Build an image at the selected bisected commit
  4. Run the fuzzers at the selected bisected commit
"""

import sys
sys.path.append("..")

import os
import subprocess
import unittest

from bisector import infer_main_repo
from bisector import NoRepoFoundException
from bisector import ProjectNotFoundException

class TestBisector(unittest.TestCase):
  """Class to test the functionality of the bisector module."""

  def test_infer_main_repo(self):
    """Tests that the bisector can infer the main repo from the docker file."""
    main_repo_loc = infer_main_repo('curl')
    self.assertEqual(main_repo_loc, 'https://github.com/curl/curl.git')

    main_repo_loc = infer_main_repo('aspell')
    self.assertEqual(main_repo_loc, 'https://github.com/gnuaspell/aspell.git')

    with self.assertRaises(NoRepoFoundException):
      main_repo_loc = infer_main_repo('bad_example')


if __name__ == '__main__':
  unittest.main()
