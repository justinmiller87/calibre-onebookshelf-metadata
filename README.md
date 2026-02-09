# OneBookShelf Calibre Plugins

This repository contains a collection of Calibre metadata source plugins for the OneBookShelf network of sites.

Each plugin is independent and specialized for its specific site, allowing you to fetch metadata (Title, Author, Publisher, Date) and covers for books, comics, and cards from these marketplaces.

## Supported Sites

| Site | Plugin Name | Identifier |
| :--- | :--- | :--- |
| **DMsGuild** | DMsGuild Metadata | `dmsguild` |
| **DriveThruRPG** | DriveThruRPG Metadata | `drivethrurpg` |
| **DriveThruComics** | DriveThruComics Metadata | `drivethrucomics` |
| **DriveThruFiction** | DriveThruFiction Metadata | `drivethrufiction` |
| **DriveThruCards** | DriveThruCards Metadata | `drivethrucards` |
| **Wargame Vault** | Wargame Vault Metadata | `wargamevault` |
| **Pathfinder Infinite** | Pathfinder Infinite Metadata | `pathfinderinfinite` |
| **Starfinder Infinite** | Starfinder Infinite Metadata | `starfinderinfinite` |
| **Storytellers Vault** | Storytellers Vault Metadata | `storytellersvault` |

## Installation

You can install any or all of these plugins individually:

1.  Download the **Zip file** for the specific plugin you want (e.g., `DMsGuild.zip`, `StarfinderInfinite.zip`).
2.  Open **Calibre**.
3.  Go to **Preferences** -> **Plugins**.
4.  Click **Load plugin from file**.
5.  Select the Zip file you downloaded.
6.  Restart Calibre.

## Configuration (Important: Cloudflare Cookies)

All these sites use Cloudflare protection, which blocks automated requests (like this plugin) unless a valid browser cookie is provided. You **MUST** provide a `cf_clearance` cookie for each plugin you use.

**Note:** Each site has its own cookie. You generally cannot mix cookies between sites (even Pathfinder/Starfinder usually prefer their own).

### How to get the Cookie

1.  Open **Firefox** (Chrome/Edge strings might not work due to TLS fingerprinting).
2.  Go to the specific site (e.g., `www.pathfinderinfinite.com`) and log in (or just visit).
3.  Open Developer Tools (**F12**).
4.  Go to the **Storage** tab.
5.  Expand **Cookies** and select the site URL.
6.  Find the row named `cf_clearance`.
7.  Copy the **Value** (a long string of random characters).

### Where to paste it

1.  In Calibre, go to **Preferences** -> **Plugins**.
2.  Search for the plugin (e.g., "Starfinder Infinite Metadata").
3.  Click **Customize plugin**.
4.  Paste the cookie string into the `cf_clearance` Cookie field.
5.  Click **OK**.

## Usage

### Automatic Search
When editing metadata for a book, click **Download Metadata**. The plugin will search automatically based on Title and Author.

### Id-Based Search
To force a specific match, add the site identifier to the **Ids** field in Calibre's metadata editor.

**Where to find the ID:**
Look at the product's URL in your browser. The ID is the number immediately following `/product/`.
*   Example URL: `https://www.dmsguild.com/product/174433/A-History-of-Waterdeep`
*   The ID is **174433**.

**Prefixes:**

| Site | Prefix | Example |
| :--- | :--- | :--- |
| **DMsGuild** | `dmsguild` | `dmsguild:174433` |
| **DriveThruRPG** | `drivethrurpg` | `drivethrurpg:12345` |
| **DriveThruComics** | `drivethrucomics` | `drivethrucomics:98765` |
| **DriveThruFiction** | `drivethrufiction` | `drivethrufiction:55555` |
| **DriveThruCards** | `drivethrucards` | `drivethrucards:11223` |
| **Wargame Vault** | `wargamevault` | `wargamevault:44444` |
| **Pathfinder Infinite** | `pathfinderinfinite` | `pathfinderinfinite:66666` |
| **Starfinder Infinite** | `starfinderinfinite` | `starfinderinfinite:77777` |
| **Storytellers Vault** | `storytellersvault` | `storytellersvault:88888` |

## Troubleshooting

-   **403 Forbidden Error:** Your cookie is invalid or expired. Get a new `cf_clearance` cookie from Firefox.
-   **No Results:** Try forcing the specific ID in the metadata ids field.

## License
GPL v3
