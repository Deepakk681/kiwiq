"""
High-precision publication/updated date extraction for HTML pages (Scrapy-native).

Output model and precedence:
- We return two fields only: `published` and `updated` (ISO 8601 strings or None).
- "Published" always takes priority over any "created" value. If explicit
  published is not found but a reliable "created" is available, we use
  the created value as the published date.

Priority order (highest to lowest):
1) Request metadata (already parsed by upstream components)
   - published: feed_published_parsed, feed_created_parsed (fallback only)
   - updated:   feed_updated_parsed, url_last_modified
   Rationale: these are high-confidence server/feed-derived timestamps.

2) Structured data (JSON-LD Article/BlogPosting/NewsArticle)
   - published: datePublished
   - updated:   dateModified
   Rationale: SEO markup is explicit and widely used.

3) Meta tags
   - published: meta[property="article:published_time"], meta[name="DC.date.created"],
                meta[name="publish_date"], meta[name="date"]
   - updated:   meta[property="article:modified_time"], meta[name="DC.date.modified"],
                meta[name="last-modified"]
   Rationale: Site-level metadata is common and relatively reliable.

4) HTML5 <time> elements and common patterns
   - published: time[pubdate], time.published, elements with class/id containing
                publish/date (datetime attr or text)
   - updated:   time.updated, elements with class containing updated
   Rationale: Semantic DOM hints; good fallback when meta is missing.

5) HTTP response headers
   - published: Date header (very weak; only if nothing better)
   - updated:   Last-Modified header
   Rationale: Coarse server timings; only use as last fallback.

Implementation details:
- Pure Scrapy selectors; no secondary HTML parsers are used.
- Parsing uses conservative strategies and multiple datetime formats.
- Time zones: when a time zone/offset is present in the source value, the
  resulting ISO string is normalized to UTC and suffixed with 'Z'. If no
  time zone is present (naive datetime), the resulting ISO string is naive
  (no offset), preserving the ambiguity.
- `source_priority` captures which source provided each chosen value.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    from scrapy.http import Response


def _safe_parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse a datetime string using several strategies with graceful failure.

    Tries common ISO-8601 formats first, then RFC 2822 (HTTP dates), and
    optionally dateutil if available in environment.
    """
    if not value:
        return None
    v = value.strip()
    if not v:
        return None

    # 1) ISO 8601 common forms
    iso_candidates = [
        v,
        v.replace(" ", "T"),
    ]
    for cand in iso_candidates:
        try:
            # datetime.fromisoformat handles many ISO strings
            return datetime.fromisoformat(cand.replace("Z", "+00:00"))
        except Exception:
            pass

    # 2) RFC 2822 / HTTP-date (returns aware datetimes in UTC when possible)
    try:
        from email.utils import parsedate_to_datetime  # stdlib, safe

        dt = parsedate_to_datetime(v)
        if dt:
            # Some environments may return naive UTC; ensure awareness
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except Exception:
        pass

    # 3) dateutil (optional) — returns aware datetimes when TZ info present
    try:
        from dateutil import parser as dateutil_parser  # type: ignore

        dt = dateutil_parser.parse(v)  # type: ignore
        # If parser inferred UTC designator 'Z' or offset, keep it; else leave naive
        return dt
    except Exception:
        return None


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    try:
        # Normalize aware datetimes to UTC with trailing 'Z' for consistency
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        return dt.isoformat()
    except Exception:
        return None


@dataclass
class PageDates:
    """Container for page dates.

    Only two fields are returned:
    - published: publication datetime (ISO 8601) or None
    - updated:   last modified datetime (ISO 8601) or None

    Note: If explicit published is not found, a reliable created value
    will be used to populate `published`.
    """

    published: Optional[str]
    updated: Optional[str]
    source_priority: Dict[str, str]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PageDateParser:
    """Parse created/published/updated dates from a Scrapy Response.

    Priority order per method-level docstring above. This class avoids
    heavy parsing. It favors Scrapy selectors and exact attribute lookups.
    """

    def __init__(self, prefer_request_meta: bool = True) -> None:
        self.prefer_request_meta = prefer_request_meta

    def extract(self, response: "Response") -> PageDates:
        """Extract best-effort dates with priority and return as ISO strings.

        Order of attempts: request.meta → JSON-LD → meta tags → time elements → headers.
        """
        published_dt: Optional[datetime] = None
        updated_dt: Optional[datetime] = None
        created_dt: Optional[datetime] = None  # internal-only fallback for published
        source_priority: Dict[str, str] = {}

        # 1) Request meta: feed and sitemap
        if self.prefer_request_meta and response.request is not None:
            meta = response.request.meta or {}
            for key, target in [
                ("feed_published_parsed", "published"),
                ("feed_created_parsed", "created"),
                ("feed_updated_parsed", "updated"),
                ("url_last_modified", "updated"),
            ]:
                value = meta.get(key)
                if isinstance(value, datetime):
                    if target == "published" and published_dt is None:
                        published_dt = value
                        source_priority.setdefault("published", key)
                    if target == "updated" and updated_dt is None:
                        updated_dt = value
                        source_priority.setdefault("updated", key)
                    if target == "created" and created_dt is None:
                        created_dt = value
                elif isinstance(value, str):
                    parsed = _safe_parse_datetime(value)
                    if parsed:
                        if target == "published" and published_dt is None:
                            published_dt = parsed
                            source_priority.setdefault("published", key)
                        if target == "updated" and updated_dt is None:
                            updated_dt = parsed
                            source_priority.setdefault("updated", key)
                        if target == "created" and created_dt is None:
                            created_dt = parsed

        # Early exit if both already set
        if published_dt and updated_dt:
            return PageDates(
                published=_to_iso(published_dt),
                updated=_to_iso(updated_dt),
                source_priority=source_priority,
            )

        # 2) Structured data: JSON-LD
        try:
            json_ld_blocks = response.css('script[type="application/ld+json"]::text').getall()
            import json

            for block in json_ld_blocks:
                try:
                    data = json.loads(block)
                except Exception:
                    continue

                def _extract_from_obj(obj: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime]]:
                    type_val = obj.get("@type")
                    if isinstance(type_val, list):
                        type_list = [t.lower() for t in type_val if isinstance(t, str)]
                    elif isinstance(type_val, str):
                        type_list = [type_val.lower()]
                    else:
                        type_list = []

                    if any(t in {"article", "blogposting", "newsarticle"} for t in type_list):
                        pub = _safe_parse_datetime(obj.get("datePublished"))
                        mod = _safe_parse_datetime(obj.get("dateModified"))
                        return pub, mod
                    return None, None

                candidates: list[Dict[str, Any]] = []
                if isinstance(data, list):
                    candidates.extend([d for d in data if isinstance(d, dict)])
                elif isinstance(data, dict):
                    candidates.append(data)

                for obj in candidates:
                    pub, mod = _extract_from_obj(obj)
                    if pub and not published_dt:
                        published_dt = pub
                        source_priority.setdefault("published", "json_ld")
                    if mod and not updated_dt:
                        updated_dt = mod
                        source_priority.setdefault("updated", "json_ld")
                    if published_dt and updated_dt:
                        break
                if published_dt and updated_dt:
                    break
        except Exception:
            pass

        # 3) Meta tags: Open Graph + Dublin Core + generic
        if not published_dt:
            published_dt = _safe_parse_datetime(
                response.css('meta[property="article:published_time"]::attr(content)').get()
                or response.css('meta[name="DC.date.created"]::attr(content)').get()
                or response.css('meta[name="publish_date"]::attr(content)').get()
                or response.css('meta[name="date"]::attr(content)').get()
            ) or published_dt
            if published_dt:
                source_priority.setdefault("published", "meta")

        if not updated_dt:
            updated_dt = _safe_parse_datetime(
                response.css('meta[property="article:modified_time"]::attr(content)').get()
                or response.css('meta[name="DC.date.modified"]::attr(content)').get()
                or response.css('meta[name="last-modified"]::attr(content)').get()
            ) or updated_dt
            if updated_dt:
                source_priority.setdefault("updated", "meta")

        # 4) HTML5 time elements and CSS selector patterns
        if not published_dt:
            published_dt = _safe_parse_datetime(
                response.css('time[pubdate]::attr(datetime)').get()
                or response.css('time.published::attr(datetime)').get()
                or response.css('time.published::text').get()
                or response.css('[class*="publish"] time::attr(datetime)').get()
                or response.css('[class*="publish"]::attr(datetime)').get()
                or response.css('[class*="date"] time::attr(datetime)').get()
                or response.css('[class*="date"]::attr(datetime)').get()
                or response.css('[id*="post-date"]::attr(datetime)').get()
            ) or published_dt
            if published_dt:
                source_priority.setdefault("published", "time_element")

        if not updated_dt:
            updated_dt = _safe_parse_datetime(
                response.css('time.updated::attr(datetime)').get()
                or response.css('time.updated::text').get()
                or response.css('[class*="updated"] time::attr(datetime)').get()
                or response.css('[class*="updated"]::attr(datetime)').get()
            ) or updated_dt
            if updated_dt:
                source_priority.setdefault("updated", "time_element")

        # 5) HTTP headers as final fallback
        if not updated_dt:
            try:
                last_mod = response.headers.get(b"Last-Modified")
                if last_mod:
                    updated_dt = _safe_parse_datetime(last_mod.decode("utf-8", errors="ignore"))
                    if updated_dt:
                        source_priority.setdefault("updated", "http_header_last_modified")
            except Exception:
                pass

        # if not published_dt:
        #     try:
        #         date_hdr = response.headers.get(b"Date")
        #         if date_hdr:
        #             published_dt = _safe_parse_datetime(date_hdr.decode("utf-8", errors="ignore"))
        #             if published_dt:
        #                 source_priority.setdefault("published", "http_header_date")
        #     except Exception:
        #         pass

        # Finalize values
        # If no explicit published, but a created was found, use created as published
        if not published_dt and created_dt:
            published_dt = created_dt
            source_priority.setdefault("published", "created_fallback")

        return PageDates(
            published=_to_iso(published_dt),
            updated=_to_iso(updated_dt),
            source_priority=source_priority,
        )

