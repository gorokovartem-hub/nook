# EU

A minimalist Windows utility: a taskbar widget and a small tray window.
Python + customtkinter. The theme (dark/light) is picked up from Windows settings.

<!-- Add a screenshot here: ![screenshot](docs/screenshot.png) -->

[![release](https://img.shields.io/github/v/release/gorokovartem-hub/nook)](https://github.com/gorokovartem-hub/nook/releases/latest)

## Download

**[nook-v0.2.0-win64.zip](https://github.com/gorokovartem-hub/nook/releases/download/v0.2.0/nook-v0.2.0-win64.zip)** — a ready-to-use Windows build, no Python required.
Unpack the archive and run `nook.exe`. All versions: [Releases](https://github.com/gorokovartem-hub/nook/releases).

> Windows SmartScreen or your antivirus may warn you about an unsigned application
> (the program uses global hotkeys). The source code is open.

## Features

- **Nook Studio** — manage widget visibility, taskbar mode, and desktop cards.
- **Appearance customization** — 10 ready-made themes, color selection, widget transparency, and corner rounding.
- **Layout profiles** — save and apply visibility, mode, and individual positions of each card.
- **System monitoring** — CPU, RAM, and GPU load, disk activity, inbound and outbound network traffic, battery status.
- **Disk monitoring** — track drive usage and storage activity.
- **Clock and calendar** — current time, date, and calendar data in one place.
- **Music player** — quick access to music and playback controls.
- **Internet monitor** — connection status, traffic, and network metrics.
- **Quick launcher** — launch apps and shortcuts without extra steps.
- **Clipboard history** — store and restore recently copied data.
- **Notes and tasks** — quick notes, to-do lists, and reminders.
- **Hotkeys** — quick actions and control without the mouse.
- **Theme import and export** — transfer appearance between configurations.
- **Windows autostart** — launch Nook when the system starts.
- **Magnetic snapping** — precisely keep widgets near screen edges and boundaries.
- **Taskbar widget** — CPU and RAM with mini-graphs; in full mode, also GPU, disk, and network.
  Two modes (full / compact), dragging with edge snapping, a tooltip with details,
  auto-hide in fullscreen applications.
- **System** — component load, drive activity, and network speeds.
- **Focus** — Pomodoro 25 / 5 with a long break after four cycles and a sprint indicator.
- **Notes** — entries are displayed as separate cards; the quick window shows recent notes and opens from the tray or via `Ctrl+Alt+N`. All entries are saved to `notes.txt`.
- **Clipboard** — copy history; clicking returns an entry to the clipboard.
- **Area screenshot** with copying to the clipboard.

## Hotkeys

| Keys           | Action                           |
|----------------|----------------------------------|
| `Ctrl+Alt+C`   | Compact widget mode              |
| `Ctrl+Alt+F`   | Full widget mode                 |
| `Ctrl+Alt+W`   | Show / hide widget               |
| `Ctrl+Alt+N`   | Quick note                       |
| `Ctrl+Alt+S`   | Area screenshot                  |

In the main window: `Ctrl+1…5` — switch tabs, `Esc` — minimize to tray.

## Running from source

```powershell
git clone https://github.com/gorokovartem-hub/nook.git
cd nook
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Requires Windows 10/11 and Python 3.10+.

## Settings

Widget position and mode are stored in `config.json` next to the program (created automatically).
In Nook Studio, you can choose the system, dark, or light theme, customize colors,
widget transparency, and corner radius.
The desktop cards "System", "Disks", and "Clock" can be dragged independently
and automatically snap to screen edges and to each other.
To restore their layout, right-click a card and select
"Reset card positions". Card visibility is configured in Nook Studio.



## English build / Сборка на английском

The repository can produce separate Russian and English Windows builds. The English build starts through `main_en.py`, which selects English before loading the UI.

To build it locally on Windows, install the requirements and PyInstaller, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\build_en.ps1
```

The executable will be at `dist\Nook-English\Nook-English.exe`. Pushing a version tag such as `v0.2.1` also triggers the GitHub Actions workflow, which builds and attaches both `Nook-Russian-win64.zip` and `Nook-English-win64.zip` to the GitHub Release.

## License

<!-- Choose a license, e.g. MIT, and add a LICENSE file -->

---
# RU

Минималистичная утилита для Windows: виджет на панели задач и небольшое окно в трее.
Python + customtkinter. Тема (тёмная/светлая) подхватывается из настроек Windows.

<!-- Добавьте сюда скриншот: ![screenshot](docs/screenshot.png) -->

[![release](https://img.shields.io/github/v/release/gorokovartem-hub/nook)](https://github.com/gorokovartem-hub/nook/releases/latest)

## Скачать

**[nook-v0.2.0-win64.zip](https://github.com/gorokovartem-hub/nook/releases/download/v0.2.0/nook-v0.2.0-win64.zip)** — готовая сборка для Windows, Python не нужен.
Распакуйте архив и запустите `nook.exe`. Все версии: [Releases](https://github.com/gorokovartem-hub/nook/releases).

> Windows SmartScreen или антивирус могут предупредить о неподписанном приложении
> (программа использует глобальные горячие клавиши). Исходный код открыт.

## Возможности

- **Nook Studio** — управление видимостью виджетов, режимом панели задач и карточками рабочего стола.
- **Настройка оформления** — 10 готовых тем, выбор цветов, прозрачность виджетов и скругление углов.
- **Профили раскладки** — сохранение и применение видимости, режима и отдельных позиций каждой карточки.
- **Мониторинг системы** — загрузка CPU, RAM и GPU, активность диска, входящий и исходящий сетевой трафик, состояние батареи.
- **Мониторинг дисков** — отслеживание заполнения накопителей и активности хранилища.
- **Часы и календарь** — текущее время, дата и календарные данные в одном месте.
- **Музыкальный плеер** — быстрый доступ к музыке и контролам воспроизведения.
- **Интернет-монитор** — статус соединения, трафик и сетевые показатели.
- **Быстрый лаунчер** — запуск приложений и ярлыков без лишних действий.
- **История буфера обмена** — хранение и возврат последних скопированных данных.
- **Заметки и задачи** — быстрые записи, списки дел и напоминания.
- **Горячие клавиши** — быстрые действия и управление без мыши.
- **Импорт и экспорт тем** — перенос оформления между конфигурациями.
- **Автозапуск Windows** — запуск Nook при старте системы.
- **Магнитная привязка** — точное удержание виджетов возле краёв и границ экрана.
- **Виджет на панели задач** — CPU и RAM с мини-графиками, в полном режиме ещё GPU, диск и сеть.
  Два режима (полный / компактный), перетаскивание с прилипанием к краям, тултип с подробностями,
  автоскрытие в полноэкранных приложениях.
- **Система** — загрузка компонентов, активность накопителя и сетевые скорости.
- **Фокус** — помодоро 25 / 5 с длинным отдыхом после четырёх циклов и индикатором спринтов.
- **Заметки** — записи отображаются отдельными карточками; быстрое окно показывает последние заметки и открывается из трея или по `Ctrl+Alt+N`. Все записи сохраняются в `notes.txt`.
- **Буфер обмена** — история копирований, клик возвращает запись в буфер.
- **Скриншот области** с копированием в буфер.

## Горячие клавиши

| Клавиши        | Действие                         |
|----------------|----------------------------------|
| `Ctrl+Alt+C`   | Компактный режим виджета         |
| `Ctrl+Alt+F`   | Полный режим виджета             |
| `Ctrl+Alt+W`   | Показать / скрыть виджет         |
| `Ctrl+Alt+N`   | Быстрая заметка                  |
| `Ctrl+Alt+S`   | Скриншот области                 |

В главном окне: `Ctrl+1…5` — переключение вкладок, `Esc` — свернуть в трей.

## Запуск из исходников

```powershell
git clone https://github.com/gorokovartem-hub/nook.git
cd nook
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Требуется Windows 10/11 и Python 3.10+.

## Настройки

Позиция и режим виджетов хранятся в `config.json` рядом с программой (создаётся автоматически).
В Nook Studio можно выбрать системную, тёмную или светлую тему, настроить цвета,
прозрачность виджетов и радиус скругления углов.
Карточки «Система», «Диски» и «Часы» рабочего стола перетаскиваются независимо
и автоматически примагничиваются к краям экрана и друг к другу.
Чтобы восстановить их расположение, нажмите правой кнопкой мыши на карточку и выберите
«Сбросить позиции карточек». Видимость карточек настраивается в Nook Studio.

## Лицензия

<!-- Выберите лицензию, например MIT, и добавьте файл LICENSE -->