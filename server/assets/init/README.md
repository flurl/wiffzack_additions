# Initial Stock Configuration 🚀

This directory is where you'll define the starting inventory levels for your various clients or storage locations.

## How It Works

To set up the initial stock for a client/storage:

1.  **Create a CSV File:** For each client or storage location, create a new CSV (Comma Separated Values) file in this directory.
2.  **Naming Convention:** The name of the CSV file is important! It should correspond to the client or storage name as recognized by the system (e.g., if your storage is named "MainWarehouse", the file should be `MainWarehouse.csv`).
3.  **File Format:** Each CSV file must adhere to the following simple format, using a semicolon (`;`) as the delimiter:

    ```csv
    article_id;amount
    ```

    *   `article_id`: The unique identifier for the article.
    *   `amount`: The initial quantity of that article in stock.

**Example CSV Content:**

```csv
article_id;amount
4661;10
4662;10
4666;10
1020;25
3055;5
```