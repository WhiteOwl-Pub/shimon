from typing import Optional
from urllib.parse import urljoin, urlparse, urlunparse

import requests

from .resource import Resource
from .utils import (
    get_content_type,
    get_md5,
    get_mmh3,
    get_response,
    get_sha1,
    get_sha256,
    get_soup,
)

LINK_RELS = [
    "icon",
    "shortcut icon",
    "apple-touch-icon",
    "apple-touch-icon-precomposed",
]


def is_absolute(url: str):
    return bool(urlparse(url).netloc)


def get_default_favicon_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, "favicon.ico", "", "", ""))


def get_favicon_urls_from_html(url: str, html: str) -> list[str]:
    soup = get_soup(html)

    link_tags = set()
    for rel in LINK_RELS:
        for link_tag in soup.find_all(
            "link", attrs={"rel": lambda r: r and r.lower() == rel, "href": True}
        ):
            link_tags.add(link_tag)

    icons: list[str] = []
    for tag in link_tags:
        href = tag.get("href", "") or tag.get("content", "")
        href = href.strip()

        if not href or href.startswith("data:image/"):
            continue

        if is_absolute(href):
            url_parsed = href
        else:
            url_parsed = urljoin(url, href)

        # repair '//cdn.network.com/favicon.png' or `icon.png?v2`
        scheme = urlparse(url).scheme
        url_parsed = urlparse(url_parsed, scheme=scheme)

        url = url_parsed.geturl()
        if url not in icons:
            icons.append(url)

    return icons


class Favicon(Resource):
    @classmethod
    def parse_response(cls, response: requests.Response) -> Optional["Favicon"]:
        favicon_urls = get_favicon_urls_from_html(response.url, response.text)
        favicon_urls.append(get_default_favicon_url(response.url))

        for url in favicon_urls:
            try:
                favicon_response = get_response(url)
                return cls(
                    content_type=get_content_type(favicon_response),
                    md5=get_md5(favicon_response),
                    mmh3=get_mmh3(favicon_response),
                    sha1=get_sha1(favicon_response),
                    sha256=get_sha256(favicon_response),
                    url=favicon_response.url,
                )
            except requests.HTTPError:
                pass

        return None
