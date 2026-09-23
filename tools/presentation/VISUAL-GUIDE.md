# Visual guide / Визуальное объяснение

T051 / HR010-001. Formal impact: NONE. Pre-implementation Constitution Check:
UI-only conceptual illustrations and bounded static PNG delivery; no protocol,
arithmetic, voting, durability, native or qualification behavior is changed.
The accepted baseline report remains the authority; this viewer adds none.

Open **How it works** in Admin UI or Presentation. Both links open the same
`/admin/?lang=en#/guide` page. Use `lang=ru` for Russian captions and controls.
Buttons, Left/Right, Home/End and numbered slide selectors navigate seven images.
Full screen enlarges the illustration; Escape exits through the browser.
The selected slide is stored in the URL (`&slide=5`) for refresh and sharing.
The original image can be opened separately for browser zoom.

В Admin UI и Presentation выберите **Как это работает**. Это одна страница
`/admin/?lang=ru#/guide`. Листайте кнопками «Назад»/«Далее», стрелками, Home/End
или номерами слайдов. «На весь экран» включает режим показа; Escape выходит.
Номер слайда сохраняется в URL (`&slide=5`). Ссылку можно обновлять и пересылать.
Исходное изображение открывается отдельно для увеличения средствами браузера.

Seven user-supplied illustrations are embedded unchanged, in pages 1–7 order.
Their internal text is English and includes original page labels “of 9”; only
seven files were supplied. No missing pages are invented. Captions, controls,
alt text and notes are bilingual. `guide/images/sources.json` records original
names and SHA-256; it is provenance, not protocol evidence.

Предоставлены семь изображений: встроенный в них текст остаётся английским,
а подписи, управление и пояснения переведены. На исходниках указано «из 9»,
но файлов только семь. Изображения сохранены без изменений и без дорисовки.

Slide 5 contains incorrect arithmetic in the original. Visible bilingual notes
give the correct weighted means (65/3, 12.5, 38/3), including in full screen.
Other notes distinguish the conceptual drawings from authoritative context,
certificate chains, domain assignment and fixed-point/rational arithmetic.
No picture is a trace or evidence of a qualifying execution.

На пятом слайде в исходнике есть арифметические ошибки. Правильные значения
(65/3, 12,5, 38/3) показаны под ним, в том числе в полноэкранном режиме.
Пояснения отделяют общую идею от точного протокола; квалификацию они не меняют.

Deployment: build/install Admin using `install-admin-ui.ps1`, then reload the
presentation server and remote gateway for the PNG allowlist. Preserve the
Controller instance and saved workspace. A gateway restart allocates a new
Quick Tunnel URL: `START-REMOTE.ps1 status` prints the verified current address.
The persistent access code remains valid; browser sessions need a new login.
