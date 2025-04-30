*   `GET /api/<string:client>/sales`
    *   Retrieves the total sales figures aggregated for a specific client (waiter).
*   `GET /api/<string:client>/tallied_articles`
    *   Retrieves a list of articles tallied (booked) by a specific client.
*   `GET /api/<string:client>/latest_tallied_articles`
    *   Retrieves the most recently tallied articles for a specific client.
*   `GET /api/wardrobe_sales`
    *   Retrieves sales data specifically related to the wardrobe.
*   `GET /api/artikel`
    *   Retrieves a list of all available articles (ID, name, price).
*   `GET /api/storage_article_groups`
    *   Retrieves all article groups associated with storage.
*   `GET /api/storage_article_groups/<int:storage_id>`
    *   Retrieves the article groups present within a specific storage location.
*   `GET /api/storage_article_by_group/<int:group>`
    *   Retrieves articles belonging to a specific article group within storage.
*   `POST /api/update_storage/to/<int:to_storage_id>`
    *   Adds articles to the specified storage. Accepts a JSON payload detailing articles and amounts. Can operate in relative (default) or absolute mode via the `method` query parameter.
*   `POST /api/update_storage/from/<int:from_storage_id>`
    *   Withdraws articles from the specified storage. Accepts a JSON payload detailing articles and amounts. Can operate in relative (default) or absolute mode via the `method` query parameter.
*   `POST /api/update_storage/from/<int:from_storage_id>/to/<int:to_storage_id>`
    *   Moves articles between the specified 'from' and 'to' storages. Accepts a JSON payload detailing articles and amounts. Can operate in relative (default) or absolute mode via the `method` query parameter.
*   `GET /api/get_articles_in_storage/<int:storage_id>`
    *   Retrieves a list of articles and their amounts currently in the specified storage.
*   `GET /api/get_articles_in_storage/<int:storage_id>/article_group/<int:article_group_id>`
    *   Retrieves a list of articles and their amounts currently in the specified storage, filtered by a specific article group.
*   `GET /api/get_storage_name/<int:storage_id>`
    *   Retrieves the name of the specified storage location.
*   `GET /api/get_config/<string:terminal_id>`
    *   Retrieves configuration settings specific to the given terminal ID from the `config.toml` file.
*   `GET /api/set_init_inventory/storage/<int:storage_id>`
    *   Sets the inventory count for articles in the specified storage based on data read from a corresponding CSV file (e.g., `StorageName.csv`). This effectively initializes or resets the stock count.
*   `GET /api/invoice/list`
    *   Retrieves a list of all invoices.
*   `GET /api/invoice/list/<string:waiter>`
    *   Retrieves a list of invoices filtered by a specific waiter.
*   `GET /api/invoice/print/<int:invoice_id>`
    *   Sends a request to the background print service to print the specified invoice ID (ESC/POS format).
*   `GET /api/invoice/html/<int:invoice_id>`
    *   Retrieves the HTML representation of the specified invoice from the background print service.
*   `GET /api/message/list`
    *   Retrieves a list of available messages (metadata like path, name, type) from the configured message directory.
*   `GET /api/message/<string:message_path>`
    *   Retrieves the full details (including content for 'txt' type) of a specific message identified by its path segment.
*   `GET /message/html/<string:message_path>/`
    *   Serves the primary HTML file (e.g., `message_name.html`) for an HTML-type message. Used for rendering in an iframe.
*   `GET /message/html/<string:message_path>/<string:file>`
    *   Serves auxiliary files (like CSS, JS, images) associated with an HTML-type message, allowing the main HTML file to reference them correctly.
