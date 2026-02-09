#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2025, Justin Miller'
__docformat__ = 'restructuredtext en'

import time
import re
import subprocess
from urllib.parse import quote
from queue import Empty, Queue

try:
    from PyQt5.Qt import QUrl, QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit
except ImportError:
    from PyQt4.Qt import QUrl, QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit

from calibre.ebooks.metadata.sources.base import Source, Option
from calibre.ebooks.metadata import check_isbn
from calibre.utils.icu import lower
from calibre.utils.cleantext import clean_ascii_chars

class ConfigWidget(QWidget):
    def __init__(self, plugin):
        QWidget.__init__(self)
        self.plugin = plugin
        layout = QVBoxLayout(self)
        
        # Cookie Input
        self.cookie_label = QLabel('DriveThruFiction "cf_clearance" Cookie:', self)
        layout.addWidget(self.cookie_label)
        
        self.cookie_input = QLineEdit(self)
        self.cookie_input.setText(plugin.prefs.get('cf_cookie_dtf', ''))
        self.cookie_input.setPlaceholderText('Paste DriveThruFiction cookie here')
        layout.addWidget(self.cookie_input)

        layout.addStretch(1)

    def save_settings(self):
        self.plugin.prefs['cf_cookie_dtf'] = self.cookie_input.text().strip()

class DriveThruFictionSource(Source):
    name = 'DriveThruFiction Metadata'
    description = 'Downloads metadata and covers from DriveThruFiction.'
    author = 'Justin Miller'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    # Capabilities
    capabilities = frozenset(['identify', 'cover'])
    touched_fields = frozenset(['title', 'authors', 'tags', 'pubdate', 'comments', 'publisher', 'identifier:drivethrufiction', 'series', 'rating'])
    
    # Explicitly enable customization
    def is_customizable(self):
        return True

    def config_widget(self):
        return ConfigWidget(self)

    def save_settings(self, config_widget):
        config_widget.save_settings()

    def get_base_url(self):
        return 'https://www.drivethrufiction.com'

    def _fetch_url(self, url, timeout=30):
        # Try standard browser first
        br = self.browser
        br.set_handle_robots(False)
        br.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Referer', 'https://www.google.com/')
        ]
        
        # Select cookie
        cookie = self.prefs.get('cf_cookie_dtf')
            
        if cookie:
             br.addheaders.append(('Cookie', f'cf_clearance={cookie}'))

        try:
            return br.open_novisit(url, timeout=timeout).read()
        except Exception as e:
            # Check for 403 or other blocking
            msg = str(e)
            if '403' in msg or 'Forbidden' in msg:
                 return self._fetch_via_curl(url, timeout)
            raise e

    def _fetch_via_curl(self, url, timeout):
        # Fallback to system curl with high-fidelity headers to mimic Chrome
        cmd = [
            'curl', '-L', 
            '-A', 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
            '-H', 'accept: application/json, text/plain, */*',
            '-H', 'accept-language: en-US,en;q=0.9',
            '-H', 'cache-control: max-age=0',
            '-H', 'sec-ch-ua: "Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            '-H', 'sec-ch-ua-mobile: ?0',
            '-H', 'sec-ch-ua-platform: "Windows"',
            '-H', 'sec-fetch-dest: document',
            '-H', 'sec-fetch-mode: navigate',
            '-H', 'sec-fetch-site: none',
            '-H', 'sec-fetch-user: ?1',
            '-H', 'upgrade-insecure-requests: 1',
            '--compressed',
            '--max-time', str(timeout)
        ]
        
        # Select cookie based on URL
        cookie = self.prefs.get('cf_cookie_dtf')

        if cookie:
            cmd.extend(['-H', f'Cookie: cf_clearance={cookie}'])

        # URL last
        cmd.append(url)

        try:
            return subprocess.check_output(cmd)
        except Exception as e:
            # Log specific curl error 
            raise Exception(f"Curl failed: {e}")

    def identify(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30):
        # 1. Check for specific identifiers
        plugin_id = identifiers.get('drivethrufiction', None)
        
        product_id = plugin_id
        # 2. Search if no ID
        if not product_id:
            query = self._create_query(title, authors)
            if not query:
                return

            print(f"DEBUG: Running from {__file__}")
            print(f"DEBUG: Query generated: '{query}'")
            log.info(f'Searching API (v2) for: {query}')
            try:
                # Strategy 1: Title + Author (Strict)
                matches = self._api_search(query, timeout, log)
                
                # Strategy 2: Title Only (Broad)
                if not matches and authors:
                    log.info("S1 Failed. Trying Title Only...")
                    q2 = self._create_query(title, [])
                    if q2 != query:
                         matches = self._api_search(q2, timeout, log)

                # Strategy 3: Cleaned Title (No v1.0, parens)
                if not matches:
                    clean_title = self._clean_title(title)
                    if clean_title != title:
                        log.info(f"S2 Failed. Trying Cleaned Title: '{clean_title}'")
                        matches = self._api_search(clean_title, timeout, log)
                        
                        # Strategy 4: First 4 words of Cleaned Title (Fuzzyish)
                        if not matches:
                            words = clean_title.split()
                            if len(words) > 4:
                                short_title = " ".join(words[:4])
                                log.info(f"S3 Failed. Trying Short Title: '{short_title}'")
                                matches = self._api_search(short_title, timeout, log)

                if not matches:
                    log.info('No results found via API after all attempts.')
                    return
                
                # Use first match
                product_id = matches[0]['id']
                log.info(f"Found match via API: {matches[0]['name']} (ID: {product_id})")
                
            except Exception as e:
                log.error(f'API Search failed: {e}')
                return

        # 3. Fetch Details
        if product_id:
            try:
                self._get_product_details(product_id, result_queue, log, timeout)
            except Exception as e:
                log.error(f'Failed to fetch details for ID {product_id}: {e}')

    def _api_search(self, query, timeout, log):
        import json
        # api.drivethrufiction.com/api/vBeta/search_ahead?keyword=...
        base = "https://api.drivethrufiction.com/api/vBeta/search_ahead"
        
        # Site ID: 70, Group ID: 25
        site_id = 70
        group_id = 25
        
        # Using the params captured from user
        url = f"{base}?groupId={group_id}&keyword={quote(query)}&siteId={site_id}"
        
        log.info(f"Searching: {url}")
        
        raw_json = self._fetch_via_curl(url, timeout)
        
        data = json.loads(raw_json)
        
        results = []
        if 'data' in data:
            for item in data['data']:
                attrs = item.get('attributes', {})
                pid = attrs.get('entityId')
                name = attrs.get('name')
                if pid and name:
                    # Filter out "Fantasy Grounds" content
                    if 'fantasy grounds' in name.lower():
                        continue
                    # Only products, ignore publishers? For now keep broadly useful
                    results.append({'id': pid, 'name': name})
        return results

    def _get_product_details(self, product_id, result_queue, log, timeout):
        import json
        from calibre.ebooks.metadata.book.base import Metadata
        
        url = f"https://api.drivethrufiction.com/api/vBeta/products/{product_id}"
        log.info(f"Fetching details from: {url}")
        
        raw_json = self._fetch_via_curl(url, timeout)
        root = json.loads(raw_json)
        
        data = root.get('data', {})
        attrs = data.get('attributes', {})
        
        # Title
        # Title is inside description.name usually
        desc_obj = attrs.get('description', {})
        title = desc_obj.get('name') or attrs.get('name') or "Unknown"
        
        # Authors
        authors = attrs.get('authors', [])
        if not authors:
            authors = ['Unknown']
            
        mi = Metadata(title, authors)
        mi.set_identifier('drivethrufiction', str(product_id))
        mi.source = self.name
        
        # Description
        mi.comments = desc_obj.get('description', '')
        
        # Publisher
        # Can extract from "included" section or attributes.publisherId
        # For simplicity, if included has type "Publisher", use that
        if 'included' in root:
            for inc in root['included']:
                if inc.get('type') == 'Publisher':
                    pub_attrs = inc.get('attributes', {})
                    if pub_attrs.get('name'):
                        mi.publisher = pub_attrs.get('name')
                        break
        
        # Date
        # "dateAvailable": "2018-04-25T13:39:15-05:00"
        date_str = attrs.get('dateAvailable')
        if date_str:
            from calibre.utils.date import parse_date
            try:
                mi.pubdate = parse_date(date_str)
            except:
                pass

        # Cover
        # "image": "8957/240640.jpg"
        img_path = attrs.get('image')
        if img_path:
            # Construct full URL
            cover_url = f"https://www.drivethrufiction.com/images/{img_path}"
            self.cache_cover_url(cover_url, str(product_id))

        result_queue.put(mi)

    def _create_query(self, title, authors):
        # Clean title
        tokens = []
        if title:
            tokens.append(title)
        if authors:
            tokens.append(authors[0]) 
        return " ".join(tokens)

    def _clean_title(self, title):
        if not title: return ""
        # Remove version numbers like v1.0, v2
        t = re.sub(r'(?i)\b(v|ver|vol)\.?\s*\d+(\.\d+)*\b', '', title)
        # Remove content in brackets/parens like (2020) or [PDF]
        t = re.sub(r'[\(\[].*?[\)\]]', '', t)
        # Remove extra whitespace
        return ' '.join(t.split())

    def download_cover(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30, get_best_cover=False):
        cached_url = self.get_cached_cover_url(identifiers)
        if cached_url:
            log.info(f"Downloading cover from: {cached_url}")
            try:
                # Use curl fallback for cover as well, just in case of CDN protections
                cdata = self._fetch_via_curl(cached_url, timeout)
                result_queue.put((self, cdata))
            except Exception as e:
                log.error(f'Failed to download cover from {cached_url}: {e}')
        else:
            log.info('No cached cover found, running identify to find it...')
            # Could re-run identify here or skip
            pass

    def get_cached_cover_url(self, identifiers):
        # Check our temp cache
        plugin_id = identifiers.get('drivethrufiction')
        if plugin_id:
            return getattr(self, '_cached_cover', {}).get(plugin_id)
        return None

    def cache_cover_url(self, url, product_id):
        if not hasattr(self, '_cached_cover'):
            self._cached_cover = {}
        self._cached_cover[product_id] = url

if __name__ == '__main__':
    # Local testing block
    from calibre.ebooks.metadata.sources.test import (test_identify_plugin,
            title_test, authors_test, series_test)
    
    # Try reading cookie files
    import os
    if os.path.exists('../cookie_dtf.txt'):
        with open('../cookie_dtf.txt', 'r') as f:
            cookie = f.read().strip()
            print(f"Using DTF cookie from file: {cookie[:10]}...")
            DriveThruFictionSource.prefs['cf_cookie_dtf'] = cookie
            
    print("Running DriveThruFiction tests...")
    tests = [
        (
            {'identifiers': {},
             'title': 'Dracula', 'authors': ['Bram Stoker']},
            [title_test('Dracula', exact=False)]
        )
    ]
    
    test_identify_plugin(DriveThruFictionSource.name, tests)
