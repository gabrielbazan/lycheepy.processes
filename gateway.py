from os import listdir, makedirs
from os.path import join, basename, isfile, exists, splitext
import sys
from shutil import rmtree
from importlib import import_module
import inspect
from ftp import Ftp


def to_camel_case(string):
    return ''.join(x.capitalize() or '_' for x in string.split('_'))


class ProcessContext(object):

    def __init__(self, identifier, local_directory):
        self.identifier = identifier
        self.local_directory = local_directory
        self.instance = None

    def __enter__(self):
        self.create_ini_file()

        sys.path.insert(0, self.local_directory)

        module_name = self.get_local_process_file()
        import_module(module_name)
        class_name = to_camel_case(module_name)

        for name, _class in inspect.getmembers(sys.modules[module_name], inspect.isclass):
            if _class.__name__ == class_name or _class.__name__.lower() == self.identifier.lower():
                self.instance = _class()

        assert self.instance, 'Could not find process class'

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.path.remove(self.local_directory)
        rmtree(self.local_directory)

    def create_ini_file(self):
        open(join(self.local_directory, '__ini__.py'), 'a').close()

    def get_local_process_file(self):
        process_file = '.'
        for f in listdir(self.local_directory):
            if isfile(join(self.local_directory, f)) and f != '__ini__.py':
                process_file = f
        return splitext(process_file)[0]

    def get_process_instance(self):
        return self.instance


class ProcessesGateway(object):

    def __init__(self, host, user, password, timeout, directory):
        self.connection = Ftp(host, user, password, timeout)
        self.remote_directory = directory

    def add(self, identifier, process_file_path):
        with self.connection:
            process_directory = self._get_remote_process_directory(identifier)
            remote_file_path = join(process_directory, basename(process_file_path))
            self.connection.create_directory_if_not_exists(self.remote_directory)
            self.connection.create_directory_if_not_exists(process_directory)
            self.connection.upload_file(process_file_path, remote_file_path)

    def get(self, identifier, local_directory):
        remote_process_dir = self._get_remote_process_directory(identifier)
        local_process_dir = join(local_directory, identifier)
        self._create_local_directory(local_process_dir)
        with self.connection:
            self.connection.download_directory_contents(remote_process_dir, local_process_dir)
        return local_process_dir

    def remove(self, identifier):
        with self.connection:
            self.connection.delete_non_empty_directory(self._get_remote_process_directory(identifier))

    def get_process_context(self, identifier, local_directory):
        local_directory = self.get(identifier, local_directory)
        return ProcessContext(identifier, local_directory)

    def _get_remote_process_directory(self, identifier):
        return join(self.remote_directory, identifier)

    @staticmethod
    def _create_local_directory(directory):
        if not exists(directory):
            makedirs(directory)
