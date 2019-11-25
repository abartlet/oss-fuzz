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
"""Uses bisection to determine which commit a bug was introduced and fixed.

This module takes a high and a low commit SHA, a repo name, and a bug.
The module bisects the high and low commit SHA searching for the location
where the bug was introduced. It also looks for where the bug was solved.
This is done with the following steps:
  Typical usage example:
    1. (Host) Clone the main project repo on the host
    2. (Host) Run git fetch --unshallow
    3. (Host) Use git bisect to identify the next commit to check
    4. (Client) Build the image at the specific commit using git hooks
    5. (Host) Build the fuzzers from new image with updated repo
    6. (Host) Test for bug’s existence
    7. Go to step 3

    python bisect.py --project_name curl 
      --commit-new e1f66ee3bfa06d294260a75ac6300f3783c7cc0b
      --commit-old 07cf042ececdcdc2b731c7a2040a48f21dde85b6
      --bug bug_data
"""

import argparse
import os
import subprocess
import shutil

from helper import _check_project_exists
from helper import _get_dockerfile_path


LOCAL_GIT_DIR = 'tmp_git'

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class NoRepoFoundException(Error):
  """Occurs when the bisector cant infer the main repo."""
  pass

class ProjectNotFoundException(Error):
  """No project could be found with given name."""

def main():
  
  """
  parser = argparse.ArgumentParser('bisector.py',
      description='git bisection for finding introduction of bugs')

  parser.add_argument('--project_name',
                      help='The name of the project where the bug occured',
                      required=True)
  parser.add_argument('--commit-new',
                      help='The newest commit SHA to be bisected',
                      required=True)
  parser.add_argument('--commit-old',
                      help='The oldest commit SHA to be bisected',
                      required=True)
  parser.add_argument('--bug', help='the bug to be searched for',
                      required=True)
  args = parser.parse_args()
  """

  remove(LOCAL_GIT_DIR)
  clone_repo_local('https://github.com/curl/curl.git', 'curl')


def remove(path):
    """ param <path> could either be relative or absolute. """
    if os.path.isfile(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        raise ValueError("file {} is not a file or dir.".format(path))

def infer_main_repo(project_name):
  if not _check_project_exists(project_name):
    raise ProjectNotFoundException('No project could be found with name %s' % project_name)

  docker_path = _get_dockerfile_path(project_name)
  with open(docker_path, 'r') as fp:
    for r in fp.readlines():
      for part_command in r.split(' '):
        if '/' + str(project_name) + '.git' in part_command:
          return part_command
  raise NoRepoFoundException('No repos were found with name %s in docker file %s' % (project_name, docker_path))

def run_command_in_repo(command, project_name):
  cur_dir = os.getcwd()
  os.chdir(LOCAL_GIT_DIR + '/' + project_name)
  process = subprocess.Popen(command, stdout=subprocess.PIPE)
  out, err = process.communicate()
  os.chdir(cur_dir)
  return out.decode('ascii').strip('\n'), err.decode('ascii').strip('\n')

def run_command_in_tmp(command):
  cur_dir = os.getcwd()
  os.chdir(LOCAL_GIT_DIR)
  subprocess.check_call(command)
  os.chdir(cur_dir)



def clone_repo_local(repo_name, project_name):
  os.mkdir(LOCAL_GIT_DIR)
  run_command_in_tmp(['git', 'clone', repo_name])
  out, err = run_command_in_repo(['git', 'bisect'

if __name__ == '__main__':
  main()
