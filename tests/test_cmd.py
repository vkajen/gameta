import json
import venv
import zipfile
from os.path import join, dirname, exists
from shutil import copyfile
from unittest import TestCase
from unittest.mock import patch

from click.testing import CliRunner

from gameta.context import GametaContext
from gameta.cmd import add, delete, update, ls


class TestCommandAdd(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.add = add

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_key_parameters_not_provided(self, mock_ensure_object):
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.add)
            self.assertEqual(result.exit_code, 2)
            self.assertEqual(
                result.output,
                "Usage: add [OPTIONS]\n"
                "Try 'add --help' for help.\n"
                "\n"
                "Error: Missing option '--name' / '-n'.\n"
            )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_no_meta_file(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add, ['-n', params['name'], '-c', params['commands'][0], '-c', params['commands'][1]]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Adding command {params['name']} with parameters ({{'commands': {params['commands']}, "
                f"'description': '', 'tags': [], 'repositories': [], 'venv': None, 'verbose': False, 'shell': True, "
                f"'python': False, 'raise_errors': False}}) "
                f"to the command store\n"
                f"Successfully added command {params['name']} to the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {},
                        'commands': {
                            params['name']: {
                                'commands': params['commands'],
                                'description': '',
                                'raise_errors': False,
                                'repositories': [],
                                'shell': True,
                                'tags': [],
                                'venv': None,
                                'python': False,
                                'verbose': False
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_python_scripts(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': [
                'from random import choice\n'
                'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                '    f.write("".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '
                'for _ in range({KEY_LEN})]))',
                'from os import getcwd\n'
                'from os.path import join, exists\n'
                'from shutil import copyfile\n'
                'for repo, details in {__repos__}.items():\n'
                '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
            ],
            'description': 'Generates an encryption key',
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': True,
            'venv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-d', params['description'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-p', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Adding command {params['name']} with parameters ({{'commands': {params['commands']}, "
                f"'description': '{params['description']}', 'tags': {params['tags']}, "
                f"'repositories': {params['repositories']}, 'venv': {params['venv']}, 'verbose': {params['verbose']}, "
                f"'shell': {params['shell']}, 'python': {params['python']}, 'raise_errors': {params['raise_errors']}}})"
                f" to the command store\n"
                f"Successfully added command {params['name']} to the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            params['name']: {
                                'commands': params['commands'],
                                'description': params['description'],
                                'raise_errors': params['raise_errors'],
                                'repositories': params['repositories'],
                                'shell': params['shell'],
                                'tags': params['tags'],
                                'venv': params['venv'],
                                'python': params['python'],
                                'verbose': params['verbose']
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_invalid_python_script(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': [
                'from random import choice\n'
                'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                '    f.write(".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '  # Missing a "
                'for _ in range({KEY_LEN})]))',
                'from os import getcwd\n'
                'from os.path import join, exists\n'
                'from shutil import copyfile\n'
                'for repo, details in {__repos__}.items():\n'
                '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
            ],
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': True,
            'virtualenv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-p', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Error: One of the commands in {params['commands']} is not a valid Python script\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_python_flag_with_shell_command(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': True,
            'virtualenv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-p', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Error: One of the commands in {params['commands']} is not a valid Python script\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_full_data(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'description': 'Fetches code from all repos',
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': False,
            'venv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-d', params['description'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-s', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Adding command {params['name']} with parameters ({{'commands': {params['commands']}, "
                f"'description': '{params['description']}', 'tags': {params['tags']}, "
                f"'repositories': {params['repositories']}, 'venv': {params['venv']}, 'verbose': {params['verbose']}, "
                f"'shell': {params['shell']}, 'python': {params['python']}, 'raise_errors': {params['raise_errors']}}})"
                f" to the command store\n"
                f"Successfully added command {params['name']} to the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            params['name']: {
                                'commands': params['commands'],
                                'description': params['description'],
                                'raise_errors': params['raise_errors'],
                                'repositories': params['repositories'],
                                'shell': params['shell'],
                                'tags': params['tags'],
                                'venv': params['venv'],
                                'python': params['python'],
                                'verbose': params['verbose']
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_nonexistent_tag(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': ['hello'],
            'repositories': [],
            'verbose': True,
            'shell': True,
            'python': False,
            'virtualenv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-t', params['tags'][0],
                    '-v', '-s', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Error: One of the tags in {params['tags']} has not been added, please run "
                f"`gameta tags add` to add it first\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_nonexistent_repository(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': [],
            'repositories': ['GitPython', 'gitdb'],
            'verbose': True,
            'shell': True,
            'python': False,
            'virtualenv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-r', params['repositories'][0],
                    '-r', params['repositories'][1],
                    '-v', '-s', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Error: One of the repositories in {params['repositories']} does not exist, please "
                f"run `gameta repo add` to add it first\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_command_overwritten(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'description': 'Fetches all commands',
            'verbose': True,
            'shell': True,
            'python': False,
            'venv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'description': 'Lame description',
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'tags': [],
                                    'venv': None,
                                    'python': False,
                                    'verbose': False
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-d', params['description'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-s', '-e', '-o'
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Adding command {params['name']} with parameters ({{'commands': {params['commands']}, "
                f"'description': '{params['description']}', 'tags': {params['tags']}, "
                f"'repositories': {params['repositories']}, 'venv': {params['venv']}, 'verbose': {params['verbose']}, "
                f"'shell': {params['shell']}, 'python': {params['python']}, 'raise_errors': {params['raise_errors']}}}) "
                f"to the command store\n"
                f"Overwriting command {params['name']} in the command store\n"
                f"Successfully added command {params['name']} to the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            params['name']: {
                                'commands': params['commands'],
                                'description': params['description'],
                                'raise_errors': params['raise_errors'],
                                'repositories': params['repositories'],
                                'shell': params['shell'],
                                'tags': params['tags'],
                                'python': params['python'],
                                'venv': params['venv'],
                                'verbose': params['verbose']
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_shell_command_with_virtualenv(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['pip install cryptography'],
            'description': 'Install cryptography into virtualenv test',
            'tags': [],
            'repositories': ['gameta'],
            'verbose': False,
            'shell': True,
            'python': False,
            'raise_errors': True,
            'venv': 'test',
            'directory': 'test'
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            venv.create(params['directory'], clear=False, with_pip=True, symlinks=False, system_site_packages=False)
            with open(join(dirname(__file__), 'data', '.meta'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update({'virtualenvs': {params['venv']: join(f, params['directory'])}})
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-r', params['repositories'][0],
                    '-d', params['description'],
                    '-ve', params['venv'],
                    '-s', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Adding command {params['name']} with parameters ({{'commands': {params['commands']}, "
                f"'description': '{params['description']}', 'tags': {params['tags']}, "
                f"'repositories': {params['repositories']}, 'venv': '{params['venv']}', "
                f"'verbose': {params['verbose']}, 'shell': {params['shell']}, 'python': {params['python']}, "
                f"'raise_errors': {params['raise_errors']}}}) to the command store\n"
                f"Successfully added command {params['name']} to the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        },
                        'commands': {
                            params['name']: {
                                'commands': params['commands'],
                                'description': params['description'],
                                'raise_errors': params['raise_errors'],
                                'repositories': params['repositories'],
                                'shell': params['shell'],
                                'tags': params['tags'],
                                'python': params['python'],
                                'venv': params['venv'],
                                'verbose': params['verbose']
                            }
                        },
                        'virtualenvs': {
                            params['venv']: join(f, params['directory'])
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_python_commands_with_virtualenv(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': [
                'from cryptography.fernet import Fernet\n'
                'key = Fernet.generate_key()\n'
                'encryptor = Fernet(key)\n'
                'message = encryptor.encrypt(b"This is a secret message")\n'
                'with open("{ENCRYPTION_FILE_NAME}", "wb") as f:\n'
                '    f.write(message)\n'
                'with open("key", "wb") as f:\n'
                '    f.write(key)\n',
                'from cryptography.fernet import Fernet\n'
                'with open("key", "rb") as f:\n'
                '    decryptor = Fernet(f.read())\n'
                'with open("{ENCRYPTION_FILE_NAME}", "rb") as f:\n'
                '    print("This is the decrypted message:", decryptor.decrypt(f.read()).decode("utf-8"))\n'
            ],
            'description': 'Install cryptography into virtualenv test',
            'tags': [],
            'repositories': ['gameta'],
            'verbose': False,
            'shell': True,
            'python': True,
            'raise_errors': True,
            'venv': 'test',
            'directory': 'test'
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            venv.create(params['directory'], clear=False, with_pip=True, symlinks=False, system_site_packages=False)
            with open(join(dirname(__file__), 'data', '.meta'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update({'virtualenvs': {params['venv']: join(f, params['directory'])}})
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-r', params['repositories'][0],
                    '-d', params['description'],
                    '-ve', params['venv'],
                    '-s', '-e', '-p'
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Adding command {params['name']} with parameters ({{'commands': {params['commands']}, "
                f"'description': '{params['description']}', 'tags': {params['tags']}, "
                f"'repositories': {params['repositories']}, 'venv': '{params['venv']}', "
                f"'verbose': {params['verbose']}, 'shell': {params['shell']}, 'python': {params['python']}, "
                f"'raise_errors': {params['raise_errors']}}}) to the command store\n"
                f"Successfully added command {params['name']} to the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        },
                        'commands': {
                            params['name']: {
                                'commands': params['commands'],
                                'description': params['description'],
                                'raise_errors': params['raise_errors'],
                                'repositories': params['repositories'],
                                'shell': params['shell'],
                                'tags': params['tags'],
                                'python': params['python'],
                                'venv': params['venv'],
                                'verbose': params['verbose']
                            }
                        },
                        'virtualenvs': {
                            params['venv']: join(f, params['directory'])
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_python_flag_with_shell_command(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': True,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-p', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Error: One of the commands in {params['commands']} is not a valid Python script\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_add_shell_command_with_nonexistent_virtualenv(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['pip install cryptography'],
            'description': 'Install cryptography into virtualenv test',
            'tags': [],
            'repositories': ['gameta'],
            'verbose': False,
            'shell': True,
            'python': False,
            'raise_errors': True,
            'venv': 'test'
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.add,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-r', params['repositories'][0],
                    '-d', params['description'],
                    '-ve', params['venv'],
                    '-s', '-e'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Error: Virtualenv {params['venv']} has not been registered, please run `gameta venv register` to "
                f"register it first\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        }
                    }
                )


class TestCommandDelete(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.delete = delete

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_delete_key_parameters_not_provided(self, mock_ensure_object):
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.delete)
            self.assertEqual(result.exit_code, 2)
            self.assertEqual(
                result.output,
                "Usage: delete [OPTIONS]\n"
                "Try 'delete --help' for help.\n"
                "\n"
                "Error: Missing option '--name' / '-n'.\n"
            )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_delete_no_meta_file(self, mock_ensure_object):
        params = {
            'name': 'hello_world'
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.delete, ['-n', params['name']])
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Deleting command {params['name']} from the command store\n"
                f"Error: Command {params['name']} does not exist in the command store\n"
            )
            self.assertFalse(exists(join(f, '.meta')))

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_delete_nonexistent_command(self, mock_ensure_object):
        params = {
            'name': 'hello_world'
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.delete, ['-n', params['name']])
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Deleting command {params['name']} from the command store\n"
                f"Error: Command {params['name']} does not exist in the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_delete_command_deleted(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull']
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'description': "test",
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'python': False,
                                    'venv': None,
                                    'tags': [],
                                    'verbose': False
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.delete, ['-n', params['name']])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Deleting command {params['name']} from the command store\n"
                f"Successfully deleted command {params['name']} from the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        },
                        "commands": {}
                    }
                )


class TestCommandUpdate(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.update = update

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_key_parameters_not_provided(self, mock_ensure_object):
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta_other_repos'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.update)
            self.assertEqual(result.exit_code, 2)
            self.assertEqual(
                result.output,
                "Usage: update [OPTIONS]\n"
                "Try 'update --help' for help.\n"
                "\n"
                "Error: Missing option '--name' / '-n'.\n"
            )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_no_meta_file(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': False,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.update, ['-n', params['name']])
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Error: Command {params['name']} does not exist in the command store\n"
            )
            self.assertFalse(exists(join(f, '.meta')))

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_nonexistent_command(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': False,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.update, ['-n', params['name']])
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Error: Command {params['name']} does not exist in the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_full_update(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'description': 'Fetches and updates code',
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': False,
            'venv': 'test',
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'description': 'Lame description',
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'tags': [],
                                    'python': False,
                                    'venv': None,
                                    'verbose': False
                                }
                            },
                            'virtualenvs': {
                                params['venv']: join(f, params['venv'])
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-d', params['description'],
                    '-r', params['repositories'][0],
                    '-ve', params['venv'],
                    '-v', '-s', '-e',
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Successfully updated command {params['name']} in the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['commands'],
                                'description': params['description'],
                                'venv': params['venv'],
                                'tags': params['tags'],
                                'python': False,
                                'repositories': params['repositories'],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'raise_errors': params['raise_errors']
                            }
                        },
                        'virtualenvs': {
                            params['venv']: join(f, params['venv'])
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_to_another_virtualenv(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'description': 'Fetches and updates code',
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': False,
            'venv1': 'test1',
            'venv2': 'test2',
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'description': 'Lame description',
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'tags': [],
                                    'python': False,
                                    'venv': params['venv1'],
                                    'verbose': False
                                }
                            },
                            'virtualenvs': {
                                params['venv1']: join(f, params['venv1']),
                                params['venv2']: join(f, params['venv2'])
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-d', params['description'],
                    '-r', params['repositories'][0],
                    '-ve', params['venv2'],
                    '-v', '-s', '-e',
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Successfully updated command {params['name']} in the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['commands'],
                                'description': params['description'],
                                'venv': params['venv2'],
                                'tags': params['tags'],
                                'python': False,
                                'repositories': params['repositories'],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'raise_errors': params['raise_errors']
                            }
                        },
                        'virtualenvs': {
                            params['venv1']: join(f, params['venv1']),
                            params['venv2']: join(f, params['venv2'])
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_to_python_scripts(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'new_commands': [
                'from random import choice\n'
                'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                '    f.write("".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '
                'for _ in range({KEY_LEN})]))',
                'from os import getcwd\n'
                'from os.path import join, exists\n'
                'from shutil import copyfile\n'
                'for repo, details in {__repos__}.items():\n'
                '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
            ],
            'description': 'Generates an encryption key',
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': True,
            'venv': 'test',
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'description': "Lame description",
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'python': True,
                                    'tags': [],
                                    'venv': None,
                                    'verbose': False
                                }
                            },
                            'virtualenvs': {
                                params['venv']: join(f, params['venv'])
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-c', params['new_commands'][0],
                    '-c', params['new_commands'][1],
                    '-d', params['description'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-ve', params['venv'],
                    '-v', '-s', '-e', '-p'
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Successfully updated command {params['name']} in the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['new_commands'],
                                'description': params['description'],
                                'tags': params['tags'],
                                'repositories': params['repositories'],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'python': params['python'],
                                'venv': params['venv'],
                                'raise_errors': params['raise_errors']
                            }
                        },
                        'virtualenvs': {
                            params['venv']: join(f, params['venv'])
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_from_python_scripts(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'new_commands': ['git fetch --all --tags --prune', 'git pull'],
            'commands': [
                'from random import choice\n'
                'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                '    f.write("".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '
                'for _ in range({KEY_LEN})]))',
                'from os import getcwd\n'
                'from os.path import join, exists\n'
                'from shutil import copyfile\n'
                'for repo, details in {__repos__}.items():\n'
                '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
            ],
            'tags': ['a', 'b'],
            'description': "Generates an encryption key",
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': False,
            'venv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'description': "test",
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'tags': [],
                                    'venv': None,
                                    'python': True,
                                    'verbose': False
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-c', params['new_commands'][0],
                    '-c', params['new_commands'][1],
                    '-d', params['description'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-s', '-e', '-np'
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Successfully updated command {params['name']} in the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['new_commands'],
                                'description': params['description'],
                                'tags': params['tags'],
                                'repositories': params['repositories'],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'python': params['python'],
                                'venv': params['venv'],
                                'raise_errors': params['raise_errors']
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_with_invalid_python_scripts(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': [
                'from random import choice\n'
                'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                '    f.write("".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '
                'for _ in range({KEY_LEN})]))',
                'from os import getcwd\n'
                'from os.path import join, exists\n'
                'from shutil import copyfile\n'
                'for repo, details in {__repos__}.items():\n'
                '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
            ],
            'invalid_commands': [
                'from random import choice\n'
                'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                '    f.write(".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '  # Missing a "
                'for _ in range({KEY_LEN})]))',
                'from os import getcwd\n'
                'from os.path import join, exists\n'
                'from shutil import copyfile\n'
                'for repo, details in {__repos__}.items():\n'
                '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
            ],
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'python': True,
            'venv': None,
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'description': 'This is a lame description',
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'tags': [],
                                    'python': True,
                                    'venv': None,
                                    'verbose': False
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-c', params['invalid_commands'][0],
                    '-c', params['invalid_commands'][1],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-s', '-e', '-p'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Error: One of the commands in {params['invalid_commands']} is not a valid Python script\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['commands'],
                                'raise_errors': False,
                                'repositories': [],
                                'shell': True,
                                'tags': [],
                                'description': 'This is a lame description',
                                'venv': None,
                                'python': True,
                                'verbose': False
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_python_flag_but_not_python_commands(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': [
                'from random import choice\n'
                'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                '    f.write("".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '
                'for _ in range({KEY_LEN})]))',
                'from os import getcwd\n'
                'from os.path import join, exists\n'
                'from shutil import copyfile\n'
                'for repo, details in {__repos__}.items():\n'
                '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
            ],
            'tags': ['a', 'b'],
            'repositories': ['gameta'],
            'verbose': True,
            'shell': True,
            'venv': None,
            'python': False,
            'description': "Hello world",
            'raise_errors': True
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'raise_errors': False,
                                    'repositories': [],
                                    'shell': True,
                                    'tags': [],
                                    'venv': None,
                                    'description': '',
                                    'python': True,
                                    'verbose': False
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-r', params['repositories'][0],
                    '-v', '-s', '-e', '-np'
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Error: Python flag was unset but one of the commands in {params['commands']} is still Python "
                f"compilable\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['commands'],
                                'description': '',
                                'venv': None,
                                'raise_errors': False,
                                'repositories': [],
                                'shell': True,
                                'tags': [],
                                'python': True,
                                'verbose': False
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_partial_update(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': ['a', 'b'],
            'repositories': [],
            'verbose': False,
            'shell': True,
            'python': False,
            'description': 'Hello world',
            'venv': None,
            'raise_errors': False
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'raise_errors': params['raise_errors'],
                                    'repositories': params['repositories'],
                                    'shell': params['shell'],
                                    'tags': [],
                                    'description': params['description'],
                                    'venv': params['venv'],
                                    'python': params['python'],
                                    'verbose': params['verbose']
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1]
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Successfully updated command {params['name']} in the command store\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['commands'],
                                'description': params['description'],
                                'python': params['python'],
                                'venv': params['venv'],
                                'tags': params['tags'],
                                'repositories': params['repositories'],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'raise_errors': params['raise_errors']
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_invalid_tags(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': ['hello', 'b', 'a'],
            'repositories': [],
            'verbose': False,
            'shell': True,
            'venv': None,
            'description': 'Hello world',
            'python': False,
            'raise_errors': False
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta_other_repos'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': params['commands'],
                                    'raise_errors': params['raise_errors'],
                                    'repositories': params['repositories'],
                                    'shell': params['shell'],
                                    'tags': [],
                                    'verbose': params['verbose'],
                                    'python': params['python'],
                                    'description': params['description'],
                                    'venv': params['venv']
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-t', params['tags'][0],
                    '-t', params['tags'][1],
                    '-t', params['tags'][2]
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Error: One of the tags in {params['tags']} has not been added, please run "
                f"`gameta tags add` to add it first\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'GitPython': {
                                '__metarepo__': False,
                                'path': 'GitPython',
                                'tags': ['a', 'b', 'c'],
                                'url': 'https://github.com/gitpython-developers/GitPython.git'
                            },
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            },
                            'gitdb': {
                                '__metarepo__': False,
                                'path': 'core/gitdb',
                                'tags': ['a', 'c', 'd'],
                                'url': 'https://github.com/gitpython-developers/gitdb.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': params['commands'],
                                'description': params['description'],
                                'tags': [],
                                'repositories': params['repositories'],
                                'venv': params['venv'],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'python': params['python'],
                                'raise_errors': params['raise_errors']
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_invalid_command_configuration(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune', 'git pull'],
            'tags': [],
            'repositories': ['gitdb', 'GitPython'],
            'verbose': False,
            'shell': False,
            'python': False,
            'raise_errors': False
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': ['git fetch --all --tags --prune'],
                                    'raise_errors': params['raise_errors'],
                                    'repositories': [],
                                    'shell': False,
                                    'tags': params['tags'],
                                    'python': False,
                                    'description': "hello world",
                                    'venv': None,
                                    'verbose': params['verbose']
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-c', params['commands'][1],
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Error: Multiple CLI commands requires shell param to be True\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': ['git fetch --all --tags --prune'],
                                'python': False,
                                'description': "hello world",
                                'venv': None,
                                'tags': [],
                                'repositories': [],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'raise_errors': params['raise_errors']
                            }
                        }
                    }
                )

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_update_nonexistent_venv(self, mock_ensure_object):
        params = {
            'name': 'hello_world',
            'commands': ['git fetch --all --tags --prune'],
            'tags': [],
            'repositories': ['gitdb', 'GitPython'],
            'verbose': False,
            'shell': False,
            'python': False,
            'raise_errors': False,
            'venv': 'test'
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output.update(
                        {
                            'commands': {
                                'hello_world': {
                                    'commands': ['git fetch --all --tags --prune'],
                                    'raise_errors': params['raise_errors'],
                                    'repositories': [],
                                    'shell': False,
                                    'tags': params['tags'],
                                    'python': False,
                                    'description': "hello world",
                                    'venv': None,
                                    'verbose': params['verbose']
                                }
                            }
                        }
                    )
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(
                self.update,
                [
                    '-n', params['name'],
                    '-c', params['commands'][0],
                    '-ve', params['venv']
                ]
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(
                result.output,
                f"Updating command {params['name']} in the command store\n"
                f"Error: Virtualenv {params['venv']} has not been registered, please run `gameta venv register` to "
                f"register it first\n"
            )
            self.assertTrue(exists(join(f, '.meta')))
            with open(join(f, '.meta'), 'r') as m:
                self.assertEqual(
                    json.load(m),
                    {
                        'repositories': {
                            'gameta': {
                                '__metarepo__': True,
                                'path': '.',
                                'tags': ['metarepo'],
                                'url': 'git@github.com:genius-systems/gameta.git'
                            }
                        },
                        'commands': {
                            'hello_world': {
                                'commands': ['git fetch --all --tags --prune'],
                                'python': False,
                                'description': "hello world",
                                'venv': None,
                                'tags': [],
                                'repositories': [],
                                'verbose': params['verbose'],
                                'shell': params['shell'],
                                'raise_errors': params['raise_errors']
                            }
                        }
                    }
                )


class TestCommandLs(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.ls = ls

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_ls_no_commands_in_command_store(self, mock_ensure_object):
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            copyfile(join(dirname(__file__), 'data', '.meta'), join(f, '.meta'))
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.ls)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.output, '')

    @patch('gameta.cli.click.Context.ensure_object')
    def test_command_ls_all_commands(self, mock_ensure_object):
        params = {
            'commands': {
                'hello_world': {
                    'commands': ['git fetch --all --tags --prune', 'git pull'],
                    'description': 'Fetches source',
                    'tags': [],
                    'repositories': ['gitdb', 'GitPython'],
                    'verbose': False,
                    'shell': False,
                    'python': False,
                    'venv': None,
                    'raise_errors': False
                },
                'hello_world2': {
                    'commands': ['git fetch --all --tags --prune', 'git pull'],
                    'description': 'Fetches source',
                    'tags': [],
                    'repositories': ['gitdb', 'GitPython'],
                    'verbose': False,
                    'shell': False,
                    'python': False,
                    'venv': None,
                    'raise_errors': False
                },
                'hello_world3': {
                    'commands': [
                        'from random import choice\n'
                        'from string import ascii_lowercase, ascii_uppercase, digits, punctuation\n'
                        'with open("{ENCRYPTION_FILE_NAME}", "w") as f:\n'
                        '    f.write("".join([choice(ascii_lowercase + ascii_uppercase + digits + punctuation) '
                        'for _ in range({KEY_LEN})]))',
                        'from os import getcwd\n'
                        'from os.path import join, exists\n'
                        'from shutil import copyfile\n'
                        'for repo, details in {__repos__}.items():\n'
                        '    if not exists(join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}")):\n'
                        '        copyfile("{ENCRYPTION_FILE_NAME}", join(getcwd(), details["path"], "{ENCRYPTION_FILE_NAME}"))'
                    ],
                    'description': 'Generates encryption key',
                    'tags': [],
                    'repositories': ['gitdb', 'GitPython'],
                    'verbose': False,
                    'shell': False,
                    'python': True,
                    'venv': 'test',
                    'raise_errors': False
                }
            }
        }
        with self.runner.isolated_filesystem() as f:
            with zipfile.ZipFile(join(dirname(__file__), 'data', 'git.zip'), 'r') as template:
                template.extractall(f)
            with open(join(dirname(__file__), 'data', '.meta'), 'r') as m1:
                output = json.load(m1)
                with open(join(f, '.meta'), 'w') as m2:
                    output['commands'] = params['commands']
                    output['virtualenvs'] = {'test': join(f, 'test')}
                    json.dump(output, m2)
            context = GametaContext()
            context.project_dir = f
            context.load()
            mock_ensure_object.return_value = context
            result = self.runner.invoke(self.ls)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output,
                "hello_world:\n"
                f"\tdescription: {params['commands']['hello_world']['description']}\n"
                f"\tcommands: {' && '.join(params['commands']['hello_world']['commands'])}\n"
                f"\ttags: {', '.join(params['commands']['hello_world']['tags'])}\n"
                f"\trepositories: {', '.join(params['commands']['hello_world']['repositories'])}\n"
                f"\tvenv: {params['commands']['hello_world']['venv']}\n"
                f"\tverbose: {params['commands']['hello_world']['verbose']}\n"
                f"\tshell: {params['commands']['hello_world']['shell']}\n"               
                f"\tpython: {params['commands']['hello_world']['python']}\n"
                f"\traise_errors: {params['commands']['hello_world']['raise_errors']}\n"
                '\n'
                "hello_world2:\n"
                f"\tdescription: {params['commands']['hello_world2']['description']}\n"
                f"\tcommands: {' && '.join(params['commands']['hello_world2']['commands'])}\n"
                f"\ttags: {', '.join(params['commands']['hello_world2']['tags'])}\n"
                f"\trepositories: {', '.join(params['commands']['hello_world2']['repositories'])}\n"
                f"\tvenv: {params['commands']['hello_world2']['venv']}\n"
                f"\tverbose: {params['commands']['hello_world2']['verbose']}\n"
                f"\tshell: {params['commands']['hello_world2']['shell']}\n"
                f"\tpython: {params['commands']['hello_world2']['python']}\n"
                f"\traise_errors: {params['commands']['hello_world2']['raise_errors']}\n"
                '\n'
                'hello_world3:\n'
                f"\tdescription: {params['commands']['hello_world3']['description']}\n"
                f"\tcommands: {' && '.join(params['commands']['hello_world3']['commands'])}\n"
                f"\ttags: {', '.join(params['commands']['hello_world3']['tags'])}\n"
                f"\trepositories: {', '.join(params['commands']['hello_world3']['repositories'])}\n"
                f"\tvenv: {params['commands']['hello_world3']['venv']}\n"
                f"\tverbose: {params['commands']['hello_world3']['verbose']}\n"
                f"\tshell: {params['commands']['hello_world3']['shell']}\n"
                f"\tpython: {params['commands']['hello_world3']['python']}\n"
                f"\traise_errors: {params['commands']['hello_world3']['raise_errors']}\n"
                '\n'
            )
