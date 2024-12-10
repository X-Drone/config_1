import zipfile
import os
import configparser
import datetime
from zipfile import ZipFile


class shell_emulator:
    def __init__(self):
        # Чтение конфигурации из .ini файла
        config = configparser.ConfigParser()
        config.read('config.ini')

        # Прочитаем параметры из секции "system"
        self.user = config['settings']['user']
        system_zip = config['settings']['system_file']
        self.system = ZipFile(system_zip)
        self.system_name = system_zip
        self.path_obj = zipfile.Path(self.system)
        self.path = self.path_obj.name

    def sawed_off_path(self, path):
        path = self.create_path(path)
        self.path = path[:-1]

        for i in range(len(self.path) - 1, -1, -1):
            if self.path[i] == "/":
                return self.path
            self.path = self.path[:-1]
        return self.path

    def create_path(self, path):
        if path == "":
            return "/"
        if path[-1] != "/":
            path = path + "/"
        if path[0] != "/":
            path = "/" + path
        return path

    def ls(self):
        files = list(self.path_obj.iterdir())
        for file in files:
            print(file.name + ('/' if file.is_dir() else ''))

    def cd(self, path):
        # Получаем текущую директорию
        temp = self.path_obj

        if path.startswith('/'):
            temp = zipfile.Path(self.system)

        # Разбиваем путь на части по символу '/'
        for part in path.split('/'):
            if part == '' or part == '.':
                # Пустая строка или '.' не изменяют путь
                continue
            elif part == '..':
                # '..' - поднимаемся на уровень выше, если это возможно
                if temp == zipfile.Path(self.system):
                    # Если мы находимся в корне, не можем подняться выше
                    continue
                temp = temp.parent
            else:
                # Иначе пытаемся перейти в указанный каталог
                temp = temp / part
                # Проверяем, существует ли такой файл или каталог
                if not temp.exists():
                    print(f'No such file or directory: {str(temp)[len(self.system_name):]}')
                    return

        # После выполнения всех шагов, temp будет содержать нужный путь
        self.path_obj = temp
        #print(f'Current directory: {self.path_obj}')

    # Команда touch - создание нового файла
    def touch(self, filename):
        # Создаем путь к файлу
        file_path = self.create_path(self.path + filename)
        #print(file_path)

        # Создаем временный ZIP-архив для записи обновлений
        tmp_file = self.system_name[:-4] + '.tmp.tar'
        tmp = zipfile.ZipFile(tmp_file, mode='w')

        # Переносим все файлы из текущего архива в новый
        for file in self.system.infolist():
            tmp.writestr(file.filename, self.system.read(file.filename))

        # Добавляем или обновляем новый файл
        tmp.writestr(file_path[1:-1], b'')  # Пустой файл

        tmp.close()

        # Заменяем старый архив на новый
        self.system.close()
        os.remove(self.system_name)
        os.rename(tmp_file, self.system_name)
        self.system = ZipFile(self.system_name)  # Перезагружаем архив
        self.cd(self.path)
        print(f"{file_path} created or updated")

    # Команда who - выводит текущего пользователя и время входа
    def who(self):
        # Используем os для получения текущего пользователя
        login_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        print(f"{self.user}  pts/0        {login_time} (localhost)")

    # Команда du - выводит размер файлов в текущем каталоге
    def du(self):
        total_size = 0

        # Функция для рекурсивного обхода всех файлов и директорий
        def get_size(path):
            nonlocal total_size
            if path.is_file():
                total_size += len(path.read_bytes())
            elif path.is_dir():
                for subpath in path.iterdir():
                    get_size(subpath)

        # Запуск рекурсивной функции с текущего каталога
        get_size(self.path_obj)
        print(f"Total disk usage: {total_size} bytes")


if __name__ == '__main__':
    shell = shell_emulator()

    while True:
        try:
            com = input(f"{shell.user}@virtual_shell:{shell.create_path(shell.path)}$ ").split(" ")

            if com[0] == "ls":
                shell.ls()
            elif com[0] == "cd" and len(com) == 2:
                shell.cd(' '.join(com[1:]))
            elif com[0] == "tree":
                shell.system.printdir()
            elif com[0] == "echo" and len(com) == 2:
                print(com[1])
            elif com[0] == "touch" and len(com) == 2:
                shell.touch(com[1])
            elif com[0] == "who":
                shell.who()
            elif com[0] == "du":
                shell.du()
            elif com[0] == "exit":
                print('Exiting...')
                break
            else:
                print(f"Unknown command: {com[0]}")

            # Update the current path based on the shell's path object
            shell.path = shell.create_path(str(shell.path_obj)[len(shell.system_name):])

        except KeyboardInterrupt:
            break
