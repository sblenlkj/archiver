# Запуск без uv

Проект **не требует uv, pip-пакетов или интернета для выполнения архивации**. Нужен Python **3.12+** (см. `pyproject.toml`). Используется только стандартная библиотека.

## Вариант A — прямо из исходников, без установки (рекомендуется)

Открой терминал в корне `archive_over_vk` и проверь:

```bash
python3 --version
```

На macOS / Linux:

```bash
python3 src/archiver/encoder.py demo 
python3 src/archiver/decoder.py decoded/encoded.txt --extract decoded/restored
```

На Windows:

```powershell
py -3 src\archiver\encoder.py demo 
py -3 src\archiver\decoder.py decoded/encoded.txt --extract decoded/restored
```

Таким образом **совсем не требуется установка Python-пакета**, в том числе `uv_build`. Оба файла имеют самостоятельную функцию `main()`. Для экспериментальной локальной машины это самый простой путь.

## Вариант B — через стандартный venv, также без uv

`venv` создаёт изолированное окружение, но само по себе не устанавливает проект. Поскольку зависимости отсутствуют, можно просто запускать исходные Python-скрипты выбранным интерпретатором.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python src/archiver/encoder.py demo 
python src/archiver/decoder.py decoded/encoded.txt --extract decoded/restored
deactivate
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python src\archiver\encoder.py demo 
python src\archiver\decoder.py decoded/encoded.txt --extract decoded/restored
deactivate
```

Если политика PowerShell не позволяет активировать окружение, запускай `.venv\Scripts\python.exe` напрямую вместо активации.

## Вариант C — вызов модулей через `python -m`

При `src`-layout Python должен видеть папку `src`:

macOS / Linux:

```bash
PYTHONPATH=src python3 -m archiver.encoder demo 
PYTHONPATH=src python3 -m archiver.decoder decoded/encoded.txt --extract decoded/restored
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
py -3 -m archiver.encoder demo 
py -3 -m archiver.decoder decoded/encoded.txt --extract decoded/restored
Remove-Item Env:PYTHONPATH
```

## А что с командами `archive-encode` / `archive-decode`?

Они объявлены в `[project.scripts]` файла `pyproject.toml`, но становятся доступными только **после установки проекта**. Для установки через `pip install -e .` требуется сборочный backend `uv_build`, указанный в `pyproject.toml`; при обычной настройке pip загрузит его как build dependency. Это не требует установки CLI `uv`, но может потребовать доступ в интернет/заранее подготовленный wheel. Поэтому для полностью автономного запуска лучше варианты A–C.

Все артефакты по умолчанию сохраняются в `decoded/`; этот каталог целиком внесён в `.gitignore`.

## Проверка результатов

- `decoded/encoded.txt` — одна непрерывная Base64-строка из ZIP (без собственных сегментов).
- `decoded/restored.zip` — восстановленный архив.
- `decoded/restored/` — распакованный пример `demo/`.
- Кодер выводит SHA-256 ZIP. Чтобы проверить результат из браузера, передай этот хеш декодеру через `--sha256 <значение>`.
- В эксперименте проверяй однократную передачу Base64. Если один архив был вставлен несколько раз подряд, получившийся TXT не является корректным входом для текущего декодера.

Скрипт браузерного сбора расположен в `src/archiver/collect_archive.js`; запускается отдельно в DevTools и не зависит от Python.
