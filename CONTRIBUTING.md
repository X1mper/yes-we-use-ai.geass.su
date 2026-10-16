# Support the letter / Поддержать письмо

[Read the letter](https://yes-we-use-ai.geass.su/en/) · [Прочитать письмо](https://yes-we-use-ai.geass.su/)

## English

You don't have to use AI to support freedom of tool choice, responsible testing, and respectful criticism. Sign only if you agree with the letter, including the responsibility and testing commitments when they apply to your work.

### A one-file pull request

1. Fork this repository, or use GitHub's web editor for [`supporters.jsonc`](supporters.jsonc).
2. Add **one object** to the JSON array. Keep existing entries. GitHub's web editor will offer to create a fork if necessary.
3. Open a pull request and fill in the short checklist. You do **not** need to edit HTML, translate your name, run a build, or commit generated files. An optional avatar requires one image file in the same PR.

Person:

```json
{
  "type": "person",
  "name": "Example Person",
  "url": "https://example.org/people/example"
}
```

Organization:

```json
{
  "type": "organization",
  "name": "Example Organization",
  "url": "https://example.org",
  "description": "Independent software team"
}
```

The file uses JSONC (JSON with comments) and contains commented examples for a person and a team. Copy an example inside the array, remove its `//` prefixes, and replace the fictional details with yours. Leave the examples commented out. Insert a comma between real entries, but not after the last one. `type`, `name`, and `url` are required; `description` is optional. Use double quotes. `//` line comments and `/* … */` block comments are supported; trailing commas are not.

- `type`: exactly `person` or `organization`.
- `name`: public name or handle, up to 100 characters.
- `url`: your public HTTPS profile or organization's website, up to 300 characters, no credentials or nonstandard ports. No email/phone/address or tracking/referral links.
- `description`: optional short role or project, up to 140 characters; one text string shown as-is in both languages. English, Russian, or a concise bilingual description is fine.
- `avatar`: optional local image path, for example `/avatars/your-name.jpg`. Add that file to `avatars/` in your PR. PNG, JPEG (`.jpg`/`.jpeg`), WebP, or static SVG, at most 1 MiB; use a square image, ideally 256 × 256. Filenames may contain ASCII letters, numbers, hyphens, and underscores, with a lowercase extension. External image URLs, symlinks, and nested paths are not supported. SVG must be UTF-8 with the SVG namespace: basic shapes, paths, groups, gradients and clipping are supported. Scripts, event handlers, CSS/style attributes, animation, embedded images, links, DTD/entities, comments and editor metadata are rejected. Export a plain SVG with presentation attributes; unsupported content fails the build rather than being silently removed. Leave `avatar` out if you don't want an image. You may use an organization's logo if you have permission.

Names are sorted automatically within the People and Organizations lists. No HTML, scripts, slogans, or extra fields. No one else should edit or remove an existing signature without the signer's request and maintainer review.

### Browser preview

Each new push to your PR refreshes four Chromium screenshots (RU/EN, 1440 px and 375 px). The bot updates one comment with the artifact link and commit ID; screenshots expire after 14 days and downloading requires GitHub sign-in. GitHub may ask a maintainer to approve checks for a first-time fork contributor. A failed build is reported with a run link rather than stale screenshots. This does not deploy the PR.

### Consent and review

- Submit your own signature from your own account. A handle is fine; we do not ask for legal names or identity documents.
- Organizational signatures need an authorized representative. In the PR, link to public evidence of your affiliation (for example, your organization's team page or an organization-member profile). If authority is unclear, maintainers can request confirmation through an official public channel. Do not post private documents or secrets.
- Signing as a person does not sign on behalf of your employer. Organizational signatures are separate.
- No unsolicited signatures, impersonation, spam, harassment, or unrelated advertising.
- By submitting, you consent to public display of this entry and its retention in Git/PR history. For corrections or removal from the live list, open a PR or issue; removing an entry from the website does not erase public history or third-party caches.
- Maintainers review consent, affiliation where applicable, content, and run the local validation/build. A successful build is not identity verification. There is no automatic merge or deployment from an unmerged PR.
- After merge, GitHub Actions builds and publishes the site automatically. A badge can be used independently; it does not automatically add a signature and is not a quality certification.

## Русский

Чтобы поддержать свободу выбора инструментов и ответственную работу, не обязательно использовать ИИ. Подписываясь, вы соглашаетесь с принципами письма, включая ответственность и тщательное тестирование там, где это относится к вашей работе.

1. Откройте `supporters.jsonc` в редакторе GitHub. При необходимости GitHub предложит создать форк.
2. Внутри файла есть закомментированные примеры человека и команды. Скопируйте один из них внутрь массива, уберите у копии `//` и замените вымышленные данные своими: `type` (`person` или `organization`), `name`, `url` (публичная HTTPS-ссылка). Между реальными записями ставится запятая, после последней — нет. Исходные примеры оставьте комментариями. Поддерживаются комментарии `//` и `/* … */`; запятые перед закрывающей скобкой не поддерживаются.
3. Необязательное `description` — краткая роль или проект. Оно показывается одинаково в обеих версиях сайта; можно написать на русском, английском или коротко на обоих языках.
4. Необязательное `avatar` — путь к локальной картинке, например `/avatars/your-name.jpg`. Добавьте файл в папку `avatars/` тем же PR: PNG, JPEG (`.jpg`/`.jpeg`), WebP или статический SVG, до 1 МиБ. Лучше квадрат 256 × 256. В имени — латинские буквы, цифры, дефис и подчёркивание; расширение строчными буквами. Внешние URL, симлинки и вложенные папки не поддерживаются. SVG — UTF-8 с пространством имён SVG: поддерживаются базовые фигуры, контуры, группы, градиенты и обрезка. Скрипты, обработчики событий, CSS/style, анимация, встроенные картинки, ссылки, DTD/сущности, комментарии и метаданные редакторов запрещены. Экспортируйте простой SVG с атрибутами оформления; неподдерживаемое содержимое вызывает ошибку сборки, а не удаляется молча. Без картинки поле `avatar` просто не добавляйте. Для организации допустим логотип, который вы вправе использовать.
5. Создайте PR и заполните чеклист. HTML менять, сборку запускать и generated-файлы коммитить **не нужно**.

Ограничения: имя до 100 символов, HTTPS-ссылка до 300, описание до 140. Без HTML, лишних полей, реферальных ссылок и персональных контактов. Имена сортируются автоматически.

Подписывайтесь только за себя. За организацию — только с правом её представлять: добавьте в PR публичную ссылку, подтверждающую связь с организацией. При необходимости мы запросим подтверждение по официальному каналу; приватные документы не нужны. Личная подпись не означает поддержку работодателя.

Добавляя запись, вы соглашаетесь с её публичной публикацией, в том числе в истории Git и PR. Для исправления или удаления с сайта откройте PR/issue; публичная история и чужие кэши при этом не исчезают. Чужие подписи без согласия не добавляем и не меняем. Запрещены травля, подмена личности, спам и посторонняя реклама.

Каждый push в PR обновляет четыре скриншота Chromium (RU/EN, ширины 1440 и 375 px). Бот обновляет один комментарий ссылкой на артефакт и указывает коммит. Хранение — 14 дней; скачивание требует входа в GitHub. Первому PR из форка может понадобиться стандартное одобрение проверки сопровождающим. Ошибка сборки отмечается ссылкой на запуск, а не старыми скриншотами. До принятия PR сайт не меняется.

Каждую заявку проверяет человек. После принятия PR GitHub Actions проверяет данные и собирает сайт; успешная сборка публикуется автоматически. Шильдик не добавляет вас в список автоматически и не является гарантией качества.

## Development / Разработка

```sh
python3 tools/build.py
python3 -m http.server 8766 --bind 127.0.0.1 --directory build
node --check language.js
```

Python 3.10+, no third-party packages. Edit `templates/ru.html` and `templates/en.html` together. Output is in ignored `build/`. The publishing workflow runs only on `main` updates or a manual dispatch on `main`, not on pull requests. GitHub-hosted runners build the static release. There is no automatic merge.
