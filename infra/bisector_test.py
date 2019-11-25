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

import bisector
from bisector import *


class TestBisector(unittest.TestCase):
  """Class to test the functionality of the bisector module."""

  # The name of the project used for testing
  PROJECT_TEST_NAME = 'curl'


  def setUp(self):
    """Sets up a testing enviroment for the curl git directory."""
    try:
      repo_name = infer_main_repo(self.PROJECT_TEST_NAME)
    except ProjectNotFoundException:
      print("Error project %s was not found under oss fuzz project" % args.project_name)
      return 1
    except NoRepoFoundException:
      print("Error the main repo of %s was not able to be inferred" % args.project_name)
      return 1
    clone_repo_local(repo_name)


  def tearDown(self):
    """Tears down the testing enviroment for the curl git directory. """
    remove(bisector.LOCAL_GIT_DIR)


  def test_infer_main_repo(self):
    """Tests that the bisector can infer the main repo from the docker file."""
    main_repo_loc = infer_main_repo('curl')
    self.assertEqual(main_repo_loc, 'https://github.com/curl/curl.git')

    main_repo_loc = infer_main_repo('aspell')
    self.assertEqual(main_repo_loc, 'https://github.com/gnuaspell/aspell.git')

    with self.assertRaises(NoRepoFoundException):
      main_repo_loc = infer_main_repo('bad_example')


  def test_commit_exists(self):
    """Tests if the commit exists function is working properly"""
    self.assertTrue(commit_exists('7627a2dd9d4b7417672fdec3dc6e7f8d3de379de', self.PROJECT_TEST_NAME))
    self.assertTrue(commit_exists('e80b5c801652bdd8aa302345954c3ef8050d039a', self.PROJECT_TEST_NAME))
    self.assertFalse(commit_exists('', self.PROJECT_TEST_NAME))
    self.assertFalse(commit_exists(' ', self.PROJECT_TEST_NAME))
    self.assertFalse(commit_exists('e16eed09ac66546db5a66fba07e849c19b85dcdf', self.PROJECT_TEST_NAME)) 

if __name__ == '__main__':
  unittest.main()
