import os
from ftp import Ftp


class ProcessesGateway(object):

    def __init__(self, host, user, password, timeout, directory):
        self.connection = Ftp(host, user, password, timeout)
        self.directory = directory

    def add(self, process_file_path):
        with self.connection:
            if not self.connection.directory_exist(self.directory):
                self.connection.create_directory(self.directory)
            self.connection.upload_file(
                process_file_path,
                os.path.join(self.directory, os.path.basename(process_file_path))
            )

    def get(self, remote_file_path, local_destination_path):
        with self.connection:
            self.connection.download_file(remote_file_path, local_destination_path)

    def remove(self, remote_file_path):
        with self.connection:
            self.connection.delete_file(remote_file_path)
