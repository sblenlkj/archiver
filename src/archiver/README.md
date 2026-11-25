# Archiver components

- `encoder.py` — папка → ZIP → Base64; по умолчанию `decoded/encoded.txt`, с `--splits [DIR]` — нумерованные части в `decoded/splits/` плюс `manifest.json`. `--block-limit` задаёт длину части (по умолчанию 500000).
- `decoder.py` — один Base64 TXT или `--splits [DIR]` → ZIP → папка; проверяет хеши и архив.
- `collect_archive.js` — DevTools: последняя группа сообщений, после отдельного `###`, собрать Base64 и скачать TXT.
- `collect_markdown.js` — DevTools: после отдельного `###` собрать Markdown и скопировать в буфер.

Оба JS-скрипта работают только с уже загруженными DOM-сообщениями. Локальные split-файлы и `manifest.json` не интегрированы с JS-сборщиками. Детали и команды — в корневом README.

Все локальные выходные файлы по умолчанию находятся в корневой папке `decoded/`, которая игнорируется Git.
