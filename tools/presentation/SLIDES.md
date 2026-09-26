# Презентация RU / EN в работающем демо

26 сентября 2026 опубликованы предоставленные пользователем HTML-презентации.
Исходник: `C:/Users/madoev/.gemini/antigravity-ide/scratch/presentation`.
Обе HTML-страницы, оба Markdown-доклада и 18 PNG скопированы без изменения байтов
в `tools/presentation/slides/` и `D:/delta-presentation/slides/`.
SHA256 и размеры исходных 22 файлов сохранены в `slides-manifest.json`.
Содержание слайдов не является новой формальной аттестацией или Feature010 GO.

Запуск или получение актуальных внешних ссылок:

```powershell
pwsh -NoProfile -File D:/delta-presentation/START-SLIDES.ps1 start
pwsh -NoProfile -File D:/delta-presentation/START-SLIDES.ps1 status
```

Локально: `http://127.0.0.1:8873/?lang=ru` и `http://127.0.0.1:8873/?lang=en`.
Снаружи используется отдельный аутентифицированный HTTPS Quick Tunnel;
код входа тот же, что у основного демо. Текущий origin записан в
`D:/delta-data/presentation-20260924/slides-tunnel/current-url.txt`
и `D:/delta-presentation/SLIDES-URL.txt`. Добавьте `/?lang=ru` или `/?lang=en`.
После остановки/перезагрузки новый запуск может выдать другой hostname.

`slides-start.ps1` обновляет два пункта меню главного демо через отдельный
JS-ресурс в игнорируемом `dist-live/assets` установленного Admin UI.
Если демо уже открыто, обновите страницу. Controller, Worker, Presentation
и node-training не перезапускаются. Порты 8873/8874 принадлежат только слайдам;
`stop` останавливает только этот процесс и его туннель.

`slides_host.py` читает рабочую копию из `D:/delta-presentation/slides`.
Для HTTP-ответа он адаптирует только пути переключателя языка, изображений
и lightbox к разрешённым маршрутам существующего `tunnel_gateway.py`.
Сервис читает страницы/PNG и не запускает вычисления. Google Fonts, указанные
автором, сохранены; CSS содержит резервные системные шрифты.

При восстановлении скопируйте содержимое версионированного `slides/` в
`D:/delta-presentation/slides`, сверьте manifest, запустите `slides-start.ps1`.
Основной туннель по-прежнему управляется отдельным `START-REMOTE.ps1`.

Задачи: T051, HR010-001; область — демонстрационные статические материалы.
