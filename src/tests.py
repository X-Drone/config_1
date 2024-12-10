import unittest
from unittest.mock import patch, mock_open
import zipfile
import os
import configparser
import datetime
from zipfile import ZipFile
from shell_emulator import *

class TestShellEmulator(unittest.TestCase):

    def setUp(self):
        # Создаем временный конфигурационный файл
        self.config_content = """
        [settings]
        user = testuser
        system_file = test_system.zip
        """
        with patch('builtins.open', mock_open(read_data=self.config_content)):
            self.config = configparser.ConfigParser()
            self.config.read('config.ini')

        # Создаем временный ZIP-архив
        self.zip_content = {
            'file1.txt': b'Content of file1',
            'dir1/file2.txt': b'Content of file2',
            'dir2/file3.txt': b'Content of file3'
        }
        self.zip_file = 'test_system.zip'
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            for file, content in self.zip_content.items():
                zf.writestr(file, content)

        # Создаем экземпляр shell_emulator
        self.shell = shell_emulator()

    def tearDown(self):
        # Удаляем временный ZIP-архив
        if os.path.exists(self.zip_file):
            os.remove(self.zip_file)

    def test_create_path(self):
        self.assertEqual(self.shell.create_path(''), '/')
        self.assertEqual(self.shell.create_path('dir1'), '/dir1/')
        self.assertEqual(self.shell.create_path('/dir1'), '/dir1/')
        self.assertEqual(self.shell.create_path('dir1/'), '/dir1/')

    def test_sawed_off_path(self):
        self.assertEqual(self.shell.sawed_off_path('/dir1/dir2/'), '/dir1/dir2')
        self.assertEqual(self.shell.sawed_off_path('/dir1/dir2'), '/dir1')
        self.assertEqual(self.shell.sawed_off_path('/dir1/'), '/dir1')
        self.assertEqual(self.shell.sawed_off_path('/dir1'), '/')

    def test_ls(self):
        with patch('builtins.print') as mocked_print:
            self.shell.ls()
            mocked_print.assert_any_call('file1.txt')
            mocked_print.assert_any_call('dir1/')
            mocked_print.assert_any_call('dir2/')

    def test_cd(self):
        self.shell.cd('/dir1')
        self.assertEqual(str(self.shell.path_obj), '/dir1/')
        self.shell.cd('..')
        self.assertEqual(str(self.shell.path_obj), '/')
        self.shell.cd('/dir2')
        self.assertEqual(str(self.shell.path_obj), '/dir2/')
        self.shell.cd('..')
        self.assertEqual(str(self.shell.path_obj), '/')

    def test_touch(self):
        with patch('builtins.print') as mocked_print:
            self.shell.touch('newfile.txt')
            mocked_print.assert_called_with('/newfile.txt created or updated')
            self.shell.system.close()
            with zipfile.ZipFile(self.zip_file, 'r') as zf:
                self.assertIn('newfile.txt', zf.namelist())

    def test_who(self):
        with patch('builtins.print') as mocked_print:
            self.shell.who()
            mocked_print.assert_called_with(f"testuser  pts/0        {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} (localhost)")

    def test_du(self):
        with patch('builtins.print') as mocked_print:
            self.shell.du()
            total_size = sum(len(content) for content in self.zip_content.values())
            mocked_print.assert_called_with(f"Total disk usage: {total_size} bytes")

if __name__ == '__main__':
    unittest.main()
