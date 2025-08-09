import feedparser
import re
import calendar
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, MutableMapping, Optional, Tuple, Union

# Type aliases for clarity
Url = str
UrlMetadata = Dict[str, Any]
FlatResults = Dict[Url, UrlMetadata]
CategorizedResults = Dict[str, FlatResults]

def extract_urls_from_feed(
    feed_url: str,
    extract_media: bool = False,
    extract_embedded_urls: bool = True,
    flatten_results: bool = True,
) -> Union[FlatResults, CategorizedResults]:
    """
    Parse an RSS/Atom feed and extract content URLs with minimal metadata.

    This function focuses on extracting date metadata as timezone-aware
    datetime objects (UTC) for simplicity and consistency:
      - feed_published_parsed (datetime)
      - feed_updated_parsed (datetime)
      - feed_created_parsed (datetime)

    Args:
        feed_url: An HTTP(S) URL to the feed (or a feed string/bytes supported by feedparser.parse).
        extract_media: When True, include media/enclosure URLs found in entries.
        extract_embedded_urls: When True, also scan entry content/summary text for embedded URLs.
        flatten_results: When True, return a flat mapping of URL -> metadata. When False, return
            a categorized mapping with buckets like 'article_urls', 'alternate_urls', etc.

    Returns:
        - If flatten_results=True: Dict[Url, UrlMetadata]
        - If flatten_results=False: Dict[str, Dict[Url, UrlMetadata]]

    Notes:
        - Only the "*_parsed" variants of dates are included (struct_time objects from feedparser).
        - Keys used for dates are prefixed with 'feed_' to clearly indicate the source.
    """
    # Parse the feed
    feed = feedparser.parse(feed_url)
    
    # Initialize URL containers - now stores URL->metadata mappings
    urls = {
        'article_urls': {},      # Primary article/blog post URLs
        'source_urls': {},       # Original source URLs (if different from article)
        'comment_urls': {},      # Comment/discussion URLs
        'feed_home': {},         # Feed's home page
        'alternate_urls': {},    # Alternative versions (AMP, mobile, etc.)
        'embedded_urls': {},     # URLs found within content
        'all_content_urls': {}   # All non-media URLs
    }
    
    if extract_media:
        urls.update({
            'media_urls': {},    # Images, videos, audio
            'enclosure_urls': {} # Podcast episodes, attachments
        })
    
    # Helper function to extract date metadata from entry
    def get_entry_dates(entry) -> UrlMetadata:
        """Extract parsed date metadata from a feed entry as UTC datetimes."""
        dates: UrlMetadata = {}

        # Convert struct_time to aware UTC datetimes using calendar.timegm
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dates['feed_published_parsed'] = datetime.fromtimestamp(
                calendar.timegm(entry.published_parsed), tz=timezone.utc
            )

        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            dates['feed_updated_parsed'] = datetime.fromtimestamp(
                calendar.timegm(entry.updated_parsed), tz=timezone.utc
            )

        if hasattr(entry, 'created_parsed') and entry.created_parsed:
            dates['feed_created_parsed'] = datetime.fromtimestamp(
                calendar.timegm(entry.created_parsed), tz=timezone.utc
            )

        return dates
    
    # Helper function to add URL with metadata
    def add_url(url: Url, category: str = 'all_content_urls', metadata: Optional[UrlMetadata] = None) -> None:
        if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
            if not extract_media and category in ['media_urls', 'enclosure_urls']:
                return  # Skip media URLs if not requested
            
            # Initialize metadata if not provided
            if metadata is None:
                metadata = {}
            
            # Add to all_content_urls
            urls['all_content_urls'][url] = metadata
            if category in urls:
                urls[category][url] = metadata
    
    # Extract feed-level URLs (blog/site home)
    if hasattr(feed, 'feed'):
        # Get feed-level dates if available (only parsed version)
        feed_metadata: UrlMetadata = {}
        if hasattr(feed.feed, 'updated_parsed') and feed.feed.updated_parsed:
            feed_metadata['feed_updated_parsed'] = datetime.fromtimestamp(
                calendar.timegm(feed.feed.updated_parsed), tz=timezone.utc
            )
        
        # Main feed link (usually the blog's homepage)
        if hasattr(feed.feed, 'link'):
            add_url(feed.feed.link, 'feed_home', feed_metadata.copy())
        
        # Alternate feed links
        if hasattr(feed.feed, 'links'):
            for link in feed.feed.links:
                if hasattr(link, 'href') and hasattr(link, 'type'):
                    # Skip feed URLs (xml, rss, atom)
                    if 'xml' not in link.type and 'rss' not in link.type:
                        add_url(link.href, 'feed_home', feed_metadata.copy())
    
    # Extract entry-level URLs (the main content)
    for entry in feed.entries:
        # Get date metadata for this entry
        entry_metadata: UrlMetadata = get_entry_dates(entry)
        entry_metadata['from_feed'] = True
        
        # Primary article URL - this is what you want most of the time
        if hasattr(entry, 'link'):
            add_url(entry.link, 'article_urls', entry_metadata.copy())
        
        # Handle multiple links (some feeds provide multiple URLs per entry)
        if hasattr(entry, 'links'):
            for link in entry.links:
                if hasattr(link, 'href'):
                    # Categorize by relationship type
                    rel = getattr(link, 'rel', 'alternate')
                    
                    if rel == 'alternate':
                        # Usually the main article URL or alternative format
                        if not hasattr(entry, 'link') or entry.link != link.href:
                            add_url(link.href, 'alternate_urls', entry_metadata.copy())
                        else:
                            add_url(link.href, 'article_urls', entry_metadata.copy())
                    
                    elif rel == 'replies' or 'comment' in rel:
                        # Comments/discussion URL
                        add_url(link.href, 'comment_urls', entry_metadata.copy())
                    
                    elif rel == 'enclosure' and extract_media:
                        # Media attachments (podcasts, videos)
                        add_url(link.href, 'enclosure_urls', entry_metadata.copy())
                    
                    elif rel == 'via' or rel == 'source':
                        # Original source (for aggregators)
                        add_url(link.href, 'source_urls', entry_metadata.copy())
        
        # Entry ID (sometimes contains the permalink)
        if hasattr(entry, 'id') and entry.id.startswith(('http://', 'https://')):
            # Only add if different from main link
            if not hasattr(entry, 'link') or entry.id != entry.link:
                add_url(entry.id, 'alternate_urls', entry_metadata.copy())
        
        # Source URL (for content aggregators)
        if hasattr(entry, 'source'):
            if hasattr(entry.source, 'href'):
                add_url(entry.source.href, 'source_urls', entry_metadata.copy())
            if hasattr(entry.source, 'link'):
                add_url(entry.source.link, 'source_urls', entry_metadata.copy())
        
        # Comments URL
        if hasattr(entry, 'comments'):
            add_url(entry.comments, 'comment_urls', entry_metadata.copy())
        
        # Extract media if requested
        if extract_media:
            _extract_media_urls(entry, urls, add_url, entry_metadata)
        
        # Extract URLs from content (optional)
        if extract_embedded_urls:
            _extract_embedded_urls(entry, urls, add_url, extract_media, entry_metadata)
    
    # Return results based on flatten_results flag
    if flatten_results:
        # Return all_content_urls dict (URL -> metadata mapping)
        return urls.get('all_content_urls', {})
    else:
        # Return categorized URLs with metadata
        return urls

def _extract_media_urls(entry, urls, add_url, entry_metadata: Optional[UrlMetadata] = None) -> None:
    """Extract media-related URLs from an entry."""
    if entry_metadata is None:
        entry_metadata = {}
    
    # Enclosures
    if hasattr(entry, 'enclosures'):
        for enclosure in entry.enclosures:
            if hasattr(enclosure, 'href'):
                add_url(enclosure.href, 'enclosure_urls', entry_metadata.copy())
            if hasattr(enclosure, 'url'):
                add_url(enclosure.url, 'enclosure_urls', entry_metadata.copy())
    
    # Media RSS extensions
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if hasattr(media, 'url'):
                add_url(media.url, 'media_urls', entry_metadata.copy())
    
    if hasattr(entry, 'media_thumbnail'):
        for thumb in entry.media_thumbnail:
            if hasattr(thumb, 'url'):
                add_url(thumb.url, 'media_urls', entry_metadata.copy())
    
    # iTunes extensions (podcasts)
    if hasattr(entry, 'itunes_image'):
        add_url(entry.itunes_image, 'media_urls', entry_metadata.copy())

def _extract_embedded_urls(entry, urls, add_url, include_media: bool = False, entry_metadata: Optional[UrlMetadata] = None) -> None:
    """Extract URLs embedded in content text."""
    if entry_metadata is None:
        entry_metadata = {}
    
    # URL regex pattern
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+/?(?:[-\w.,@?^=%&:/~+#])*(?:[-\w@?^=%&/~+#])?'
    
    # Common media extensions to filter out
    media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', 
                       '.mp3', '.mp4', '.avi', '.mov', '.webm', '.ogg'}
    
    def extract_from_text(text):
        if not text:
            return
        urls_found = re.findall(url_pattern, str(text))
        for url in urls_found:
            # Check if it's a media URL
            is_media = any(url.lower().endswith(ext) for ext in media_extensions)
            
            if is_media and include_media:
                add_url(url, 'media_urls', entry_metadata.copy())
            elif not is_media:
                add_url(url, 'embedded_urls', entry_metadata.copy())
    
    # Check content
    if hasattr(entry, 'content'):
        for content in entry.content:
            if hasattr(content, 'value'):
                extract_from_text(content.value)
    
    # Check summary/description
    if hasattr(entry, 'summary'):
        extract_from_text(entry.summary)
    if hasattr(entry, 'description'):
        extract_from_text(entry.description)


if __name__ == "__main__":
    """
    Simple test harness:
    - Fetches a feed URL (defaults to Hacker News RSS)
    - Prints a sample of extracted URLs and their parsed date metadata
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Test extract_urls_from_feed on a live RSS/Atom feed.")
    parser.add_argument(
        "--feed-url",
        type=str,
        default="https://news.ycombinator.com/rss",
        help="Feed URL to parse (default: Hacker News RSS)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max number of URLs to print",
    )
    args = parser.parse_args()

    print("Parsing feed:", args.feed_url)
    results: FlatResults = extract_urls_from_feed(args.feed_url, flatten_results=True)  # type: ignore[assignment]
    print(f"Total URLs discovered: {len(results)}")

    shown = 0
    for url, metadata in results.items():
        print(f"\nURL: {url}")
        # Show only the parsed date fields if present
        for k in ("feed_published_parsed", "feed_updated_parsed", "feed_created_parsed"):
            if k in metadata and metadata[k]:
                dt = metadata[k]
                try:
                    print(f"  {k}: {dt.isoformat()}")
                except Exception:
                    print(f"  {k}: {dt}")
        shown += 1
        if shown >= args.limit:
            break

    if shown == 0:
        print("No URLs found in the provided feed.")
