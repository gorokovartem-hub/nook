# Nook

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/github/v/release/gorokovartem-hub/nook)

A minimalist Windows utility featuring a taskbar widget and a compact system tray window.

Built with Python and CustomTkinter. The application can follow the Windows system theme or use a custom dark or light theme.

<!-- Add a screenshot here: ![Nook screenshot](docs/screenshot.png) -->

## Download

**`Nook-English.zip`** — a ready-to-use Windows build. Python is not required.

1. Download the archive from [GitHub Releases](https://github.com/gorokovartem-hub/nook/releases).
2. Extract it.
3. Run `Nook-English.exe` or `Nook-Russian.exe`.

Windows SmartScreen or antivirus software may warn you about an unsigned application because Nook uses global hotkeys. The source code is publicly available in this repository.

## Features

### Nook Studio

- **Appearance customization** — 10 predefined themes, custom colors, widget transparency, and rounded corners.
- **Layout profiles** — save and restore widget visibility, modes, and individual card positions.
- **Settings and hotkeys** — configure global shortcuts, Windows autostart, and system behavior directly from the interface.
- **Theme import and export** — transfer appearance settings between configurations.

### Widgets and monitoring

- **Taskbar widget** — CPU and RAM usage with mini-graphs. Full mode also displays GPU, disk, and network activity.
- **Desktop widgets** — independent System, Disks, and Clock cards with magnetic snapping.
- **System monitoring** — CPU, RAM, and GPU load, disk activity, network traffic, and battery status.
- **Disk monitoring** — drive usage and storage activity.
- **Clock and calendar** — current time, date, and calendar information.
- **Internet monitor** — connection status, network traffic, and connection metrics.

### Productivity

- **Focus timer** — Pomodoro sessions of 25 minutes followed by 5-minute breaks, with a longer break after four cycles and a sprint indicator.
- **Notes and tasks** — quick notes, to-do lists, and reminders. Notes appear as separate cards and are saved to `notes.txt`.
- **Quick notes window** — access recent notes from the system tray or by pressing `Ctrl+Alt+N`.
- **Clipboard history** — browse copied entries and click an item to restore it to the clipboard.
- **Quick launcher** — launch applications and shortcuts without extra steps.
- **Music player** — quick access to music and playback controls.
- **Area screenshot** — capture a selected screen area and copy it to the clipboard.

### Widget behavior

- Full and compact taskbar modes.
- Drag-and-drop positioning with magnetic edge snapping.
- Independent positioning of desktop cards.
- Automatic snapping between cards and screen boundaries.
- Detailed tooltips.
- Automatic hiding in fullscreen applications.

## Hotkeys

Global hotkeys can be customized in Settings.

| Shortcut | Action |
|---|---|
| `Ctrl+Alt+C` | Switch to compact widget mode |
| `Ctrl+Alt+F` | Switch to full widget mode |
| `Ctrl+Alt+W` | Show or hide the widget |
| `Ctrl+Alt+N` | Open quick notes |
| `Ctrl+Alt+S` | Capture a screen area |
| `Ctrl+1`–`Ctrl+5` | Switch tabs in the main window |
| `Esc` | Minimize the main window to the system tray |

## Installation from source

### Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- Git

### Setup

```powershell
git clone https://github.com/gorokovartem-hub/nook.git
cd nook

python -m venv .venv
.\.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

## Settings and configuration

Widget positions and modes are stored in `config.json` next to the application. The file is created automatically.

In Nook Studio, you can:

- Choose the system, dark, or light theme.
- Customize colors, widget transparency, and corner radius.
- Configure widget and desktop card visibility.
- Manage global hotkeys and Windows autostart.
- Save and restore layout profiles.

The System, Disks, and Clock desktop cards can be moved independently. They automatically snap to screen edges and to one another.

To restore the default card positions, right-click a card and select **Reset card positions**.

## Building the English version

The repository supports separate Russian and English Windows builds. The English version starts through `main_en.py`, which selects English before loading the interface.

To build it locally on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\build_en.ps1
```

The resulting executable will be located at:

```text
dist\Nook-English\Nook-English.exe
```

Pushing a version tag, such as `v0.3.0`, triggers the GitHub Actions release workflow. It builds both language versions and attaches the following archives to the GitHub Release:

- `Nook-Russian-win64.zip`
- `Nook-English-win64.zip`

## License

[MIT License](LICENSE) © Artem Gorokov

---

# Nook — Русская версия

Минималистичная утилита для Windows: виджет на панели задач и небольшое окно в системном трее.

Программа написана на Python с использованием CustomTkinter. Она поддерживает системную тему Windows, а также тёмное и светлое оформление.

<!-- Добавьте скриншот: ![Скриншот Nook](docs/screenshot.png) -->

## Скачать

**`Nook-Russian.zip`** — готовая сборка для Windows. Устанавливать Python не нужно.

1. Скачайте архив со страницы [GitHub Releases](https://github.com/gorokovartem-hub/nook/releases).
2. Распакуйте архив.
3. Запустите `Nook-Russian.exe` или `Nook-English.exe`.

Windows SmartScreen или антивирус могут предупредить о неподписанном приложении, поскольку Nook использует глобальные горячие клавиши. Исходный код открыт и доступен в этом репозитории.

## Возможности

### Nook Studio

- **Настройка оформления** — 10 готовых тем, выбор цветов, прозрачность виджетов и скругление углов.
- **Профили раскладки** — сохранение и восстановление видимости виджетов, режимов и индивидуальных позиций карточек.
- **Настройки и горячие клавиши** — управление глобальными сочетаниями клавиш, автозапуском Windows и системным поведением.
- **Импорт и экспорт тем** — перенос настроек оформления между конфигурациями.

### Виджеты и мониторинг

- **Виджет на панели задач** — загрузка CPU и RAM с мини-графиками. В полном режиме также отображаются GPU, диск и сеть.
- **Виджеты рабочего стола** — независимые карточки «Система», «Диски» и «Часы» с магнитной привязкой.
- **Мониторинг системы** — загрузка CPU, RAM и GPU, активность дисков, сетевой трафик и состояние батареи.
- **Мониторинг дисков** — заполненность накопителей и активность хранилища.
- **Часы и календарь** — текущее время, дата и календарная информация.
- **Интернет-монитор** — состояние соединения, сетевой трафик и показатели подключения.

### Продуктивность

- **Таймер фокуса** — Pomodoro: 25 минут работы и 5 минут отдыха, длинный перерыв после четырёх циклов и индикатор спринтов.
- **Заметки и задачи** — быстрые записи, списки дел и напоминания. Заметки отображаются отдельными карточками и сохраняются в `notes.txt`.
- **Быстрые заметки** — доступ к последним записям из системного трея или по `Ctrl+Alt+N`.
- **История буфера обмена** — просмотр скопированных данных и восстановление записи нажатием.
- **Быстрый лаунчер** — запуск приложений и ярлыков без лишних действий.
- **Музыкальный плеер** — быстрый доступ к музыке и управлению воспроизведением.
- **Скриншот области** — захват выбранной области экрана с копированием изображения в буфер обмена.

### Поведение виджетов

- Полный и компактный режимы виджета на панели задач.
- Перетаскивание с магнитной привязкой к краям экрана.
- Независимое расположение карточек рабочего стола.
- Автоматическая привязка карточек друг к другу и к границам экрана.
- Подробные всплывающие подсказки.
- Автоматическое скрытие в полноэкранных приложениях.

## Горячие клавиши

Глобальные сочетания клавиш можно изменить в настройках.

| Сочетание | Действие |
|---|---|
| `Ctrl+Alt+C` | Переключить компактный режим виджета |
| `Ctrl+Alt+F` | Переключить полный режим виджета |
| `Ctrl+Alt+W` | Показать или скрыть виджет |
| `Ctrl+Alt+N` | Открыть быстрые заметки |
| `Ctrl+Alt+S` | Сделать скриншот области |
| `Ctrl+1`–`Ctrl+5` | Переключить вкладку главного окна |
| `Esc` | Свернуть главное окно в системный трей |

## Запуск из исходников

### Требования

- Windows 10 или Windows 11
- Python 3.10 или новее
- Git

### Установка

```powershell
git clone https://github.com/gorokovartem-hub/nook.git
cd nook

python -m venv .venv
.\.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

## Настройки и конфигурация

Позиции и режимы виджетов хранятся в файле `config.json` рядом с программой. Он создаётся автоматически.

В Nook Studio можно:

- Выбрать системную, тёмную или светлую тему.
- Настроить цвета, прозрачность виджетов и радиус скругления углов.
- Настроить видимость виджетов и карточек рабочего стола.
- Управлять глобальными горячими клавишами и автозапуском Windows.
- Сохранять и восстанавливать профили раскладки.

Карточки «Система», «Диски» и «Часы» можно перемещать независимо друг от друга. Они автоматически примагничиваются к краям экрана и соседним карточкам.

Чтобы восстановить исходное расположение карточек, нажмите правой кнопкой мыши на карточку и выберите **«Сбросить позиции карточек»**.

## Сборка английской версии

Репозиторий поддерживает отдельные сборки для русского и английского языков. Английская версия запускается через `main_en.py`, который выбирает английский язык до загрузки интерфейса.

Чтобы собрать её локально в Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\build_en.ps1
```

Готовый исполняемый файл появится по пути:

```text
dist\Nook-English\Nook-English.exe
```

При отправке тега версии, например `v0.3.0`, GitHub Actions автоматически собирает обе языковые версии и прикрепляет к GitHub Release архивы:

- `Nook-Russian.zip`
- `Nook-English.zip`

## Лицензия

[MIT License](LICENSE) © Artem Gorokov