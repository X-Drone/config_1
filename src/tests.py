import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import zipfile
from zipfile import ZipFile
import configparser
import datetime
import tkinter as tk
from tkinter import scrolledtext
from shell_emulator import ShellEmulator, execute_command, on_enter

class TestShellEmulator(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='[settings]\nuser=test_user\nsystem_file=test_system.tar')
    def setUp(self, mock_file):
        # Создаем временный ZIP-архив для тестирования
        self.zip_name = 'test_system.tar'
        with ZipFile(self.zip_name, 'w') as zipf:
            zipf.writestr('file1.txt', 'content1')
            zipf.writestr('dir1/file2.txt', 'content2')

        # Создаем экземпляр ShellEmulator
        self.output_widget = MagicMock()
        self.shell = ShellEmulator(self.output_widget)

    def tearDown(self):
        # Удаляем временный ZIP-архив после тестирования
        self.shell.system.close()
        os.remove(self.zip_name)

    def test_ls(self):
        self.shell.ls()
        self.output_widget.insert.assert_any_call(tk.END, 'file1.txt\n')
        self.output_widget.insert.assert_any_call(tk.END, 'dir1/\n')

    def test_cd(self):
        self.shell.cd('/dir1')
        self.assertEqual(str(self.shell.path_obj), 'test_system.tar/dir1/')

        self.shell.cd('..')
        self.assertEqual(str(self.shell.path_obj), 'test_system.tar/')

        self.shell.cd('/dir1/..')
        self.assertEqual(str(self.shell.path_obj), 'test_system.tar/')

    def test_touch(self):
        self.shell.touch('newfile.txt')
        self.output_widget.insert.assert_called_with(tk.END, '/newfile.txt/ created or updated\n')

        with ZipFile(self.zip_name, 'r') as zipf:
            self.assertIn('newfile.txt', zipf.namelist())

    def test_who(self):
        self.shell.who()
        login_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        self.output_widget.insert.assert_called_with(tk.END, f"test_user  pts/0        {login_time} (localhost)\n")

    def test_du(self):
        self.shell.du()
        self.output_widget.insert.assert_called_with(tk.END, 'Total disk usage: 16 bytes\n')

if __name__ == '__main__':
    unittest.main()
