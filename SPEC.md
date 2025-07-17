# Worklog Desktop (PySide6) – Detailed Specification

## 1. Purpose
Provide a Linux desktop client that replicates, as closely as possible, every us
er‑facing behaviour of the existing React + Zustand web application contained in
 *personalLogger_frontend*.
The desktop client is aimed at developers and project managers who prefer a nati
ve workflow and want faster startup, global shortcuts, and system‑tray access.

---

## 2. Target Environment

| Item                   | Requirement                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| Operating System       | Modern Linux distros (Ubuntu 22.04 LTS+, Fedora 39+, Arch 2025.07)                             |
| Display Server         | X11 **and** Wayland                                                                        |
| Python                 | ≥ 3.12                                                                                     |
| Toolkit                | **Qt 6** via *PySide6* ≥ 6.0                                                               |
| Packaging              | Flatpak, AppImage, native `.deb` (built via PyInstaller + appstream‑metadata)                |
| Continuous Integration | GitHub Actions + branch protections                                                        |

---

## 3. High‑Level Architecture

```
main.py ──► QApplication
│
├── UI Layer (Qt Designer .ui files + custom widgets)
├── Models (QAbstractListModel subclasses for data, pydantic for validation)
├── Services
│   ├─ api_client.py          (HTTP → https://work-log.cc/api, token refresh)
│   ├─ auth/firebase.py       (Firebase Auth REST, Google OAuth PKCE flow)  <--
REQUIRES PROJECT CONFIG
│   ├─ sync_engine.py         (queue, delta sync, retry)
│   └─ export.py              (xlsx / csv via pandas + xlsxwriter)
└── Persistence
    └─ SQLite cache (SQLAlchemy + Alembic migrations)
```

The application will use **asyncio** for non-blocking HTTP calls in services.

---

## 4. Data Model (parity with web API)

| Entity     | Fields (desktop)                                                              | Notes                                          |
| ---------- | ----------------------------------------------------------------------------- | ---------------------------------------------- |
| **User**   | id, name, email, avatar_url, locale, token, refresh_token                     | Stored in `~/.config/worklog/credentials.json` |
| **Space**  | id, name, color, is_personal, created_at, updated_at                          | `*my_space` constant respected                 |
| **Member** | id, space_id → Space, display_name, role, joined_at                           | Roles: owner \| editor \| viewer               |
| **Tag**    | id, space_id, name, color, created_at                                         |                                                |
| **Log**    | id, space_id, content (Markdown), record_time (tz‑aware), tag_ids [], created_at, updated_at | Schema versioned via Alembic                   |

---

## 5. Functional Requirements

### 5.1 Authentication

> **Implementation note (2025‑07‑17)**
> The desktop client expects two configuration files in `~/.config/worklog/`:
> `firebase_config.json` and `google_oauth_client.json`. Environment variables
> with the prefix `WORKLOG_` may override individual fields. These values are
> required so every Firebase Auth request appends `?key=<API_KEY>` and OAuth can
> identify the correct client ID.

| Area                        | Desktop Requirement                                                                                                                                                                                                                                                                                                                                                       | Notes                                                                                                                                  |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Sign‑in method**          | Google account only (Firebase Auth “Sign in with Google” OAuth PKCE flow)                                                                                                                                                                                                                                                                                                 | The web app does **not** yet implement e‑mail / password.                                                                              |
| **Firebase project config** | A *public* JSON (`firebase_config.json`) **must be present** in `~/.config/worklog/` **or** via env vars:<br>`WORKLOG_FB_API_KEY`, `WORKLOG_FB_CLIENT_ID`, `WORKLOG_FB_PROJECT_ID`, …                                                                                                                                                                                    | Same fields as the `firebaseConfig` object in the React code. Checked at startup; app aborts with an error dialog if missing.        |
| **Google OAuth client**     | `google_oauth_client.json` in the same directory or env var `WORKLOG_GOOGLE_CLIENT_ID`                                                                                                                                                                                                                                                                                      | Use the "installed" credentials from Google Cloud; only `client_id` and `redirect_uris` are required.                                  |
| **Login flow**              | 1. `LoginWindow` launches the system browser (`QDesktopServices.openUrl`) to Google OAuth with PKCE.<br>2. Redirect URI `worklog://auth` (or `http://localhost:<port>`) returns `authorization_code`.<br>3. Desktop exchanges the code via `identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key=<API_KEY>` → receives **`id_token`** + **`refresh_token`**.<br>4. Call `POST /users/` to (create \| update) user profile.<br>5. Cache credentials in a secure manner (e.g., using the Secret Service API via a library like `secretstorage`). | Mirrors `signInWithPopup()` → `useAuthState()` logic in the web client.                                                                |
| **Token refresh**           | • Every 55 min (or immediately after resume) call `securetoken.googleapis.com/v1/token?key=<API_KEY>` with `grant_type=refresh_token`.<br>• On any non‑200 response, purge credentials and reopen `LoginWindow`.                                                                                                                                                              | Matches React’s silent‑refresh loop (`getIdToken(user, true)`).                                                                         |
| **API authorisation**       | All HTTP requests include `Authorization: Bearer <id_token>` header.                                                                                                                                                                                                                                                                                                     |                                                                                                                                        |
| **Sign‑out**                | Avatar ➜ “Logout”: clear credentials, flush models, show `LoginWindow`.                                                                                                                                                                                                                                                                                                   |                                                                                                                                        |
| **Multi‑account**           | Not yet supported on either platform.                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                        |
| **Offline handling**        | If token is ≥ 50 min old **and** no network, operate read‑only; queue mutations for later sync.                                                                                                                                                                                                                                                                             |                                                                                                                                        |
| **Security**                | • Tokens never written unencrypted.<br>• Validate Firebase *project ID* (`worklog‑b6b69`) before use.                                                                                                                                                                                                                                                                      |                                                                                                                                        |

---

### 5.2 Spaces
* List spaces in a side bar.
* Create, rename, delete spaces (owner only).
* Invite members (generate magic‑link using `/spaces/{id}/invitation` endpoint).

### 5.3 Logs
* Display logs grouped by **date header**.
* Endless scrolling: fetch next page when the scrollbar approaches the end.
* **Search** (`Ctrl+F`) debounced 300 ms; updates list via model filtering.
* **Tag include / exclude** filters.
* **Create/Edit** dialog:
  * Markdown text area.
  * Date/time picker.
  * Tag multi‑select popover.
  * Shortcut: `Ctrl+Enter` to save, `Esc` to cancel.
* **Optimistic UI** – model adds placeholder immediately; sync engine retries on
 5xx with exponential back‑off.

### 5.4 Tags
* Tag list & colour picker.
* CRUD operations & bulk delete.
* Autocomplete while editing log.

### 5.5 Members
* Member table.
* Role dropdown and remove button.
* Only owners can promote/demote.

### 5.6 Export
* `File ▸ Export…` menu opens location chooser; export current space’s logs
  * CSV, XLSX (default), JSON.
* Respect active filters.
* Use `pandas.DataFrame.to_excel()`; show notification when done.

### 5.7 Settings
* Remember last selected space (`QSettings`).
* Theme: follow system / light / dark.
* Startup behaviour: autostart toggle.

### 5.8 System Tray
* Quick‑add log window (`Ctrl+Alt+L`), preview last 5 logs.

---

## 6. Non‑Functional Requirements

| Category       | Spec                                                              |
| -------------- | ----------------------------------------------------------------- |
| Performance    | Cold start ≤ 1 s on SSD + 8 GB RAM                                  |
| Responsiveness | < 100 ms UI feedback for local actions                              |
| Accessibility  | Standard Qt accessibility features; keyboard navigable            |
| Localization   | English & zh‑TW strings using Qt's translation tools (`.ts` files). |
| Offline        | All reads from SQLite; sync engine runs every 30 s or when online |
| Security       | Store tokens securely; HTTPS pinning                              |

---

## 7. User Interface Blueprint

1. **LoginWindow**

   ```
   +---------------------------------------+
   |  Worklog • Sign in                   X|
   |---------------------------------------|
   |  [ Google ]                           |
   +---------------------------------------+
   ```
2. **MainWindow (QMainWindow)**

   ```
   Title Bar:  Worklog    [▼ default]       ← Month July 2025 →      🔍  [⋮]

   (Details of the main window layout will be defined in .ui files and mockups)
   ```

   Full mock‑ups will be created in `docs/mockups/*.png`.

---

## 8. Application Lifecycle

| Phase                  | Action                                                     |
| ---------------------- | ---------------------------------------------------------- |
| `QApplication` start   | initialise logging, create directories, load `QSettings`   |
| Main window creation   | if token valid → `MainWindow`; else `LoginWindow`         |
| `QApplication` exit    | flush sync queue, close DB connection                      |

---

## 9. Build & Packaging Steps
1. `poetry install`; `poetry build` produces wheel.
2. `pyinstaller --noconfirm worklog.spec`
3. `fpm` or other tools to create `.deb` and `.rpm` packages.
4. GitHub Actions workflow `build.yml` runs matrix for x86_64 & aarch64, runs `pytest`, and pushes artifacts.

---

## 10. Mapping from Web Codebase → Desktop Modules

| Web (React)                   | Desktop (PySide6)             | Notes                                       |
| ----------------------------- | ----------------------------- | ------------------------------------------- |
| `store-user.js`               | `models/user_model.py`        | `QObject` with signals for property changes |
| `store-space.js`              | `models/space_model.py`       | `QAbstractListModel` for spaces list        |
| `store-logs.js`               | `models/log_model.py`         | `QAbstractListModel` for logs list          |
| `CreateLogDialog.jsx`         | `ui/dialogs/log_editor.py`    |                                             |
| `TagListDialog.jsx`           | `ui/dialogs/tag_list.py`      |                                             |
| `SpaceMemberEditorDialog.jsx` | `ui/dialogs/member_editor.py` |                                             |

---

## 11. Open Questions
1. **Notifications** – should desktop push notifications mirror web or rely on polling?
2. **Real‑time collaboration** – web emits WebSocket events; not yet implemented in PySide6 version.
3. **Bi‑directional sync conflicts** – Last‑write‑wins? or three‑way merge?
4. **Credential storage fallback** – if a secure storage mechanism is not available, should we require the user to set a master password for local encryption?

---

## 12. Milestones

| Sprint    | Deliverable                                                         |
| --------- | ------------------------------------------------------------------- |
| 1 (2 wks) | Skeleton PySide6 app **+ working Google login with PKCE & config JSON** |
| 2         | Space & Tag models + list UI                                        |
| 3         | Log list with offline cache                                         |
| 4         | Create/Edit dialog, sync engine                                     |
| 5         | Export & Settings                                                   |
| 6         | Packaging, QA, translations                                         |

---

### Appendix A – Backend Endpoints Discovered
* `GET /spaces/`
* `POST /spaces/`
* `GET /worklogs?...`
* `POST /worklogs/`
* `PUT /worklogs/{id}`
* `DELETE /worklogs/{id}`
* `GET /tags/`
* `POST /tags/`
…etc.

All endpoints require `Authorization: Bearer <id_token>` header.

---

© 2025 Worklog Desktop Team
