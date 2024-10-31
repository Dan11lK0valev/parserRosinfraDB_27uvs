import os
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time

# драйвер для открытия браузера
path_edge_driver = 'edgedriver_win64/msedgedriver.exe'
# ссылка к первой странице базы проектов (сортировка по актуальности)
project_base_link = 'https://dpo.rosinfra.ru/base-projects?filters=%7B"order"%3A"desc,created_at"%7D&page=1'
# project_base_link = 'https://dpo.rosinfra.ru/base-projects?page=1'

# файл персональных настроек
settings_file = 'settings.txt'
logging = 'log_file.txt'

# Коды для стилизации
RESET = "\033[0m"  # Сброс всех стилей
BOLD = "\033[1m"  # Жирный шрифт
RED = "\033[31m"  # Красный цвет текста
GREEN = "\033[32m"  # Зелёный
YELLOW = "\033[33m"  # Жёлтый

# глобальные переменные
old_mode_file = ""
## настраиваемые переменные
project_link_standard1 = 'https://dpo.rosinfra.ru/projects-office/4679/form/questionnaire'
project_link_standard2 = 'https://dpo.rosinfra.ru/projects-office/13642/form/Passport'
name_file_standard1 = "passport_standard_first.xlsx"
name_file_standard2 = "passport_standard_second.xlsx"
name_file_standard_oth = "passport_standard_oth.xlsx"
name_file_data1 = "data_type1.xlsx"
name_file_data2 = "data_type2.xlsx"
name_file_data_oth = "data_type_oth.xlsx"
skip_status = True
timeout_open_page1 = 5
timeout_perform_login1 = 5
timeout_perform_login2 = 10
timesleep_parse_tooltips1 = 0.5
timesleep_parse_tooltips2 = 0.5
timeout_parse_pagination1 = 15
timeout_parse_projects_page1 = 15
timesleep_parse_projects_page1 = 1
timeout_parse_project1 = 10
timeout_parse_project2 = 15
timeout_parse_project3 = 10
timesleep_parse_project1 = 2
timesleep_parse1 = 1


def convert_value(value):
    # Попытка преобразовать значение в bool, int или float
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value  # Оставляем как строку, если не удалось преобразовать


def load_settings(file_path):
    global project_base_link, project_link_standard1, project_link_standard2
    global name_file_standard1, name_file_standard2, name_file_standard_oth, name_file_data1, name_file_data2
    global name_file_data_oth, skip_status, timeout_open_page1, timeout_perform_login1, timeout_perform_login2
    global timesleep_parse_tooltips1, timesleep_parse_tooltips2, timeout_parse_pagination1
    global timeout_parse_projects_page1, timesleep_parse_projects_page1, timeout_parse_project1
    global timeout_parse_project2, timeout_parse_project3, timesleep_parse_project1, timesleep_parse1
    # Объявляем глобальные переменные, которые нужно изменить

    try:
        with open(file_path, 'r') as file:
            for line in file:
                if ":" in line:
                    # Убираем пробелы и разделяем по ":"
                    key, value = map(str.strip, line.split(":", 1))

                    # Присваиваем значение глобальным переменным по названию ключа
                    if key == "project_base_link":
                        project_base_link = value
                    elif key == "project_link_standard1":
                        project_link_standard1 = value
                    elif key == "project_link_standard2":
                        project_link_standard2 = value
                    elif key == "name_file_standard1":
                        name_file_standard1 = value
                    elif key == "name_file_standard2":
                        name_file_standard2 = value
                    elif key == "name_file_standard_oth":
                        name_file_standard_oth = value
                    elif key == "name_file_data1":
                        name_file_data1 = value
                    elif key == "name_file_data2":
                        name_file_data2 = value
                    elif key == "name_file_data_oth":
                        name_file_data_oth = value
                    elif key == "skip_status":
                        skip_status = convert_value(value)
                    elif key == "timeout_open_page1":
                        timeout_open_page1 = convert_value(value)
                    elif key == "timeout_perform_login1":
                        timeout_perform_login1 = convert_value(value)
                    elif key == "timeout_perform_login2":
                        timeout_perform_login2 = convert_value(value)
                    elif key == "timesleep_parse_tooltips1":
                        timesleep_parse_tooltips1 = convert_value(value)
                    elif key == "timesleep_parse_tooltips2":
                        timesleep_parse_tooltips2 = convert_value(value)
                    elif key == "timeout_parse_pagination1":
                        timeout_parse_pagination1 = convert_value(value)
                    elif key == "timeout_parse_projects_page1":
                        timeout_parse_projects_page1 = convert_value(value)
                    elif key == "timesleep_parse_projects_page1":
                        timesleep_parse_projects_page1 = convert_value(value)
                    elif key == "timeout_parse_project1":
                        timeout_parse_project1 = convert_value(value)
                    elif key == "timeout_parse_project2":
                        timeout_parse_project2 = convert_value(value)
                    elif key == "timeout_parse_project3":
                        timeout_parse_project3 = convert_value(value)
                    elif key == "timesleep_parse_project1":
                        timesleep_parse_project1 = convert_value(value)
                    elif key == "timesleep_parse1":
                        timesleep_parse1 = convert_value(value)
        print(f"{GREEN}Персональные настройки успешно загружены!{RESET}\n")

    except FileNotFoundError:
        print(f"{YELLOW}Файл {RESET}{file_path}{YELLOW} не найден.{RESET}")
    except Exception as e:
        print(f"{RED}Ошибка при чтении файла: {e}{RESET}")


class WebParser:
    def __init__(self, verbose=True):
        """Инициализация с выбором браузера и возможностью наблюдения за процессом"""
        self.verbose = verbose

        edge_options = Options()
        if not self.verbose:
            edge_options.add_argument("--headless")
        self.driver = webdriver.Edge(service=Service(path_edge_driver), options=edge_options)

    def open_page(self, url):
        """Открытие страницы с помощью selenium"""
        print(f"Открываем страницу: {url}")
        self.driver.get(url)

        try:
            # Ждем, пока появится хотя бы один элемент с классом 'card-line'
            WebDriverWait(self.driver, timeout_open_page1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'card-line'))
            )
        except Exception as e:
            print(f"Ошибка загрузки страницы: {e}"
                  f"{GREEN}(В ряде случаев можно игнорировать данное сообщение в силу его неточности.){RESET}\n")
        return self.driver

    def perform_login(self, login, password):
        """Авторизация на сайте"""
        try:
            # Ожидаем появления полей email и пароль
            email_field = WebDriverWait(self.driver, timeout_perform_login1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Ваш email"]'))
            )
            password_field = self.driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Пароль"]')

            # Вводим данные
            email_field.send_keys(login)
            password_field.send_keys(password)

            # Находим и кликаем кнопку "Войти"
            login_button = self.driver.find_element(By.XPATH, '//button[contains(text(), "Войти")]')
            login_button.click()

            # Ждем загрузки страницы после входа
            WebDriverWait(self.driver, timeout_perform_login2).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'card-line'))
            )
        except Exception as e:
            print(f"Ошибка при аутентификации: {e}\n"
                  f"{GREEN}(В ряде случаев можно игнорировать данное сообщение в силу его неточности.){RESET}\n")

    def parse_tooltips(self, name):
        """Парсинг элементов tooltip и сохранение их как заголовки таблицы."""
        column_names = ["Ссылка проекта", "Имя проекта", "Страница", "Дата добавления", "Номер проекта"]

        # Поиск всех элементов 'widget'
        widgets = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-v-13aeb537].widget.col-12[col="12"]')

        if name == 'passport_standard_first.xlsx':
            for index, widget in enumerate(widgets, start=1):
                # Если это пятый, седьмой или восьмой виджет, кликаем по заголовку, чтобы раскрыть содержимое
                if index in {5, 7, 8}:
                    header = widget.find_element(By.CSS_SELECTOR, 'div.widget__header')
                    header.click()  # Клик для раскрытия
                    time.sleep(timesleep_parse_tooltips1)  # Небольшая задержка после раскрытия

                # В каждом 'widget' ищем элементы 'tooltip'
                tooltips = widget.find_elements(By.CSS_SELECTOR, 'div[name="tooltip"].tooltip')

                for tooltip in tooltips:
                    # Получаем текст из tooltip и добавляем в список, если он не пустой
                    tooltip_text = tooltip.text
                    if tooltip_text:
                        column_names.append(tooltip_text)

        if name == 'passport_standard_second.xlsx':
            for index, widget in enumerate(widgets, start=1):
                # Если это пятый, седьмой или восьмой виджет, кликаем по заголовку, чтобы раскрыть содержимое
                if index in {2, 3}:
                    header = widget.find_element(By.CSS_SELECTOR, 'div.widget__header')
                    header.click()  # Клик для раскрытия
                    time.sleep(timesleep_parse_tooltips2)  # Небольшая задержка после раскрытия

                # В каждом 'widget' ищем элементы 'tooltip'
                tooltips = widget.find_elements(By.CSS_SELECTOR, 'div[name="tooltip"].tooltip')

                for tooltip in tooltips:
                    # Получаем текст из tooltip и добавляем в список, если он не пустой
                    tooltip_text = tooltip.text
                    if tooltip_text:
                        column_names.append(tooltip_text)

        # Создание DataFrame с названиями столбцов
        df = pd.DataFrame(columns=column_names)
        print("Заголовки таблицы:", df.columns.tolist())
        print(f"Таблица {name} создана.")

        # Сохранение таблицы в xlsx файл
        df.to_excel(name, index=False)
        return df

    def parse_pagination(self):
        """Функция для сбора всех номеров страниц в пагинации."""
        # Ожидание появления элемента пагинации на странице
        try:
            pagination = WebDriverWait(self.driver, timeout_parse_pagination1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.projects-pagination[data-v-2f1e082b]'))
            )

            # Извлекаем все элементы с номерами страниц
            page_links = pagination.find_elements(By.CSS_SELECTOR, 'a.pagination__link')
            page_numbers = [int(link.text) for link in page_links if link.text.isdigit()]

            # Находим максимальный номер страницы
            max_page_number = max(page_numbers)
            # print(f"Максимальный номер страницы: {max_page_number}")

            # Генерируем список URL для всех страниц от 1 до максимальной
            base_url = self.driver.current_url.split("page=")[0]
            page_urls = [f"{base_url}page={i}" for i in range(1, max_page_number + 1)]
            return page_urls

        except Exception as e:
            print(f"Ошибка при парсинге пагинации: {e}")
            return []

    def parse_projects_page(self, page_url, skip, mode):
        """Функция для парсинга страницы проектов по переданному URL."""
        try:
            self.driver.get(page_url)
            print(f"Парсинг страницы: {page_url}")

            # Получаем номер страницы из URL
            current_url = self.driver.current_url
            page_number = int(current_url.split("page=")[-1])

            # Ожидание появления карточек проектов
            project_cards = WebDriverWait(self.driver, timeout_parse_projects_page1).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-v-26bfe514][data-v-2f1e082b].card-line'))
            )
            # print(mode)

            project_cards_links = []

            for card in project_cards:
                try:
                    # Находим третий line-item внутри карточки
                    line_items = card.find_elements(By.CLASS_NAME, 'line-item')
                    if len(line_items) >= 3:
                        project_title_div = line_items[2].find_element(By.CSS_SELECTOR, 'div.project-title.line-title')
                        project_link = project_title_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        project_cards_links.append(project_link)
                except Exception as e:
                    print(f"Ошибка при обработке карточки проекта: {e}")

            # print(project_cards_links)
            if mode == "old":
                df = pd.read_excel(old_mode_file)
                last_row = df.iloc[-1]
                last_project_link = last_row['Ссылка проекта']

                if last_project_link in project_cards_links:
                    pos = project_cards_links.index(last_project_link) + 1
                    if pos >= len(project_cards_links):
                        print("На этой странице все проекты были пропарсены.")
                        return
                    else:
                        print(f"Найдено {len(project_cards)} карточек проектов на странице {page_url}")
                    project_cards_links = project_cards_links[pos:]
                else:
                    print(f"Ссылка {last_project_link} не содержится среди ссылок проектов данной страницы. "
                          f"Проверьте корректность своих данных.")
            # print(project_cards_links)

            for card_link in project_cards_links:
                # Открытие ссылки проекта в новой вкладке
                self.driver.execute_script("window.open(arguments[0]);", card_link)

                # Переключение на новую вкладку
                self.driver.switch_to.window(self.driver.window_handles[1])

                time.sleep(timesleep_parse_projects_page1)
                # Парсим страницу проекта
                self.parse_project(card_link, page_number, skip)
                time.sleep(timesleep_parse_projects_page1)

                # Закрываем вкладку с проектом и возвращаемся на исходную страницу
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

        except Exception as e:
            print(f"Ошибка при поиске карточек проектов на странице: {e}")

    def parse_project(self, project_link, page_number, skip):
        """Парсинг страницы конкретного проекта с учетом открытых виджетов."""
        print(f"Парсинг проекта {project_link}")

        # Ожидание загрузки виджетов
        try:
            passport = True
            # Проверка на наличие паспорта проекта
            try:
                passport_or_questionnaire_link = WebDriverWait(self.driver, timeout_parse_project1).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div.tabs__nav a[href*="Passport"], a[href*="questionnaire"]')))
            except Exception:
                passport = False
                print(f"Проект {project_link} не имеет паспорта")

            WebDriverWait(self.driver, timeout_parse_project2).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-v-13aeb537].widget.col-12[col="12"]'))
            )
            # Находим все виджеты на странице проекта
            widgets = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-v-13aeb537].widget.col-12[col="12"]')
            widget_count = len(widgets)
            # print(f"Количество виджетов: {widget_count}")

            # Выбор файла на основе количества виджетов
            data_files = {8: "data_type1.xlsx", 3: "data_type2.xlsx", 2: "data_type2.xlsx"}
            file_to_use = data_files.get(widget_count, "data_type_oth.xlsx")
            print(f"Выбран файл: {file_to_use} - в соответствии с количеством виджетов: {widget_count}")

            # Открываем выбранную таблицу и читаем заголовки
            df = pd.read_excel(file_to_use)
            column_names = df.columns.tolist()
            # print("Заголовки столбцов:", column_names)

            # Находим название проекта на странице
            project_name = WebDriverWait(self.driver, timeout_parse_project3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-v-29b913d6].project-stage__text'))
            ).text

            # Находим дату добавления и номер проекта
            project_date = self.driver.find_element(By.CSS_SELECTOR,
                                                    'div.project-info__item span.project-info__value').text
            project_number = self.driver.find_element(By.CSS_SELECTOR,
                                                      'div.project-info__item.mb-5 span.project-info__value').text

            new_row = {column_names[0]: project_link, column_names[1]: project_name, column_names[2]: page_number,
                       column_names[3]: project_date, column_names[4]: project_number}

            # Если выбран файл data_type_oth.xlsx, заполняем его только проектной ссылкой, названием, страницей и датой
            if file_to_use == "data_type_oth.xlsx" or not passport:
                # Добавляем новую строку в DataFrame и сохраняем в Excel
                new_row_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_row_df], ignore_index=True)
                df.to_excel(file_to_use, index=False)
                print(f"Проект {project_link} сохранен в базу данных нестандартных по шаблону проектов.")
                return  # Завершаем функцию, так как для этого файла ничего больше не нужно

            # Продолжаем, если используется data_type1.xlsx или data_type2.xlsx
            # Подготовка и заполнение всех виджетов данных (как было описано ранее)

            # Клик по заголовкам закрытых виджетов в зависимости от их индексов
            for index, widget in enumerate(widgets, start=1):
                if (widget_count == 8 and index in {5, 7, 8}) or (widget_count == 3 and index in {2, 3}):
                    header = widget.find_element(By.CSS_SELECTOR, 'div.widget__header')
                    header.click()  # Клик для раскрытия
                    time.sleep(timesleep_parse_project1)  # Небольшая задержка после раскрытия

            # Словарь для сохранения текста из всех виджетов
            all_groups_text = {}

            # Проход по каждому виджету для извлечения данных
            for widget in widgets:
                # Извлекаем текст из tooltip
                tooltips = widget.find_elements(By.CSS_SELECTOR, 'div[name="tooltip"].tooltip')
                tooltips_text = [tooltip.text for tooltip in tooltips]

                # Извлекаем текст из форм
                values = widget.find_elements(By.CSS_SELECTOR,
                                              'div.form-office-group__input')
                values_text = [(value.text if value.text != "Автор не предоставил информацию" else "")
                               for value in values]

                # print(tooltips_text) # проверка заголовков
                # print(values_text) #проверка значений

                # Создаем словарь с парами (название поля: значение)
                groups_text = dict(zip(tooltips_text, values_text))
                all_groups_text.update(groups_text)
            # print(all_groups_text)

            # Проверяем, что каждый ключ из словаря all_groups_text присутствует в списке колонок и вставляем значение
            for key, value in all_groups_text.items():
                if key in column_names:  # Проверяем, что ключ существует в заголовках таблицы
                    new_row[key] = value  # Вставляем значение в соответствующий столбец таблицы
                else:
                    print(f"{YELLOW}Пропущен заголовок: {RESET}{key}{YELLOW}. Нет среди заголовков таблицы.{RESET}")
                    # Отображаем, если заголовок не найден

            # print(new_row)  # Проверяем, что данные корректно вставлены
            new_row_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_row_df], ignore_index=True)
            df.to_excel(file_to_use, index=False)

        except Exception as e:
            print(f"{RED}Ошибка при парсинге проекта {project_link}: {e}{RESET}")
            if not skip:
                sys.exit(f"{BOLD}Завершение работы программы из-за критической ошибки при парсинге проекта. "
                         f"Статус skip: {skip}{RESET}")

    def close(self):
        """Закрытие браузера"""
        self.driver.quit()


def get_latest_file(files):
    """Функция для поиска файла с последней датой изменения."""
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


# Функция для создания копии таблицы passport_standard.xlsx под названием data.xlsx
def create_data_copy():
    """Создает копию таблицы passport_standard.xlsx под названием data_type.xlsx."""
    df = pd.read_excel(name_file_standard1)
    df.to_excel(name_file_data1, index=False)
    df = pd.read_excel(name_file_standard2)
    df.to_excel(name_file_data2, index=False)
    df = pd.read_excel(name_file_standard_oth)
    df.to_excel(name_file_data_oth, index=False)
    print(
        f"{GREEN}Копии таблиц {RESET}{name_file_standard1}{GREEN}, {RESET}{name_file_standard2}{GREEN} и {RESET}{name_file_standard_oth}"
        f"{GREEN} успешно созданы, как {RESET}{name_file_data1}{GREEN}, {RESET}{name_file_data2}{GREEN} и {RESET}{name_file_data_oth}"
    )


# Функция для чтения логина и пароля с проверкой корректности ввода
def get_login_and_password():
    while True:
        user_input = input("Введите логин и пароль через пробел: ")
        parts = user_input.split(" ", maxsplit=1)

        # Проверка, что ровно две части (логин и пароль)
        if len(parts) == 2:
            login, password = parts
            # print(f"Логин: {login}")
            # print(f"Пароль: {password}")
            return login, password
        else:
            print(f"{YELLOW}Ошибка: необходимо ввести ровно два значения — логин и пароль через пробел.{RESET}")


def standard1():
    project_link = project_link_standard1
    login, password = get_login_and_password()

    # Создаем экземпляр WebParser с выбранным браузером
    parser = WebParser(verbose=True)

    driver = parser.open_page(project_link)

    # Проверяем, не требуется ли аутентификация
    if 'login' in driver.current_url:
        print("Требуется аутентификация.")
        # Выполняем аутентификацию через новый метод
        parser.perform_login(login, password)

    # После авторизации или перехода на страницу вызываем метод parse_tooltips
    parser.parse_tooltips(name_file_standard1)

    # Закрываем браузер
    parser.close()


def standard2():
    project_link = project_link_standard2
    login, password = get_login_and_password()

    # Создаем экземпляр WebParser с выбранным браузером
    parser = WebParser(verbose=True)

    driver = parser.open_page(project_link)

    # Проверяем, не требуется ли аутентификация
    if 'login' in driver.current_url:
        print("Требуется аутентификация.")
        # Выполняем аутентификацию через новый метод
        parser.perform_login(login, password)

    # После авторизации или перехода на страницу вызываем метод parse_tooltips
    parser.parse_tooltips(name_file_standard2)

    # Закрываем браузер
    parser.close()


def standard_oth():
    # Создаем экземпляр WebParser с выбранным браузером
    parser = WebParser(verbose=True)

    parser.parse_tooltips(name_file_standard_oth)


def parse():
    login, password = get_login_and_password()

    mode = input("Выберите мод режим для парсинга данных (old - продолжение записи старых данных, new - "
                 "новая запись данных): ")

    if not (mode == "old" or mode == "new"):
        print(f"{YELLOW}Введен неверный мод! Выберете new или old!{RESET}")
        return

    # Создаем экземпляр WebParser с выбранным браузером
    parser = WebParser(verbose=True)

    driver = parser.open_page(project_base_link)

    # Проверяем, не требуется ли аутентификация
    if 'login' in driver.current_url:
        print("Требуется аутентификация.")
        # Выполняем аутентификацию
        parser.perform_login(login, password)

    all_projects_pages = parser.parse_pagination()

    if mode == "old":
        # Ищем самый свежий файл из списка
        files = ["data_type1.xlsx", "data_type2.xlsx", "data_type_oth.xlsx"]
        existing_files = [file for file in files if os.path.exists(file)]

        if not existing_files:
            print("Нет существующих файлов для режима 'old'. Запуск в режиме 'new'.")
            mode = "new"
        else:
            file_to_use = get_latest_file(existing_files)
            global old_mode_file
            old_mode_file = file_to_use
            print(f"Выбран файл для режима 'old': {file_to_use}")

            df = pd.read_excel(file_to_use)
            if df.empty:
                print("Таблица пуста. Переход к режиму 'new'.")
                mode = "new"
            else:
                last_row = df.iloc[-1]
                last_page_number = int(last_row['Страница'])

                # Обрезаем переменную project_base_link до элемента page= и формируем ссылку
                base_link_trimmed = project_base_link.split("page=")[0]
                last_page_url = f"{base_link_trimmed}page={last_page_number}"

                all_projects_pages_numbers = [int(page.split("page=")[-1]) for page in all_projects_pages]
                all_projects_pages_numbers = [page for page in all_projects_pages_numbers if page >= last_page_number]
                sub = len(all_projects_pages) - len(all_projects_pages_numbers)
                all_projects_pages = all_projects_pages[sub:]
                # print(all_projects_pages)
                print(f"Продолжение парсинга со страницы: {last_page_url}.")

    if mode == "new":
        create_data_copy()

    skip = skip_status
    for pages in all_projects_pages:
        parser.parse_projects_page(pages, skip, mode)
        mode = "new"
        time.sleep(timesleep_parse1)

    # Закрываем браузер
    parser.close()


def main():
    # Функция настройки. Если требуется ввести персональные настройки, то нужно раскомментировать данную функцию
    # load_settings(settings_file)

    action = input("Выберите, какое действие вы хотите провести. Среди доступных:\n"
                   "sus1 (set up standard1) - установить стандарт первого типа для таблиц данных,\n"
                   "sus2 (set up standard2) - установить стандарт второго типа для таблиц данных,\n"
                   "suso (set up standard other) - установить стандарт другого типа для таблиц с иными данными,\n"
                   "parse - выполнить парсинг источника RosInfra.\n"
                   "Действие: ")

    # Словарь для выбора действия
    actions = {
        "sus1": standard1,
        "sus2": standard2,
        "suso": standard_oth,
        "parse": parse
    }

    # Выполнение действия на основе выбора
    if action in actions:
        actions[action]()  # Запуск соответствующей функции
    else:
        print(f"{YELLOW}Неверное действие. Пожалуйста, введите{RESET} "
              f"sus1{YELLOW}, {RESET}sus2{YELLOW}, {RESET}suso{YELLOW} или {RESET}parse.")


if __name__ == "__main__":
    main()
