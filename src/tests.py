import unittest
from unittest.mock import patch, mock_open
import os
import zipfile
from zipfile import ZipFile
import configparser
import datetime
from shell_emulator import shell_emulator

class TestShellEmulator(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='[settings]\nuser=test_user\nsystem_file=test_system.tar')
    def setUp(self, mock_file):
        # Создаем временный ZIP-архив для тестирования
        self.zip_name = 'test_system.tar'
        with ZipFile(self.zip_name, 'w') as zipf:
            zipf.writestr('file1.txt', 'content1')
            zipf.writestr('dir1/file2.txt', 'content2')

        # Создаем экземпляр shell_emulator
        self.shell = shell_emulator()

    def tearDown(self):
        # Удаляем временный ZIP-архив после тестирования
        self.shell.system.close()
        os.remove(self.zip_name)

    def test_ls(self):
        with patch('builtins.print') as mock_print:
            self.shell.ls()
            mock_print.assert_any_call('file1.txt')
            mock_print.assert_any_call('dir1/')

    def test_cd(self):
        self.shell.cd('/dir1')
        self.assertEqual(str(self.shell.path_obj), 'test_system.tar/dir1/')

        self.shell.cd('..')
        self.assertEqual(str(self.shell.path_obj), 'test_system.tar/')

        self.shell.cd('/dir1/..')
        self.assertEqual(str(self.shell.path_obj), 'test_system.tar/')

    def test_touch(self):
        with patch('builtins.print') as mock_print:
            self.shell.touch('newfile.txt')
            mock_print.assert_called_with('/newfile.txt/ created or updated')

            with ZipFile(self.zip_name, 'r') as zipf:
                self.assertIn('newfile.txt', zipf.namelist())

    def test_who(self):
        with patch('builtins.print') as mock_print:
            self.shell.who()
            login_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            mock_print.assert_called_with(f"test_user  pts/0        {login_time} (localhost)")

    def test_du(self):
        with patch('builtins.print') as mock_print:
            self.shell.du()
            mock_print.assert_called_with('Total disk usage: 16 bytes')

if __name__ == '__main__':
    unittest.main()