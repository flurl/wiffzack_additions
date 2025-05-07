## Creating New Messages

Messages are discovered by the server based on a specific directory structure and file naming convention.

**Base Directory for Messages:**
All messages reside within `server/assets/messages/`.

**Message Structure:**
Each message requires its own dedicated sub-folder within the base directory.
- The **name of this sub-folder** becomes the unique `path` for the message (e.g., `server/assets/messages/my_alert/` means the path is `my_alert`).
- Inside this sub-folder, you place **one primary content file**.
- The **name of this content file** (excluding the extension) becomes the `name` of the message.
- The **file extension** determines the `type` of the message (`txt` or `html`).

---

### 1. Text-Only Messages

- **Directory:** Create a new folder under `server/assets/messages/`.
  Example: `server/assets/messages/important_notice/`
- **File:** Inside this new folder, create a `.txt` file. The filename (without `.txt`) will be the message name.
  Example: `server/assets/messages/important_notice/system_update.txt`
  - `path`: `important_notice`
  - `name`: `system_update`
  - `type`: `txt`
- **Content:** Write your plain text content directly into this `.txt` file.

---

### 2. HTML Messages

- **Directory:** Create a new folder under `server/assets/messages/`.
  Example: `server/assets/messages/new_feature/`
- **File:** Inside this new folder, create an `.html` file. The filename (without `.html`) will be the message name.
  Example: `server/assets/messages/new_feature/announcement.html`
  - `path`: `new_feature`
  - `name`: `announcement`
  - `type`: `html`
- **Content:** Write your HTML content directly into this `.html` file.
- **Associated Assets (Images, CSS, etc.):**
  - If your HTML message uses local images, CSS files, or other assets, place these files **inside the same message folder** (e.g., inside `server/assets/messages/new_feature/`). You may create a subfolder for these assets if needed.
  - You can then reference them using relative paths within your HTML (e.g., `<img src="promo_image.png">`). The server will serve these assets correctly.

---

After creating the necessary folder and file(s), the server should automatically pick up the new message.
