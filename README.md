# OneBookShelf Metadata for Calibre

A Calibre metadata source plugin for **DMsGuild** and **DriveThruRPG**.

This plugin retrieves comprehensive metadata (Title, Author, Publisher, Description, Rating, Publication Date) and high-quality cover images by leveraging the sites' internal APIs.

## Supported Sites
*   **DMsGuild**
*   **DriveThruRPG**

*(Other OneBookShelf sites like Storytellers Vault are planned but not yet verified.)*

## Requirements
Due to strict bot protection (Cloudflare) on these sites, this plugin requires a **User-Assisted Cookie Bypass**.

*   **Browser**: You **MUST** use **Firefox** to retrieve the cookie. (Cookies from Chrome/Edge will NOT work due to TLS fingerprinting mismatches).

## Installation
1.  Download the latest `calibre-dmsguild-metadata.zip`.
2.  Open Calibre.
3.  Go to **Preferences** -> **Plugins**.
4.  Click **Load plugin from file** and select the zip file.
5.  Restart Calibre.

## Configuration (CRITICAL STEP)
Before the plugin can work, you must provide a valid `cf_clearance` cookie for each site you wish to scrape.

### How to get the Cookie (Firefox Only)
1.  Open **Firefox** and go to [DMsGuild](https://www.dmsguild.com) or [DriveThruRPG](https://www.drivethrurpg.com).
2.  Make sure you are logged in (or at least passed the "Just a moment..." Cloudflare check).
3.  Press `F12` to open Developer Tools.
4.  Go to the **Storage** tab.
5.  Expand **Cookies** on the left and select the domain (e.g., `https://www.dmsguild.com`).
6.  Find the row named `cf_clearance`.
7.  Copy the long text string in the **Value** column.
8.  In Calibre, go to **Preferences** -> **Plugins** -> **Show only user installed plugins**.
9.  Select **OneBookShelf Metadata** and click **Customize plugin**.
10. Paste the value into the corresponding field ("DMsGuild cf_clearance Cookie" or "DriveThruRPG cf_clearance Cookie").
11. Click **OK**.

### Troubleshooting
*   **"No results found"**: Your cookie may have expired. Cloudflare cookies typically last a few hours to a few days. Repeat the steps above to get a fresh cookie.
*   **Error 500 / API Failures**: Ensure you are using a cookie from **Firefox**.
