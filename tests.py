import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import configparser
import zipfile
from io import BytesIO
import datetime
from shell_emulator import shell_emulator


class TestShellEmulator(unittest.TestCase):

    def setUp(self):
        # Создаем фейковый .ini файл с настройками
        self.ini_content = """
        [settings]
        user = testuser
        system_file = test_system.tar
        """

        # Мокаем создание и чтение конфигурационного файла
        with patch('builtins.open', mock_open(read_data=self.ini_content)):
            config = configparser.ConfigParser()
            config.read('config.ini')

        # Извлекаем значения из конфигурационного файла
        self.user = config.get('settings', 'user')
        self.system_file = config.get('settings', 'system_file')

        # Инициализируем объект shell_emulator с параметрами из конфигурации
        self.shell = shell_emulator()
        self.shell.user = self.user
        self.shell.system_name = self.system_file

        # Создаем тестовый архив .tar в памяти
        self.test_tar = BytesIO()
        with zipfile.ZipFile(self.test_tar, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("test.txt", "Hello, world!")  # Добавим файл test.txt в архив

        # Открываем архив .tar в режиме добавления
        self.shell.system = zipfile.ZipFile(self.test_tar, 'a')
        self.shell.path_obj = zipfile.Path(self.shell.system)
        self.shell.path = self.shell.path_obj.name

    def tearDown(self):
        """Метод для очистки после каждого теста."""
        self.config_patch.stop()

    def test_ls(self):
        """Тестируем команду ls."""
        # Мокаем итерацию по файлам в архиве
        mock_files = [zipfile.Path(self.shell.system, "test.txt"), zipfile.Path(self.shell.system, "another_file.txt")]
        self.shell.path_obj.iterdir = MagicMock(return_value=mock_files)

        with patch('builtins.print') as mocked_print:
            self.shell.ls()
            mocked_print.assert_any_call("test.txt")
            mocked_print.assert_any_call("another_file.txt")

    def test_cd(self):
        """Тестируем команду cd."""
        # Мокаем методы перехода по каталогам
        self.shell.path_obj = zipfile.Path(self.shell.system)
        self.shell.path_obj.is_dir = MagicMock(return_value=True)
        self.shell.path_obj.exists = MagicMock(return_value=True)

        with patch('builtins.print') as mocked_print:
            self.shell.cd("/test_folder")
            mocked_print.assert_not_called()  # Не должно быть ошибок

        # Проверим, что путь изменился
        self.assertEqual(str(self.shell.path_obj), '/test_folder')

    def test_cd_invalid(self):
        """Тестируем команду cd с недействительным путем."""
        # Мокаем ситуацию, когда папки не существует
        self.shell.path_obj.exists = MagicMock(return_value=False)

        with patch('builtins.print') as mocked_print:
            self.shell.cd("/nonexistent_folder")
            mocked_print.assert_called_with("No such file or directory: /nonexistent_folder")

    def test_touch(self):
        """Тестируем команду touch."""
        # Мокаем добавление файла в архив
        with patch.object(self.shell.system, 'open', mock_open()) as mock_file:
            self.shell.touch("new_file.txt")
            mock_file.assert_called_once_with('new_file.txt', 'w')

    def test_who(self):
        """Тестируем команду who."""
        # Мокаем вывод времени входа
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        with patch('builtins.print') as mocked_print:
            self.shell.who()
            mocked_print.assert_called_with(f"{self.shell.user}  pts/0        {current_time} (localhost)")

    def test_du(self):
        """Тестируем команду du для расчета размера."""
        # Мокаем подсчет размера файлов в архиве
        mock_file = MagicMock()
        mock_file.is_file = True
        mock_file.read_bytes = MagicMock(return_value=b'Hello, world!')
        self.shell.path_obj.iterdir = MagicMock(return_value=[mock_file])

        with patch('builtins.print') as mocked_print:
            self.shell.du()
            mocked_print.assert_called_with("Total disk usage: 13 bytes")

    def test_sawed_off_path(self):
        """Тестируем метод sawed_off_path."""
        self.shell.path = "/home/user/docs/"
        result = self.shell.sawed_off_path(self.shell.path)
        self.assertEqual(result, "/home/user")

    def test_create_path(self):
        """Тестируем метод create_path."""
        # Тестируем создание путей
        self.assertEqual(self.shell.create_path("docs"), "/docs/")
        self.assertEqual(self.shell.create_path("/home/docs"), "/home/docs/")
        self.assertEqual(self.shell.create_path(""), "/")

    def test_touch_with_path(self):
        """Тестируем команду touch с учетом пути."""
        # Мокаем добавление файла в архив с путем
        with patch.object(self.shell.system, 'open', mock_open()) as mock_file:
            self.shell.touch("/docs/new_file.txt")
            mock_file.assert_called_once_with('docs/new_file.txt', 'w')

    def test_cd_to_root(self):
        """Тестируем команду cd в корневую директорию."""
        self.shell.cd("/")
        self.assertEqual(str(self.shell.path_obj), '/')

    def test_ls_empty(self):
        """Тестируем команду ls для пустой директории."""
        # Мокаем ситуацию, когда в каталоге нет файлов
        self.shell.path_obj.iterdir = MagicMock(return_value=[])
        with patch('builtins.print') as mocked_print:
            self.shell.ls()
            mocked_print.assert_not_called()  # Ничего не выводится

if __name__ == '__main__':
    unittest.main()
