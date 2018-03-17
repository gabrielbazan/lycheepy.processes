from os import listdir, makedirs
from os.path import join, basename, isfile, exists, splitext
import sys
from importlib import import_module
import inspect
from ftp import Ftp


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

    def get(self, identifier, local_dir):
        remote_process_dir = self._get_remote_process_directory(identifier)
        local_process_dir = join(local_dir, identifier)
        self._create_local_directory(local_process_dir)
        with self.connection:
            self.connection.download_directory_contents(remote_process_dir, local_process_dir)
        self._create_ini_file(local_process_dir)
        return local_process_dir

    def remove(self, identifier):
        with self.connection:
            self.connection.delete_directory(self._get_remote_process_directory(identifier))

    def get_instance(self, identifier, local_path):
        local_process_dir = self.get(identifier, local_path)

        module_name = self.get_local_process_file(local_process_dir)

        sys.path.insert(0, local_process_dir)
        import_module(module_name)

        class_name = self.to_camel_case(module_name)

        instance = None
        for name, _class in inspect.getmembers(sys.modules[module_name], inspect.isclass):
            if _class.__name__ == class_name or _class.__name__ == identifier:
                instance = _class()

        return instance

    @staticmethod
    def to_camel_case(string):
        return ''.join(x.capitalize() or '_' for x in string.split('_'))

    @staticmethod
    def get_local_process_file(local_process_dir):
        process_file = '.'
        for f in listdir(local_process_dir):
            if isfile(join(local_process_dir, f)) and f != '__ini__.py':
                process_file = f
        return splitext(process_file)[0]

    def _get_remote_process_directory(self, identifier):
        return join(self.remote_directory, identifier)

    @staticmethod
    def _create_local_directory(directory):
        if not exists(directory):
            makedirs(directory)

    def _create_ini_file(self, directory):
        open(join(directory, '__ini__.py'), 'a').close()
