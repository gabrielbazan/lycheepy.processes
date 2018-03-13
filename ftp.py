import os
from ftplib import FTP, error_perm


class Ftp(object):

    def __init__(self, ip, username, password, timeout):
        self.connection = FTP(ip, timeout=timeout)
        self.connection.login(user=username, passwd=password)

    def __enter__(self):
        return self

    def __exit__(self, kind, value, tb):
        self.close()

    def close(self):
        self.connection.quit()

    def upload_files(self, files, source, destination):
        for filename in files:
            self.connection.storbinary(
                'STOR ' + os.path.join(destination, filename),
                open(os.path.join(source, filename), 'rb')
            )

    def download_file(self, remote_path, local_path):
        self.connection.retrbinary('RETR ' + remote_path, open(local_path, 'wb').write)

    def upload_file(self, local_path, remote_path):
        self.connection.storbinary('STOR ' + remote_path, open(local_path, 'rb'))

    def get_files_in_directory(self, directory):
        file_list = []
        for element in list(self.connection.nlst(directory)):
            try:
                self.connection.cwd(element)
            except error_perm:
                file_list.append(os.path.basename(element))
        return file_list

    def directory_exist(self, path):
        current_path = self.connection.pwd()
        exists = True
        try:
            self.connection.cwd(path)
        except Exception:
            exists = False
        finally:
            self.connection.cwd(current_path)
            return exists

    def create_directory(self, path):
        self.connection.mkd(path)

    def delete_file(self, path):
        self.connection.delete(path)

    def delete_directory(self, path):
        self.connection.rmd(path)

    def is_up(self):
        try:
            self.connection.retrlines('LIST')
        except Exception:
            return False
        return True
