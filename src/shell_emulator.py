import zipfile
import os
import configparser
import datetime
from zipfile import ZipFile
import tkinter as tk
from tkinter import scrolledtext

class ShellEmulator:
    def __init__(self, output_widget):
        # Чтение конфигурации из .ini файла
        config = configparser.ConfigParser()
        config.read('config.ini')

        # Прочитаем параметры из секции "settings"
        self.user = config['settings']['user']
        system_zip = config['settings']['system_file']
        self.system = ZipFile(system_zip)
        self.system_name = system_zip
        self.path_obj = zipfile.Path(self.system)
        self.path = self.path_obj.name
        self.output_widget = output_widget

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
            self.output_widget.insert(tk.END, file.name + ('/' if file.is_dir() else '') + '\n')

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
                    self.output_widget.insert(tk.END, f'No such file or directory: {str(temp)[len(self.system_name):]}\n')
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
        self.output_widget.insert(tk.END, f"{file_path} created or updated\n")

    # Команда who - выводит текущего пользователя и время входа
    def who(self):
        # Используем os для получения текущего пользователя
        login_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        self.output_widget.insert(tk.END, f"{self.user}  pts/0        {login_time} (localhost)\n")

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
        self.output_widget.insert(tk.END, f"Total disk usage: {total_size} bytes\n")

def execute_command(shell, command):
    com = command.split(" ")
    if com[0] == "ls":
        shell.ls()
    elif com[0] == "cd" and len(com) == 2:
        shell.cd(' '.join(com[1:]))
    elif com[0] == "tree":
        shell.system.printdir()
    elif com[0] == "echo" and len(com) == 2:
        shell.output_widget.insert(tk.END, com[1] + '\n')
    elif com[0] == "touch" and len(com) == 2:
        shell.touch(com[1])
    elif com[0] == "who":
        shell.who()
    elif com[0] == "du":
        shell.du()
    elif com[0] == "exit":
        shell.output_widget.insert(tk.END, 'Exiting...\n')
        return False
    else:
        shell.output_widget.insert(tk.END, f"Unknown command: {com[0]}\n")

    # Update the current path based on the shell's path object
    shell.path = shell.create_path(str(shell.path_obj)[len(shell.system_name):])
    return True

def on_enter(event, shell, entry, output):
    command = entry.get()
    entry.delete(0, tk.END)
    output.insert(tk.END, f"{shell.user}@virtual_shell:{shell.create_path(shell.path)}$ {command}\n")
    if not execute_command(shell, command):
        root.quit()

root = tk.Tk()
root.title("Virtual Shell")

output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output.pack(padx=10, pady=10)

entry = tk.Entry(root, width=80)
entry.pack(padx=10, pady=10)
entry.bind("<Return>", lambda event: on_enter(event, shell, entry, output))

shell = ShellEmulator(output)

root.mainloop()
