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
      --commit_new 7627a2dd9d4b7417672fdec3dc6e7f8d3de379de
      --commit_old e80b5c801652bdd8aa302345954c3ef8050d039a
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
  pass


def main():
  parser = argparse.ArgumentParser('bisector.py',
      description='git bisection for finding introduction of bugs')

  parser.add_argument('--project_name',
                      help='The name of the project where the bug occured',
                      required=True)
  parser.add_argument('--commit_new',
                      help='The newest commit SHA to be bisected',
                      required=True)
  parser.add_argument('--commit_old',
                      help='The oldest commit SHA to be bisected',
                      required=True)
  parser.add_argument('--bug', help='the bug to be searched for',
                      required=True)
  args = parser.parse_args()

  # Remove the temp copy of repos from previous runs
  try:
    remove(LOCAL_GIT_DIR)
  except ValueError:
    pass

  # Create a temp copy of the repo for bisection purposes
  try:
    repo_name = infer_main_repo(args.project_name)
  except ProjectNotFoundException:
    print("Error project %s was not found under oss fuzz project" % args.project_name)
    return 1
  except NoRepoFoundException:
    print("Error the main repo of %s was not able to be inferred" % args.project_name)
    return 1
  clone_repo_local(repo_name)

  # Make sure both commit SHAs exist in the repo
  if not commit_exists(args.commit_new,  args.project_name):
    print("Error: your commit_new SHA %s does not exist in project %s." % (args.commit_new, args.project_name))
    return 1
  if not commit_exists(args.commit_old,  args.project_name):
    print("Error: your commit_old SHA %s does not exist in project %s." % (args.commit_old, args.project_name))
    return 1

  # Begin bisection

def bisection_commit(commit_old, commit_new, project_name):
  """Gets the commit SHA that is inbetween the two passed in commits.

  Args:
    commit_old: The oldest SHA in the search space
    commit_new: The newest SHA in the search space
    project_name: The name of the project we are searching for

  Returns:
    The SHA string inbetween the low and high
  """

def remove(path):
  """Attempts to remove a file or folder from the os

  Args:
    path: the location of what you are trying to remove

  Raises:
    ValueError: if there was no file found with the corispoding path
  """
  if os.path.isfile(path):
      os.remove(path)  # remove the file
  elif os.path.isdir(path):
      shutil.rmtree(path)  # remove dir and all contains
  else:
      raise ValueError("file {} is not a file or dir.".format(path))


def infer_main_repo(project_name):
  """ Trys to guess the main repo of the project based on the Dockerfile.

  Args:
    project_name: The name of the project you are testing

  Returns:
    The guessed repo url path

  Raises:
    NoRepoFoundException: if the repo can't be inferred
    ProjectNotFoundException: if the project passed in is not in oss fuzz
  """
  if not _check_project_exists(project_name):
    raise ProjectNotFoundException('No project could be found with name %s' % project_name)
  docker_path = _get_dockerfile_path(project_name)
  with open(docker_path, 'r') as fp:
    for r in fp.readlines():
      for part_command in r.split(' '):
        if '/' + str(project_name) + '.git' in part_command:
          return part_command
  raise NoRepoFoundException('No repos were found with name %s in docker file %s' % (project_name, docker_path))


def commit_exists(commit, project_name):
  """ Checks to see if a commit exists in the project repo.

  Args:
    commit: The commit SHA you are checking for
    project_name: The name of the project you are checking

  Returns:
    True if the commit exits in the project
  """

  # Handle the default case
  if commit.strip(' ') == '':
    return False

  out, err = run_command_in_repo(['git', 'branch', '--contains', commit], project_name)
  if ('error: no such commit' in out) or ('error: malformed object name' in out) or (out is ''):
    return False
  else:
    return True


def run_command_in_repo(command, project_name):
  """ Runs a command in the project_name repo.

  This runs under the precondition that clone_repo_local has allready been run.

  Args:
    command: The command as a list to be run
    project_name: The name of the project where the command should be run

  Returns:
    The stdout of the command, the stderr of the command
  """
  cur_dir = os.getcwd()
  os.chdir(LOCAL_GIT_DIR + '/' + project_name)
  process = subprocess.Popen(command, stdout=subprocess.PIPE)
  out, err = process.communicate()
  os.chdir(cur_dir)
  if err is not None:
    err = err.decode('ascii').strip('\n')
  if out is not None:
    out = out.decode('ascii').strip('\n')
  return out, err


def run_command_in_tmp(command):
  """ Runs a command in a temporary workspace.

  Args:
    command: the command as a list
  """
  cur_dir = os.getcwd()
  os.chdir(LOCAL_GIT_DIR)
  subprocess.check_call(command)
  os.chdir(cur_dir)


def clone_repo_local(repo_name):
  """ creates a local clone of a repo in the temp workspace

  Args:
    repo_name: The url path of the repo to clone
  """

  # Attempt to remove outdated dirs
  try: 
    remove(LOCAL_GIT_DIR)
  except ValueError:
    pass

  os.mkdir(LOCAL_GIT_DIR)
  run_command_in_tmp(['git', 'clone', repo_name])

if __name__ == '__main__':
  main()
