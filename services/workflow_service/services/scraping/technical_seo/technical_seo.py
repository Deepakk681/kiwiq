"""
High Accuracy SEO Analysis Script

This script performs reliable technical SEO analysis on HTML content,
focusing only on elements that can be extracted with 99% accuracy.

Features:
- Title tag analysis
- Header structure analysis (H1-H6)
- Meta tags extraction (description, robots, viewport)
- Canonical tag validation
- Internal and external link analysis
- Image optimization analysis (alt text)
- Technical SEO factors (HTTPS, HTML lang)
- Open Graph detection
- Structured lists and code blocks counting

Usage:
    # Single page analysis
    from high_accuracy_seo_analyzer import SEOAnalyzer
    
    analyzer = SEOAnalyzer()
    result = analyzer.analyze_page(html_content, page_url)
    
    # Multiple pages analysis
    results = analyzer.analyze_multiple_pages(pages_data)
    
    # Generate summary report
    report = analyzer.generate_summary_report(results)
"""

import json
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime

if TYPE_CHECKING:
    from scrapy.http import Response as ScrapyResponse


@dataclass
class TitleAnalysis:
    """Title tag analysis"""
    exists: bool
    text: str
    length_chars: int
    length_words: int


@dataclass
class HeaderStructure:
    """Header tags (H1-H6) analysis"""
    h1_count: int
    h1_texts: List[str]
    h2_count: int
    h2_texts: List[str]
    h3_count: int
    h3_texts: List[str]
    h4_count: int
    h5_count: int
    h6_count: int
    has_proper_hierarchy: bool
    hierarchy_issues: List[str]


@dataclass
class MetaTagsAnalysis:
    """Meta tags analysis"""
    description_exists: bool
    description_text: str
    description_length_chars: int
    description_length_words: int
    robots_exists: bool
    robots_content: str
    has_noindex: bool
    has_nofollow: bool
    viewport_exists: bool
    viewport_content: str
    is_mobile_friendly: bool


@dataclass
class CanonicalAnalysis:
    """Canonical tag analysis"""
    exists: bool
    url: str
    is_self_referencing: bool
    is_absolute_url: bool
    is_same_domain: bool
    uses_https: bool


@dataclass
class LinkAnalysis:
    """Internal and external links analysis"""
    internal_links_count: int
    internal_links_unique_count: int
    external_links_count: int
    external_links_unique_count: int
    external_domains: List[str]
    total_links_count: int
    # Percentage metrics for standardization (0-100 scale)
    internal_links_percentage: float  # Percentage of internal links out of total links
    external_links_percentage: float  # Percentage of external links out of total links
    unique_internal_percentage: float  # Percentage of unique internal links out of total unique links
    unique_external_percentage: float  # Percentage of unique external links out of total unique links
    # Sample of internal and external links for review
    internal_links_sample: List[str]  # First 10 unique internal links
    external_links_sample: List[str]  # First 10 unique external links


@dataclass
class ImageAnalysis:
    """Image optimization analysis"""
    total_images: int
    images_with_alt: int
    images_without_alt: int
    alt_text_coverage_percentage: float
    images_with_empty_alt: int
    # Sample of images without alt text for review
    images_without_alt_sample: List[str]  # First 5 images without alt


@dataclass
class TechnicalFactors:
    """Technical SEO factors"""
    uses_https: bool
    has_html_lang: bool
    html_lang_value: str
    has_charset: bool
    charset_value: str


@dataclass
class OpenGraphAnalysis:
    """Open Graph meta tags analysis"""
    has_og_tags: bool
    og_tags_count: int
    has_og_title: bool
    has_og_description: bool
    has_og_image: bool
    has_og_url: bool
    has_og_type: bool
    og_type_value: str


@dataclass
class StructuredContent:
    """Structured content elements"""
    ordered_lists_count: int
    unordered_lists_count: int
    code_blocks_count: int
    tables_count: int
    forms_count: int
    iframes_count: int


@dataclass
class SchemaMarkup:
    """Basic schema.org detection"""
    has_json_ld: bool
    has_microdata: bool
    json_ld_types: List[str]
    microdata_types: List[str]


@dataclass
class SEOAnalysisResult:
    """Complete SEO analysis result for a single page"""
    url: str
    analysis_timestamp: str
    title: TitleAnalysis
    headers: HeaderStructure
    meta_tags: MetaTagsAnalysis
    canonical: CanonicalAnalysis
    links: LinkAnalysis
    images: ImageAnalysis
    technical: TechnicalFactors
    open_graph: OpenGraphAnalysis
    structured_content: StructuredContent
    schema: SchemaMarkup
    # Extended schema.org types analysis
    schema_types: Optional['SchemaTypesAnalysis'] = None
    

@dataclass
class SummaryReport:
    """Summary report for multiple pages"""
    total_pages_analyzed: int
    analysis_timestamp: str
    
    # Aggregated metrics (percentages)
    pages_with_title_percentage: float
    pages_with_meta_description_percentage: float
    pages_with_h1_percentage: float
    pages_with_multiple_h1_percentage: float
    pages_with_proper_hierarchy_percentage: float
    pages_with_canonical_percentage: float
    pages_with_self_referencing_canonical_percentage: float
    pages_mobile_friendly_percentage: float
    pages_using_https_percentage: float
    pages_with_html_lang_percentage: float
    pages_with_og_tags_percentage: float
    pages_with_schema_percentage: float
    pages_with_noindex_percentage: float
    
    # Averages
    avg_title_length_words: float
    avg_meta_description_length_words: float
    avg_h1_count: float
    avg_h2_count: float
    avg_internal_links: float
    avg_external_links: float
    avg_images_per_page: float
    avg_alt_text_coverage: float
    # Link distribution averages (0-100 scale for standardization)
    avg_internal_links_percentage: float  # Average percentage of internal links across pages
    avg_external_links_percentage: float  # Average percentage of external links across pages
    
    # Issues summary
    common_issues: List[Dict[str, any]]
    # Optional nested schema types summary for group analysis
    schema_types_summary: Optional['SchemaTypesSummary'] = None
    # Percentage of documents whose URLs were present in sitemap (from spider)
    pages_in_sitemap_percentage: float = 0.0


# class SEOAnalyzer:
#     """High-accuracy SEO analyzer for HTML content"""
    
#     def __init__(self):
#         """Initialize the SEO analyzer"""
#         pass
    
#     def _count_words(self, text: str) -> int:
#         """Count words in text"""
#         if not text:
#             return 0
#         words = re.findall(r'\b\w+\b', text)
#         return len(words)
    
#     def _analyze_title(self, soup: BeautifulSoup) -> TitleAnalysis:
#         """Analyze title tag"""
#         title_tag = soup.find('title')
        
#         if not title_tag:
#             return TitleAnalysis(
#                 exists=False,
#                 text="",
#                 length_chars=0,
#                 length_words=0
#             )
        
#         title_text = title_tag.get_text().strip()
        
#         return TitleAnalysis(
#             exists=True,
#             text=title_text,
#             length_chars=len(title_text),
#             length_words=self._count_words(title_text)
#         )
    
#     def _analyze_headers(self, soup: BeautifulSoup) -> HeaderStructure:
#         """Analyze header structure (H1-H6)"""
#         h1_tags = soup.find_all('h1')
#         h2_tags = soup.find_all('h2')
#         h3_tags = soup.find_all('h3')
#         h4_tags = soup.find_all('h4')
#         h5_tags = soup.find_all('h5')
#         h6_tags = soup.find_all('h6')
        
#         # Extract text from headers
#         h1_texts = [tag.get_text().strip() for tag in h1_tags if tag.get_text().strip()]
#         h2_texts = [tag.get_text().strip() for tag in h2_tags if tag.get_text().strip()]
#         h3_texts = [tag.get_text().strip() for tag in h3_tags if tag.get_text().strip()]
        
#         # Check hierarchy
#         hierarchy_issues = []
#         has_proper_hierarchy = True
        
#         # Check for missing H1
#         if len(h1_tags) == 0:
#             hierarchy_issues.append("Missing H1 tag")
#             has_proper_hierarchy = False
#         elif len(h1_tags) > 1:
#             hierarchy_issues.append(f"Multiple H1 tags found ({len(h1_tags)})")
#             has_proper_hierarchy = False
        
#         # Check for skipped heading levels
#         heading_levels = []
#         if len(h1_tags) > 0: heading_levels.append(1)
#         if len(h2_tags) > 0: heading_levels.append(2)
#         if len(h3_tags) > 0: heading_levels.append(3)
#         if len(h4_tags) > 0: heading_levels.append(4)
#         if len(h5_tags) > 0: heading_levels.append(5)
#         if len(h6_tags) > 0: heading_levels.append(6)
        
#         for i in range(1, len(heading_levels)):
#             if heading_levels[i] - heading_levels[i-1] > 1:
#                 hierarchy_issues.append(f"Skipped heading level from H{heading_levels[i-1]} to H{heading_levels[i]}")
#                 has_proper_hierarchy = False
        
#         return HeaderStructure(
#             h1_count=len(h1_tags),
#             h1_texts=h1_texts,
#             h2_count=len(h2_tags),
#             h2_texts=h2_texts,
#             h3_count=len(h3_tags),
#             h3_texts=h3_texts,
#             h4_count=len(h4_tags),
#             h5_count=len(h5_tags),
#             h6_count=len(h6_tags),
#             has_proper_hierarchy=has_proper_hierarchy,
#             hierarchy_issues=hierarchy_issues
#         )
    
#     def _analyze_meta_tags(self, soup: BeautifulSoup) -> MetaTagsAnalysis:
#         """Analyze meta tags"""
#         # Meta description
#         meta_desc = soup.find('meta', attrs={'name': 'description'})
#         desc_exists = meta_desc is not None
#         desc_text = meta_desc.get('content', '').strip() if meta_desc else ""
        
#         # Meta robots
#         meta_robots = soup.find('meta', attrs={'name': 'robots'})
#         robots_exists = meta_robots is not None
#         robots_content = meta_robots.get('content', '').lower() if meta_robots else ""
#         has_noindex = 'noindex' in robots_content
#         has_nofollow = 'nofollow' in robots_content
        
#         # Viewport meta
#         viewport = soup.find('meta', attrs={'name': 'viewport'})
#         viewport_exists = viewport is not None
#         viewport_content = viewport.get('content', '').lower() if viewport else ""
        
#         # Check mobile-friendly criteria
#         is_mobile_friendly = False
#         if viewport_content:
#             has_device_width = 'width=device-width' in viewport_content
#             has_initial_scale = 'initial-scale=1' in viewport_content
#             is_mobile_friendly = has_device_width and has_initial_scale
        
#         return MetaTagsAnalysis(
#             description_exists=desc_exists,
#             description_text=desc_text,
#             description_length_chars=len(desc_text),
#             description_length_words=self._count_words(desc_text),
#             robots_exists=robots_exists,
#             robots_content=robots_content,
#             has_noindex=has_noindex,
#             has_nofollow=has_nofollow,
#             viewport_exists=viewport_exists,
#             viewport_content=viewport_content,
#             is_mobile_friendly=is_mobile_friendly
#         )
    
#     def _analyze_canonical(self, soup: BeautifulSoup, page_url: str) -> CanonicalAnalysis:
#         """Analyze canonical tag"""
#         canonical = soup.find('link', rel='canonical')
        
#         if not canonical:
#             return CanonicalAnalysis(
#                 exists=False,
#                 url="",
#                 is_self_referencing=False,
#                 is_absolute_url=False,
#                 is_same_domain=False,
#                 uses_https=False
#             )
        
#         canonical_url = canonical.get('href', '').strip()
        
#         # Parse URLs for comparison
#         page_parsed = urlparse(page_url)
#         canonical_parsed = urlparse(canonical_url)
        
#         # Check if absolute URL
#         is_absolute = bool(canonical_parsed.scheme and canonical_parsed.netloc)
        
#         # Check if same domain
#         is_same_domain = False
#         if is_absolute:
#             is_same_domain = page_parsed.netloc.lower() == canonical_parsed.netloc.lower()
        
#         # Check if self-referencing (normalize URLs for comparison)
#         is_self_referencing = False
#         if is_absolute and is_same_domain:
#             page_path = page_parsed.path.rstrip('/')
#             canonical_path = canonical_parsed.path.rstrip('/')
#             is_self_referencing = page_path == canonical_path
        
#         # Check HTTPS
#         uses_https = canonical_parsed.scheme == 'https'
        
#         return CanonicalAnalysis(
#             exists=True,
#             url=canonical_url,
#             is_self_referencing=is_self_referencing,
#             is_absolute_url=is_absolute,
#             is_same_domain=is_same_domain,
#             uses_https=uses_https
#         )
    
#     def _analyze_links(self, soup: BeautifulSoup, page_url: str) -> LinkAnalysis:
#         """Analyze internal and external links"""
#         all_links = soup.find_all('a', href=True)
#         page_domain = urlparse(page_url).netloc.lower()
        
#         internal_links = set()
#         external_links = set()
#         external_domains = set()
        
#         for link in all_links:
#             href = link.get('href', '').strip()
            
#             # Skip anchors, mailto, tel, and javascript
#             if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
#                 continue
            
#             # Parse the URL
#             if href.startswith(('http://', 'https://')):
#                 # Absolute URL
#                 link_domain = urlparse(href).netloc.lower()
#                 if link_domain == page_domain:
#                     internal_links.add(href)
#                 else:
#                     external_links.add(href)
#                     external_domains.add(link_domain)
#             elif href.startswith('/'):
#                 # Relative URL (internal)
#                 internal_links.add(href)
#             elif href:
#                 # Relative URL without leading slash (internal)
#                 internal_links.add(href)
        
#         return LinkAnalysis(
#             internal_links_count=len([l for l in all_links if l.get('href', '').strip() and 
#                                      not l.get('href', '').startswith(('#', 'mailto:', 'tel:', 'javascript:'))]),
#             internal_links_unique_count=len(internal_links),
#             external_links_count=len(external_links),
#             external_links_unique_count=len(external_links),
#             external_domains=sorted(list(external_domains)),
#             total_links_count=len(all_links),
#             internal_links_sample=sorted(list(internal_links))[:10],
#             external_links_sample=sorted(list(external_links))[:10]
#         )
    
#     def _analyze_images(self, soup: BeautifulSoup) -> ImageAnalysis:
#         """Analyze images and alt text"""
#         all_images = soup.find_all('img')
#         total = len(all_images)
        
#         with_alt = 0
#         without_alt = 0
#         empty_alt = 0
#         without_alt_sample = []
        
#         for img in all_images:
#             if img.has_attr('alt'):
#                 alt_text = img.get('alt', '').strip()
#                 if alt_text:
#                     with_alt += 1
#                 else:
#                     empty_alt += 1
#                     with_alt += 1  # Empty alt is still valid for decorative images
#             else:
#                 without_alt += 1
#                 src = img.get('src', 'unknown')
#                 if len(without_alt_sample) < 5:
#                     without_alt_sample.append(src)
        
#         coverage = (with_alt / total * 100) if total > 0 else 100.0
        
#         return ImageAnalysis(
#             total_images=total,
#             images_with_alt=with_alt,
#             images_without_alt=without_alt,
#             alt_text_coverage_percentage=round(coverage, 2),
#             images_with_empty_alt=empty_alt,
#             images_without_alt_sample=without_alt_sample
#         )
    
#     def _analyze_technical_factors(self, soup: BeautifulSoup, page_url: str) -> TechnicalFactors:
#         """Analyze technical SEO factors"""
#         # HTTPS check
#         uses_https = page_url.startswith('https://')
        
#         # HTML lang attribute
#         html_tag = soup.find('html')
#         has_lang = False
#         lang_value = ""
#         if html_tag:
#             lang_value = html_tag.get('lang', '').strip()
#             has_lang = bool(lang_value)
        
#         # Charset
#         charset_meta = soup.find('meta', charset=True)
#         if not charset_meta:
#             charset_meta = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        
#         has_charset = charset_meta is not None
#         charset_value = ""
#         if charset_meta:
#             if charset_meta.has_attr('charset'):
#                 charset_value = charset_meta.get('charset', '').strip()
#             else:
#                 content = charset_meta.get('content', '')
#                 if 'charset=' in content:
#                     charset_value = content.split('charset=')[-1].strip()
        
#         return TechnicalFactors(
#             uses_https=uses_https,
#             has_html_lang=has_lang,
#             html_lang_value=lang_value,
#             has_charset=has_charset,
#             charset_value=charset_value
#         )
    
#     def _analyze_open_graph(self, soup: BeautifulSoup) -> OpenGraphAnalysis:
#         """Analyze Open Graph meta tags"""
#         og_tags = soup.find_all('meta', attrs={'property': lambda x: x and x.startswith('og:')})
        
#         has_og = len(og_tags) > 0
#         og_title = soup.find('meta', attrs={'property': 'og:title'}) is not None
#         og_desc = soup.find('meta', attrs={'property': 'og:description'}) is not None
#         og_image = soup.find('meta', attrs={'property': 'og:image'}) is not None
#         og_url = soup.find('meta', attrs={'property': 'og:url'}) is not None
#         og_type_tag = soup.find('meta', attrs={'property': 'og:type'})
#         og_type = og_type_tag.get('content', '').strip() if og_type_tag else ""
        
#         return OpenGraphAnalysis(
#             has_og_tags=has_og,
#             og_tags_count=len(og_tags),
#             has_og_title=og_title,
#             has_og_description=og_desc,
#             has_og_image=og_image,
#             has_og_url=og_url,
#             has_og_type=bool(og_type),
#             og_type_value=og_type
#         )
    
#     def _analyze_structured_content(self, soup: BeautifulSoup) -> StructuredContent:
#         """Analyze structured content elements"""
#         return StructuredContent(
#             ordered_lists_count=len(soup.find_all('ol')),
#             unordered_lists_count=len(soup.find_all('ul')),
#             code_blocks_count=len(soup.find_all('code')) + len(soup.find_all('pre')),
#             tables_count=len(soup.find_all('table')),
#             forms_count=len(soup.find_all('form')),
#             iframes_count=len(soup.find_all('iframe'))
#         )
    
#     def _analyze_schema(self, soup: BeautifulSoup) -> SchemaMarkup:
#         """Analyze schema.org markup"""
#         # JSON-LD
#         json_ld_scripts = soup.find_all('script', type='application/ld+json')
#         json_ld_types = []
        
#         for script in json_ld_scripts:
#             try:
#                 if script.string:
#                     data = json.loads(script.string)
#                     if isinstance(data, dict) and '@type' in data:
#                         json_ld_types.append(data['@type'])
#                     elif isinstance(data, list):
#                         for item in data:
#                             if isinstance(item, dict) and '@type' in item:
#                                 json_ld_types.append(item['@type'])
#             except (json.JSONDecodeError, KeyError):
#                 continue
        
#         # Microdata
#         microdata_items = soup.find_all(attrs={'itemtype': True})
#         microdata_types = []
        
#         for item in microdata_items:
#             itemtype = item.get('itemtype', '')
#             if 'schema.org' in itemtype:
#                 schema_type = itemtype.split('/')[-1]
#                 microdata_types.append(schema_type)
        
#         return SchemaMarkup(
#             has_json_ld=len(json_ld_scripts) > 0,
#             has_microdata=len(microdata_items) > 0,
#             json_ld_types=list(set(json_ld_types)),
#             microdata_types=list(set(microdata_types))
#         )
    
#     def analyze_page(self, html_content: str, page_url: str) -> SEOAnalysisResult:
#         """
#         Analyze a single HTML page for SEO factors
        
#         Args:
#             html_content: HTML content as string
#             page_url: URL of the page being analyzed
            
#         Returns:
#             SEOAnalysisResult object with all analysis data
#         """
#         soup = BeautifulSoup(html_content, 'html.parser')
        
#         return SEOAnalysisResult(
#             url=page_url,
#             analysis_timestamp=datetime.now().isoformat(),
#             title=self._analyze_title(soup),
#             headers=self._analyze_headers(soup),
#             meta_tags=self._analyze_meta_tags(soup),
#             canonical=self._analyze_canonical(soup, page_url),
#             links=self._analyze_links(soup, page_url),
#             images=self._analyze_images(soup),
#             technical=self._analyze_technical_factors(soup, page_url),
#             open_graph=self._analyze_open_graph(soup),
#             structured_content=self._analyze_structured_content(soup),
#             schema=self._analyze_schema(soup)
#         )
    
#     def analyze_multiple_pages(self, pages_data: List[Dict[str, str]]) -> List[SEOAnalysisResult]:
#         """
#         Analyze multiple HTML pages
        
#         Args:
#             pages_data: List of dicts with 'url' and 'content' keys
            
#         Returns:
#             List of SEOAnalysisResult objects
#         """
#         results = []
        
#         for page in pages_data:
#             if 'url' in page and 'content' in page:
#                 try:
#                     result = self.analyze_page(page['content'], page['url'])
#                     results.append(result)
#                 except Exception as e:
#                     print(f"Error analyzing {page.get('url', 'unknown')}: {str(e)}")
        
#         return results
    
#     def generate_summary_report(self, results: List[SEOAnalysisResult]) -> SummaryReport:
#         """
#         Generate a summary report from multiple analysis results
        
#         Args:
#             results: List of SEOAnalysisResult objects
            
#         Returns:
#             SummaryReport object with aggregated metrics
#         """
#         total_pages = len(results)
        
#         if total_pages == 0:
#             return SummaryReport(
#                 total_pages_analyzed=0,
#                 analysis_timestamp=datetime.now().isoformat(),
#                 pages_with_title_percentage=0,
#                 pages_with_meta_description_percentage=0,
#                 pages_with_h1_percentage=0,
#                 pages_with_multiple_h1_percentage=0,
#                 pages_with_proper_hierarchy_percentage=0,
#                 pages_with_canonical_percentage=0,
#                 pages_with_self_referencing_canonical_percentage=0,
#                 pages_mobile_friendly_percentage=0,
#                 pages_using_https_percentage=0,
#                 pages_with_html_lang_percentage=0,
#                 pages_with_og_tags_percentage=0,
#                 pages_with_schema_percentage=0,
#                 pages_with_noindex_percentage=0,
#                 avg_title_length_words=0,
#                 avg_meta_description_length_words=0,
#                 avg_h1_count=0,
#                 avg_h2_count=0,
#                 avg_internal_links=0,
#                 avg_external_links=0,
#                 avg_images_per_page=0,
#                 avg_alt_text_coverage=0,
#                 common_issues=[],
#                 pages_in_sitemap_percentage=0.0,
#             )
        
#         # Calculate percentages
#         pages_with_title = sum(1 for r in results if r.title.exists)
#         pages_with_meta_desc = sum(1 for r in results if r.meta_tags.description_exists)
#         pages_with_h1 = sum(1 for r in results if r.headers.h1_count > 0)
#         pages_with_multiple_h1 = sum(1 for r in results if r.headers.h1_count > 1)
#         pages_with_proper_hierarchy = sum(1 for r in results if r.headers.has_proper_hierarchy)
#         pages_with_canonical = sum(1 for r in results if r.canonical.exists)
#         pages_with_self_canonical = sum(1 for r in results if r.canonical.is_self_referencing)
#         pages_mobile_friendly = sum(1 for r in results if r.meta_tags.is_mobile_friendly)
#         pages_using_https = sum(1 for r in results if r.technical.uses_https)
#         pages_with_lang = sum(1 for r in results if r.technical.has_html_lang)
#         pages_with_og = sum(1 for r in results if r.open_graph.has_og_tags)
#         pages_with_schema = sum(1 for r in results if r.schema.has_json_ld or r.schema.has_microdata)
#         pages_with_noindex = sum(1 for r in results if r.meta_tags.has_noindex)
        
#         # Calculate averages
#         avg_title_words = sum(r.title.length_words for r in results) / total_pages
#         avg_desc_words = sum(r.meta_tags.description_length_words for r in results) / total_pages
#         avg_h1 = sum(r.headers.h1_count for r in results) / total_pages
#         avg_h2 = sum(r.headers.h2_count for r in results) / total_pages
#         avg_internal = sum(r.links.internal_links_unique_count for r in results) / total_pages
#         avg_external = sum(r.links.external_links_unique_count for r in results) / total_pages
#         avg_images = sum(r.images.total_images for r in results) / total_pages
#         avg_alt_coverage = sum(r.images.alt_text_coverage_percentage for r in results) / total_pages
        
#         # Identify common issues
#         issues_count = {}
#         for r in results:
#             if not r.title.exists:
#                 issues_count['Missing title tag'] = issues_count.get('Missing title tag', 0) + 1
#             if not r.meta_tags.description_exists:
#                 issues_count['Missing meta description'] = issues_count.get('Missing meta description', 0) + 1
#             if r.headers.h1_count == 0:
#                 issues_count['Missing H1 tag'] = issues_count.get('Missing H1 tag', 0) + 1
#             if r.headers.h1_count > 1:
#                 issues_count['Multiple H1 tags'] = issues_count.get('Multiple H1 tags', 0) + 1
#             if not r.headers.has_proper_hierarchy:
#                 issues_count['Improper heading hierarchy'] = issues_count.get('Improper heading hierarchy', 0) + 1
#             if not r.canonical.exists:
#                 issues_count['Missing canonical tag'] = issues_count.get('Missing canonical tag', 0) + 1
#             if not r.meta_tags.is_mobile_friendly:
#                 issues_count['Not mobile-friendly'] = issues_count.get('Not mobile-friendly', 0) + 1
#             if not r.technical.uses_https:
#                 issues_count['Not using HTTPS'] = issues_count.get('Not using HTTPS', 0) + 1
#             if r.images.images_without_alt > 0:
#                 issues_count['Images without alt text'] = issues_count.get('Images without alt text', 0) + 1
        
#         common_issues = [
#             {'issue': issue, 'pages_affected': count, 'percentage': round(count/total_pages*100, 2)}
#             for issue, count in sorted(issues_count.items(), key=lambda x: x[1], reverse=True)
#         ]
        
#         return SummaryReport(
#             total_pages_analyzed=total_pages,
#             analysis_timestamp=datetime.now().isoformat(),
#             pages_with_title_percentage=round(pages_with_title/total_pages*100, 2),
#             pages_with_meta_description_percentage=round(pages_with_meta_desc/total_pages*100, 2),
#             pages_with_h1_percentage=round(pages_with_h1/total_pages*100, 2),
#             pages_with_multiple_h1_percentage=round(pages_with_multiple_h1/total_pages*100, 2),
#             pages_with_proper_hierarchy_percentage=round(pages_with_proper_hierarchy/total_pages*100, 2),
#             pages_with_canonical_percentage=round(pages_with_canonical/total_pages*100, 2),
#             pages_with_self_referencing_canonical_percentage=round(pages_with_self_canonical/total_pages*100, 2),
#             pages_mobile_friendly_percentage=round(pages_mobile_friendly/total_pages*100, 2),
#             pages_using_https_percentage=round(pages_using_https/total_pages*100, 2),
#             pages_with_html_lang_percentage=round(pages_with_lang/total_pages*100, 2),
#             pages_with_og_tags_percentage=round(pages_with_og/total_pages*100, 2),
#             pages_with_schema_percentage=round(pages_with_schema/total_pages*100, 2),
#             pages_with_noindex_percentage=round(pages_with_noindex/total_pages*100, 2),
#             avg_title_length_words=round(avg_title_words, 2),
#             avg_meta_description_length_words=round(avg_desc_words, 2),
#             avg_h1_count=round(avg_h1, 2),
#             avg_h2_count=round(avg_h2, 2),
#             avg_internal_links=round(avg_internal, 2),
#             avg_external_links=round(avg_external, 2),
#             avg_images_per_page=round(avg_images, 2),
#             avg_alt_text_coverage=round(avg_alt_coverage, 2),
#             common_issues=common_issues,
#             pages_in_sitemap_percentage=0.0,
#         )
    
#     def save_results(self, results: List[SEOAnalysisResult], filepath: str):
#         """Save analysis results to JSON file"""
#         data = [asdict(r) for r in results]
#         with open(filepath, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)
    
#     def save_report(self, report: SummaryReport, filepath: str):
#         """Save summary report to JSON file"""
#         with open(filepath, 'w', encoding='utf-8') as f:
#             json.dump(asdict(report), f, indent=2, ensure_ascii=False)


class ScrapySEOAnalyzer:
    """
    Scrapy-native per-page technical SEO analyzer.

    Design goals:
    - Use only Scrapy selectors (no duplicate parsing with BeautifulSoup)
    - Extract high-accuracy signals per the PRD (title, headers, meta, canonical,
      links, images, technical checks, OG, structured content, schema)
    - Be resilient to malformed HTML and attribute variations

    Notes and gotchas:
    - Viewport parsing considers both 'initial-scale=1' and 'initial-scale=1.0'
    - Canonical tags may be relative; we normalize for comparisons
    - Link counts include both total and unique; unique sets are domain-aware for external links
    - Empty alt attributes count as present (valid decorative images) and tracked separately
    """

    def __init__(self, link_sample_size: int = 10):
        self.link_sample_size = link_sample_size

    def _count_words(self, text: str) -> int:
        if not text:
            return 0
        words = re.findall(r"\b\w+\b", text)
        return len(words)

    def _analyze_title(self, response: "ScrapyResponse") -> TitleAnalysis:
        """Extract <title> text safely and compute basic lengths."""
        title_text = response.css('title::text').get() or ""
        title_text = title_text.strip()
        if not title_text:
            return TitleAnalysis(False, "", 0, 0)
        return TitleAnalysis(True, title_text, len(title_text), self._count_words(title_text))

    def _analyze_headers(self, response: "ScrapyResponse") -> HeaderStructure:
        """Count headings and validate hierarchy without deep DOM traversal.

        We only check for presence of levels and detect gaps (e.g., H1 -> H3).
        Multiple H1 detection is explicit.
        """
        def texts(sel: str) -> List[str]:
            return [t.strip() for t in response.css(f'{sel}::text').getall() if t and t.strip()]

        h1_texts = texts('h1')
        h2_texts = texts('h2')
        h3_texts = texts('h3')
        h4_count = len(response.css('h4'))
        h5_count = len(response.css('h5'))
        h6_count = len(response.css('h6'))

        h1_count = len(h1_texts)
        h2_count = len(h2_texts)
        h3_count = len(h3_texts)

        hierarchy_issues: List[str] = []
        has_proper_hierarchy = True
        if h1_count == 0:
            hierarchy_issues.append("Missing H1 tag")
            has_proper_hierarchy = False
        elif h1_count > 1:
            hierarchy_issues.append(f"Multiple H1 tags found ({h1_count})")
            has_proper_hierarchy = False

        present = []
        if h1_count > 0: present.append(1)
        if h2_count > 0: present.append(2)
        if h3_count > 0: present.append(3)
        if h4_count > 0: present.append(4)
        if h5_count > 0: present.append(5)
        if h6_count > 0: present.append(6)
        for i in range(1, len(present)):
            if present[i] - present[i-1] > 1:
                hierarchy_issues.append(f"Skipped heading level from H{present[i-1]} to H{present[i]}")
                has_proper_hierarchy = False

        return HeaderStructure(
            h1_count=h1_count,
            h1_texts=h1_texts,
            h2_count=h2_count,
            h2_texts=h2_texts,
            h3_count=h3_count,
            h3_texts=h3_texts,
            h4_count=h4_count,
            h5_count=h5_count,
            h6_count=h6_count,
            has_proper_hierarchy=has_proper_hierarchy,
            hierarchy_issues=hierarchy_issues,
        )

    def _analyze_meta_tags(self, response: "ScrapyResponse") -> MetaTagsAnalysis:
        """Extract meta description, robots, and viewport for mobile-friendly check."""
        desc_text = (response.css('meta[name="description"]::attr(content)').get() or "").strip()
        robots_content = (response.css('meta[name="robots"]::attr(content)').get() or "").lower()
        viewport_content = (response.css('meta[name="viewport"]::attr(content)').get() or "").lower()

        is_mobile_friendly = False
        if viewport_content:
            has_device_width = 'width=device-width' in viewport_content
            # Accept either exactly 1 or 1.0 (and tolerate whitespace)
            has_initial_scale = ('initial-scale=1' in viewport_content) or ('initial-scale=1.0' in viewport_content)
            is_mobile_friendly = has_device_width and has_initial_scale

        return MetaTagsAnalysis(
            description_exists=bool(desc_text),
            description_text=desc_text,
            description_length_chars=len(desc_text),
            description_length_words=self._count_words(desc_text),
            robots_exists=bool(robots_content),
            robots_content=robots_content,
            has_noindex='noindex' in robots_content,
            has_nofollow='nofollow' in robots_content,
            viewport_exists=bool(viewport_content),
            viewport_content=viewport_content,
            is_mobile_friendly=is_mobile_friendly,
        )

    def _analyze_canonical(self, response: "ScrapyResponse") -> CanonicalAnalysis:
        """Validate rel=canonical and compare normalized URL to page URL.

        Handles relative canonical URLs by resolving against the page URL for
        domain and path comparisons.
        """
        canonical_url = (response.css('link[rel="canonical"]::attr(href)').get() or "").strip()
        if not canonical_url:
            return CanonicalAnalysis(False, "", False, False, False, False)

        page_parsed = urlparse(response.url)
        canonical_effective = canonical_url
        # Normalize relative canonical
        if canonical_url and not canonical_url.startswith(('http://', 'https://')):
            try:
                canonical_effective = response.urljoin(canonical_url)  # type: ignore[attr-defined]
            except Exception:
                canonical_effective = canonical_url
        canonical_parsed = urlparse(canonical_effective)
        is_absolute = bool(canonical_parsed.scheme and canonical_parsed.netloc)
        is_same_domain = page_parsed.netloc.lower() == canonical_parsed.netloc.lower() if is_absolute else False
        is_self_referencing = False
        if is_absolute and is_same_domain:
            is_self_referencing = page_parsed.path.rstrip('/') == canonical_parsed.path.rstrip('/')
        uses_https = canonical_parsed.scheme == 'https'

        return CanonicalAnalysis(True, canonical_effective, is_self_referencing, is_absolute, is_same_domain, uses_https)

    def _analyze_links(self, response: "ScrapyResponse") -> LinkAnalysis:
        """Count internal/external links and provide sample sets with percentage metrics.

        We distinguish internal vs external by comparing netloc. Relative links
        are considered internal. We provide both total counts, unique counts, and
        percentage breakdowns (0-100 scale) for standardized scoring.
        """
        page_domain = urlparse(response.url).netloc.lower()
        hrefs = [h.strip() for h in response.css('a::attr(href)').getall() if h and h.strip()]
        internal: Set[str] = set()
        external: Set[str] = set()
        external_domains: Set[str] = set()
        internal_all_count = 0
        external_all_count = 0

        for href in hrefs:
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            if href.startswith(('http://', 'https://')):
                link_domain = urlparse(href).netloc.lower()
                if link_domain == page_domain:
                    internal.add(href)
                    internal_all_count += 1
                else:
                    external.add(href)
                    external_domains.add(link_domain)
                    external_all_count += 1
            else:
                internal.add(href)
                internal_all_count += 1

        internal_sample = sorted(list(internal))[: self.link_sample_size]
        external_sample = sorted(list(external))[: self.link_sample_size]

        # Calculate percentage metrics (0-100 scale) for standardization
        total_valid_links = internal_all_count + external_all_count
        internal_percentage = (internal_all_count / total_valid_links * 100.0) if total_valid_links > 0 else 0.0
        external_percentage = (external_all_count / total_valid_links * 100.0) if total_valid_links > 0 else 0.0
        
        total_unique_links = len(internal) + len(external)
        unique_internal_percentage = (len(internal) / total_unique_links * 100.0) if total_unique_links > 0 else 0.0
        unique_external_percentage = (len(external) / total_unique_links * 100.0) if total_unique_links > 0 else 0.0

        return LinkAnalysis(
            internal_links_count=internal_all_count,
            internal_links_unique_count=len(internal),
            external_links_count=external_all_count,
            external_links_unique_count=len(external),
            external_domains=sorted(list(external_domains)),
            total_links_count=len(hrefs),
            internal_links_percentage=round(internal_percentage, 2),
            external_links_percentage=round(external_percentage, 2),
            unique_internal_percentage=round(unique_internal_percentage, 2),
            unique_external_percentage=round(unique_external_percentage, 2),
            internal_links_sample=internal_sample,
            external_links_sample=external_sample,
        )

    def _analyze_images(self, response: "ScrapyResponse") -> ImageAnalysis:
        """Count images and alt coverage; track sample without-alt sources."""
        imgs = response.css('img')
        total = len(imgs)
        with_alt = 0
        without_alt = 0
        empty_alt = 0
        without_alt_sample: List[str] = []
        for sel in imgs:
            if sel.attrib.get('alt') is not None:
                alt_text = (sel.attrib.get('alt') or '').strip()
                if alt_text:
                    with_alt += 1
                else:
                    empty_alt += 1
                    with_alt += 1
            else:
                without_alt += 1
                src = sel.attrib.get('src', 'unknown')
                if len(without_alt_sample) < 5:
                    without_alt_sample.append(src)
        coverage = (with_alt / total * 100) if total > 0 else 100.0
        return ImageAnalysis(total, with_alt, without_alt, round(coverage, 2), empty_alt, without_alt_sample)

    def _analyze_technical(self, response: "ScrapyResponse") -> TechnicalFactors:
        """Check https scheme, html[lang], and charset meta robustly."""
        uses_https = response.url.startswith('https://')
        lang_value = (response.css('html::attr(lang)').get() or '').strip()
        has_lang = bool(lang_value)
        charset_value = (response.css('meta[charset]::attr(charset)').get() or '').strip()
        if not charset_value:
            content = response.css('meta[http-equiv="Content-Type"]::attr(content)').get() or ''
            if 'charset=' in content:
                charset_value = content.split('charset=')[-1].strip()
        has_charset = bool(charset_value)
        return TechnicalFactors(uses_https, has_lang, lang_value, has_charset, charset_value)

    def _analyze_open_graph(self, response: "ScrapyResponse") -> OpenGraphAnalysis:
        """Detect presence of Open Graph tags and key fields."""
        og_tags = response.css('meta[property^="og:"]')
        og_title = bool(response.css('meta[property="og:title"]'))
        og_desc = bool(response.css('meta[property="og:description"]'))
        og_image = bool(response.css('meta[property="og:image"]'))
        og_url = bool(response.css('meta[property="og:url"]'))
        og_type_value = (response.css('meta[property="og:type"]::attr(content)').get() or '').strip()
        return OpenGraphAnalysis(bool(og_tags), len(og_tags), og_title, og_desc, og_image, og_url, bool(og_type_value), og_type_value)

    def _analyze_structured(self, response: "ScrapyResponse") -> StructuredContent:
        """Count basic structured content blocks that are reliably detected."""
        return StructuredContent(
            ordered_lists_count=len(response.css('ol')),
            unordered_lists_count=len(response.css('ul')),
            code_blocks_count=len(response.css('code')) + len(response.css('pre')),
            tables_count=len(response.css('table')),
            forms_count=len(response.css('form')),
            iframes_count=len(response.css('iframe')),
        )

    def _analyze_schema(self, response: "ScrapyResponse") -> SchemaMarkup:
        """Detect JSON-LD and microdata types conservatively (best-effort)."""
        json_ld_scripts = response.css('script[type="application/ld+json"]::text').getall()
        json_ld_types: List[str] = []
        microdata_types: List[str] = []
        try:
            import json
            for block in json_ld_scripts:
                try:
                    data = json.loads(block)
                except Exception:
                    continue
                if isinstance(data, dict) and '@type' in data:
                    t = data.get('@type')
                    if isinstance(t, list):
                        json_ld_types.extend([str(x) for x in t])
                    else:
                        json_ld_types.append(str(t))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            json_ld_types.append(str(item['@type']))
        except Exception:
            pass
        for el in response.css('[itemtype]'):
            itemtype = el.attrib.get('itemtype', '')
            if 'schema.org' in itemtype:
                schema_type = itemtype.split('/')[-1]
                microdata_types.append(schema_type)
        return SchemaMarkup(bool(json_ld_scripts), len(response.css('[itemtype]')) > 0, list(set(json_ld_types)), list(set(microdata_types)))

    def analyze_response(self, response: "ScrapyResponse") -> SEOAnalysisResult:
        """Analyze a Scrapy Response and return the aggregated result dataclass."""
        result = SEOAnalysisResult(
            url=response.url,
            analysis_timestamp=datetime.now().isoformat(),
            title=self._analyze_title(response),
            headers=self._analyze_headers(response),
            meta_tags=self._analyze_meta_tags(response),
            canonical=self._analyze_canonical(response),
            links=self._analyze_links(response),
            images=self._analyze_images(response),
            technical=self._analyze_technical(response),
            open_graph=self._analyze_open_graph(response),
            structured_content=self._analyze_structured(response),
            schema=self._analyze_schema(response),
        )
        try:
            # Integrate schema types analysis directly through class methods for clarity
            jsonld = self._collect_json_ld_types(response)
            micro = self._collect_microdata_types(response)
            has_rdfa, rdfa = self._collect_rdfa_types(response)
            by_source: Dict[str, Dict[str, int]] = {'json_ld': {}, 'microdata': {}, 'rdfa': {}}
            for t in jsonld:
                by_source['json_ld'][t] = by_source['json_ld'].get(t, 0) + 1
            for t in micro:
                by_source['microdata'][t] = by_source['microdata'].get(t, 0) + 1
            for t in rdfa:
                by_source['rdfa'][t] = by_source['rdfa'].get(t, 0) + 1
            aggregate: Dict[str, int] = {}
            for src in by_source.values():
                for t, c in src.items():
                    aggregate[t] = aggregate.get(t, 0) + c
            focus: Dict[str, int] = {t: c for t, c in aggregate.items() if t in FOCUS_SCHEMA_TYPES}
            classifications = self._classify_from_types(aggregate)
            result.schema_types = SchemaTypesAnalysis(
                has_rdfa=has_rdfa,
                detected_types=aggregate,
                detected_types_by_source=by_source,
                matched_focus_types=focus,
                classifications=classifications,
            )
        except Exception:
            result.schema_types = None
        return result
    def _collect_json_ld_types(self, response: "ScrapyResponse") -> List[str]:
        """Robustly collect @type values from JSON-LD blocks, including @graph and nested objects."""
        def walk(obj: Any, out: List[str]) -> None:
            if isinstance(obj, dict):
                t = obj.get('@type')
                if isinstance(t, str):
                    out.append(t)
                elif isinstance(t, list):
                    out.extend([str(x) for x in t if isinstance(x, (str, int, float))])
                for v in obj.values():
                    walk(v, out)
            elif isinstance(obj, list):
                for it in obj:
                    walk(it, out)

        types: List[str] = []
        for block in response.css('script[type="application/ld+json"]::text').getall():
            try:
                import json
                data = json.loads(block)
                walk(data, types)
            except Exception:
                continue
        norm: List[str] = []
        for t in types:
            ts = str(t).rsplit('/', 1)[-1]
            if ts:
                norm.append(ts)
        return norm

    def _collect_microdata_types(self, response: "ScrapyResponse") -> List[str]:
        types: List[str] = []
        for el in response.css('[itemtype]'):
            val = el.attrib.get('itemtype', '')
            for token in val.split():
                ts = token.rsplit('/', 1)[-1]
                if ts:
                    types.append(ts)
        return types

    def _collect_rdfa_types(self, response: "ScrapyResponse") -> Tuple[bool, List[str]]:
        """Collect RDFa types using typeof and optional vocab/prefix context."""
        has_vocab = bool(response.css('[vocab*="schema.org"], [prefix*="schema.org"]'))
        rdfa_types: List[str] = []
        for el in response.css('[typeof]'):
            tokens = (el.attrib.get('typeof') or '').split()
            for tok in tokens:
                tname = ''
                if ':' in tok:
                    tname = tok.split(':', 1)[1]
                elif has_vocab:
                    tname = tok
                if tname:
                    rdfa_types.append(tname)
        return bool(rdfa_types), rdfa_types

    def _classify_from_types(self, type_counts: Dict[str, int]) -> Dict[str, bool]:
        tset = set(k for k, v in type_counts.items() if v > 0)
        return {
            'blog_like': any(t in tset for t in {'BlogPosting', 'Article', 'TechArticle'}),
            'faq_like': ('FAQPage' in tset) or (('Question' in tset) and ('Answer' in tset)),
            'product_like': any(t in tset for t in {'Product', 'Offer', 'AggregateRating', 'PriceSpecification'}),
            'software_like': any(t in tset for t in {'SoftwareApplication', 'WebApplication', 'APIReference', 'SoftwareSourceCode'}),
            'organization_like': any(t in tset for t in {'Organization', 'Corporation'}),
            'event_like': any(t.endswith('Event') for t in tset) or ('Event' in tset),
            'course_like': any(t in tset for t in {'Course', 'LearningResource'}),
            'has_breadcrumbs': 'BreadcrumbList' in tset,
            'has_site_search': 'SearchAction' in tset,
        }


# Focus schema types to examine explicitly (extendable)
FOCUS_SCHEMA_TYPES: Set[str] = {
    "SoftwareApplication","WebApplication","Organization","Corporation","TechArticle",
    "HowTo","FAQPage","Question","Answer","Service","Product","Offer","PriceSpecification",
    "ContactPoint","PostalAddress","Person","EmployeeRole","Review","AggregateRating","VideoObject",
    "ImageObject","WebSite","WebPage","SearchAction","BreadcrumbList","SiteNavigationElement","Article",
    "BlogPosting","Course","LearningResource","Dataset","APIReference","SoftwareSourceCode","CreativeWork",
    "Brand","Event","WebinarEvent","BusinessEvent","EducationalEvent","JobPosting","Occupation",
    "MonetaryAmount","QuantitativeValue","PropertyValue","Rating","MediaObject","DigitalDocument",
    "TextDigitalDocument","PresentationDigitalDocument","SpreadsheetDigitalDocument","Place","VirtualLocation",
    "OnlineBusiness","ProfessionalService"
}


@dataclass
class SchemaTypesAnalysis:
    """Detailed schema.org types analysis across JSON-LD, microdata, and RDFa.

    - detected_types: aggregate counts of each type across all sources
    - detected_types_by_source: separate counts for 'json_ld', 'microdata', 'rdfa'
    - has_rdfa: whether RDFa types were detected (vocab or typeof patterns)
    - matched_focus_types: subset counts of FOCUS_SCHEMA_TYPES
    - classifications: heuristic booleans indicating page intent
    """
    has_rdfa: bool
    detected_types: Dict[str, int]
    detected_types_by_source: Dict[str, Dict[str, int]]
    matched_focus_types: Dict[str, int]
    classifications: Dict[str, bool]

    @property
    def has_any_schema(self) -> bool:
        return bool(self.detected_types)


@dataclass
class SchemaTypesSummary:
    """Aggregated schema types metrics across multiple pages."""
    total_pages_analyzed: int
    analysis_timestamp: str
    pages_with_any_schema_percentage: float
    pages_with_json_ld_percentage: float
    pages_with_microdata_percentage: float
    pages_with_rdfa_percentage: float
    # Top detected types across pages (sorted by pages containing type)
    top_detected_types: List[Dict[str, Any]]
    # Presence of focus types across pages
    focus_type_presence: List[Dict[str, Any]]
    # Classification percentages per page intent (e.g., blog_like)
    classification_percentages: Dict[str, float]


## Note: Removed duplicate module-level helpers for schema type collection and
## classification in favor of the ScrapySEOAnalyzer instance methods.


async def compute_schema_types_summary(documents: List[Dict[str, Any]], top_n: int = 10) -> 'SchemaTypesSummary':
    """Aggregate schema types across documents into SchemaTypesSummary."""
    total = 0
    pages_with_any = 0
    pages_jsonld = 0
    pages_micro = 0
    pages_rdfa = 0
    type_pages: Dict[str, int] = {}
    focus_pages: Dict[str, int] = {t: 0 for t in FOCUS_SCHEMA_TYPES}
    classification_counts: Dict[str, int] = {}

    for doc in documents:
        seo = doc.get('technical_seo') if isinstance(doc, dict) else None
        if not seo:
            continue
        st = seo.get('schema_types') or {}
        if not st:
            continue
        total += 1
        types = st.get('detected_types') or {}
        by_src = st.get('detected_types_by_source') or {}
        classifications = st.get('classifications') or {}

        if types:
            pages_with_any += 1
        if (by_src.get('json_ld') or {}):
            pages_jsonld += 1
        if (by_src.get('microdata') or {}):
            pages_micro += 1
        if (by_src.get('rdfa') or {}):
            pages_rdfa += 1

        for t in set(types.keys()):
            type_pages[t] = type_pages.get(t, 0) + 1

        for ft in FOCUS_SCHEMA_TYPES:
            if ft in types:
                focus_pages[ft] += 1

        for k, v in classifications.items():
            if v:
                classification_counts[k] = classification_counts.get(k, 0) + 1

    if total == 0:
        return SchemaTypesSummary(
            total_pages_analyzed=0,
            analysis_timestamp=datetime.now().isoformat(),
            pages_with_any_schema_percentage=0,
            pages_with_json_ld_percentage=0,
            pages_with_microdata_percentage=0,
            pages_with_rdfa_percentage=0,
            top_detected_types=[],
            focus_type_presence=[],
            classification_percentages={},
        )

    denom = float(total)
    top_types_sorted = sorted(type_pages.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_detected_types = [
        {'type': t, 'pages': c, 'percentage': round(c/denom*100, 2)} for t, c in top_types_sorted
    ]
    focus_presence = [
        {'type': t, 'pages': focus_pages[t], 'percentage': round(focus_pages[t]/denom*100, 2)}
        for t in sorted(FOCUS_SCHEMA_TYPES)
        if focus_pages[t] > 0
    ]
    classification_percentages = {k: round(v/denom*100, 2) for k, v in classification_counts.items()}

    return SchemaTypesSummary(
        total_pages_analyzed=total,
        analysis_timestamp=datetime.now().isoformat(),
        pages_with_any_schema_percentage=round(pages_with_any/denom*100, 2),
        pages_with_json_ld_percentage=round(pages_jsonld/denom*100, 2),
        pages_with_microdata_percentage=round(pages_micro/denom*100, 2),
        pages_with_rdfa_percentage=round(pages_rdfa/denom*100, 2),
        top_detected_types=top_detected_types,
        focus_type_presence=focus_presence,
        classification_percentages=classification_percentages,
    )


async def compute_summary_from_documents(documents: List[Dict[str, Any]]) -> SummaryReport:
    """
    Aggregate a SummaryReport from scraped documents containing 'technical_seo'.

    This mirrors the fields of SummaryReport for uniform downstream handling.
    It scans documents for a 'technical_seo' mapping with the same shape
    produced by ScrapySEOAnalyzer. If no such documents are found, returns a
    SummaryReport with zeros.
    """
    total = 0
    # Percentage accumulators
    pages_with_title = 0
    pages_with_meta_desc = 0
    pages_with_h1 = 0
    pages_with_multiple_h1 = 0
    pages_with_proper_hierarchy = 0
    pages_with_canonical = 0
    pages_with_self_canonical = 0
    pages_mobile_friendly = 0
    pages_using_https = 0
    pages_with_lang = 0
    pages_with_og = 0
    pages_with_schema = 0
    pages_with_noindex = 0
    pages_in_sitemap = 0

    # Averages accumulators
    sum_title_words = 0.0
    sum_desc_words = 0.0
    sum_h1 = 0.0
    sum_h2 = 0.0
    sum_internal = 0.0
    sum_external = 0.0
    sum_images = 0.0
    sum_alt_coverage = 0.0
    # Link percentage accumulators (0-100 scale)
    sum_internal_percentage = 0.0
    sum_external_percentage = 0.0

    for doc in documents:
        seo = doc.get('technical_seo') if isinstance(doc, dict) else None
        if not seo:
            continue
        total += 1

        title = seo.get('title') or {}
        headers = seo.get('headers') or {}
        meta_tags = seo.get('meta_tags') or {}
        canonical = seo.get('canonical') or {}
        links = seo.get('links') or {}
        images = seo.get('images') or {}
        technical = seo.get('technical') or {}
        open_graph = seo.get('open_graph') or {}
        schema = seo.get('schema') or {}

        if title.get('exists'): pages_with_title += 1
        if meta_tags.get('description_exists'): pages_with_meta_desc += 1
        if (headers.get('h1_count') or 0) > 0: pages_with_h1 += 1
        if (headers.get('h1_count') or 0) > 1: pages_with_multiple_h1 += 1
        if headers.get('has_proper_hierarchy'): pages_with_proper_hierarchy += 1
        if canonical.get('exists'): pages_with_canonical += 1
        if canonical.get('is_self_referencing'): pages_with_self_canonical += 1
        if meta_tags.get('is_mobile_friendly'): pages_mobile_friendly += 1
        if technical.get('uses_https'): pages_using_https += 1
        if technical.get('has_html_lang'): pages_with_lang += 1
        if open_graph.get('has_og_tags'): pages_with_og += 1
        if schema.get('has_json_ld') or schema.get('has_microdata'): pages_with_schema += 1
        if meta_tags.get('has_noindex'): pages_with_noindex += 1
        if doc.get('is_url_in_sitemap'):
            pages_in_sitemap += 1

        sum_title_words += float(title.get('length_words') or 0)
        sum_desc_words += float(meta_tags.get('description_length_words') or 0)
        sum_h1 += float(headers.get('h1_count') or 0)
        sum_h2 += float(headers.get('h2_count') or 0)
        sum_internal += float(links.get('internal_links_unique_count') or 0)
        sum_external += float(links.get('external_links_unique_count') or 0)
        sum_images += float(images.get('total_images') or 0)
        sum_alt_coverage += float(images.get('alt_text_coverage_percentage') or 0)
        # Accumulate percentage metrics (already 0-100 scale)
        sum_internal_percentage += float(links.get('internal_links_percentage') or 0)
        sum_external_percentage += float(links.get('external_links_percentage') or 0)

    if total == 0:
        return SummaryReport(
            total_pages_analyzed=0,
            analysis_timestamp=datetime.now().isoformat(),
            pages_with_title_percentage=0,
            pages_with_meta_description_percentage=0,
            pages_with_h1_percentage=0,
            pages_with_multiple_h1_percentage=0,
            pages_with_proper_hierarchy_percentage=0,
            pages_with_canonical_percentage=0,
            pages_with_self_referencing_canonical_percentage=0,
            pages_mobile_friendly_percentage=0,
            pages_using_https_percentage=0,
            pages_with_html_lang_percentage=0,
            pages_with_og_tags_percentage=0,
            pages_with_schema_percentage=0,
            pages_with_noindex_percentage=0,
            avg_title_length_words=0,
            avg_meta_description_length_words=0,
            avg_h1_count=0,
            avg_h2_count=0,
            avg_internal_links=0,
            avg_external_links=0,
            avg_images_per_page=0,
            avg_alt_text_coverage=0,
            avg_internal_links_percentage=0,
            avg_external_links_percentage=0,
            common_issues=[],
            pages_in_sitemap_percentage=0.0,
        )

    denom = float(total)

    # Common issues similar to analyzer's generate_summary_report
    issues_count: Dict[str, int] = {}
    def add_issue(name: str):
        issues_count[name] = issues_count.get(name, 0) + 1

    # Second pass for issues
    for doc in documents:
        seo = doc.get('technical_seo') if isinstance(doc, dict) else None
        if not seo:
            continue
        title = seo.get('title') or {}
        headers = seo.get('headers') or {}
        meta_tags = seo.get('meta_tags') or {}
        canonical = seo.get('canonical') or {}
        images = seo.get('images') or {}
        technical = seo.get('technical') or {}

        if not title.get('exists'):
            add_issue('Missing title tag')
        if not meta_tags.get('description_exists'):
            add_issue('Missing meta description')
        if (headers.get('h1_count') or 0) == 0:
            add_issue('Missing H1 tag')
        if (headers.get('h1_count') or 0) > 1:
            add_issue('Multiple H1 tags')
        if not headers.get('has_proper_hierarchy'):
            add_issue('Improper heading hierarchy')
        if not canonical.get('exists'):
            add_issue('Missing canonical tag')
        if not meta_tags.get('is_mobile_friendly'):
            add_issue('Not mobile-friendly')
        if not technical.get('uses_https'):
            add_issue('Not using HTTPS')
        if (images.get('images_without_alt') or 0) > 0:
            add_issue('Images without alt text')

    common_issues = [
        {'issue': issue, 'pages_affected': count, 'percentage': round(count/denom*100, 2)}
        for issue, count in sorted(issues_count.items(), key=lambda x: x[1], reverse=True)
    ]

    # Also include schema types summary if present
    schema_types_summary = await compute_schema_types_summary(documents)

    return SummaryReport(
        total_pages_analyzed=total,
        analysis_timestamp=datetime.now().isoformat(),
        pages_with_title_percentage=round(pages_with_title/denom*100, 2),
        pages_with_meta_description_percentage=round(pages_with_meta_desc/denom*100, 2),
        pages_with_h1_percentage=round(pages_with_h1/denom*100, 2),
        pages_with_multiple_h1_percentage=round(pages_with_multiple_h1/denom*100, 2),
        pages_with_proper_hierarchy_percentage=round(pages_with_proper_hierarchy/denom*100, 2),
        pages_with_canonical_percentage=round(pages_with_canonical/denom*100, 2),
        pages_with_self_referencing_canonical_percentage=round(pages_with_self_canonical/denom*100, 2),
        pages_mobile_friendly_percentage=round(pages_mobile_friendly/denom*100, 2),
        pages_using_https_percentage=round(pages_using_https/denom*100, 2),
        pages_with_html_lang_percentage=round(pages_with_lang/denom*100, 2),
        pages_with_og_tags_percentage=round(pages_with_og/denom*100, 2),
        pages_with_schema_percentage=round(pages_with_schema/denom*100, 2),
        pages_with_noindex_percentage=round(pages_with_noindex/denom*100, 2),
        avg_title_length_words=round(sum_title_words/denom, 2),
        avg_meta_description_length_words=round(sum_desc_words/denom, 2),
        avg_h1_count=round(sum_h1/denom, 2),
        avg_h2_count=round(sum_h2/denom, 2),
        avg_internal_links=round(sum_internal/denom, 2),
        avg_external_links=round(sum_external/denom, 2),
        avg_images_per_page=round(sum_images/denom, 2),
        avg_alt_text_coverage=round(sum_alt_coverage/denom, 2),
        avg_internal_links_percentage=round(sum_internal_percentage/denom, 2),
        avg_external_links_percentage=round(sum_external_percentage/denom, 2),
        common_issues=common_issues,
        schema_types_summary=schema_types_summary,
        pages_in_sitemap_percentage=round(pages_in_sitemap/denom*100, 2),
    )



# CLI interface
if __name__ == "__main__":
    import sys
    
    def print_usage():
        print("""
High Accuracy SEO Analysis Script

Usage:
  python high_accuracy_seo_analyzer.py <input_file> [output_file] [report_file]

Arguments:
  input_file   : JSON file containing pages data (array of {url, content} objects)
  output_file  : (Optional) Path to save individual analysis results
  report_file  : (Optional) Path to save summary report

Example:
  python high_accuracy_seo_analyzer.py pages.json results.json report.json
        """)
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    report_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Load input data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            pages_data = json.load(f)
    except Exception as e:
        print(f"Error loading input file: {e}")
        sys.exit(1)
    
    # Ensure it's a list
    if not isinstance(pages_data, list):
        pages_data = [pages_data]
    
    # Run analysis
    print(f"Analyzing {len(pages_data)} pages...")
    analyzer = SEOAnalyzer()
    results = analyzer.analyze_multiple_pages(pages_data)
    print(f"Successfully analyzed {len(results)} pages")
    
    # Generate report
    report = analyzer.generate_summary_report(results)
    
    # Save results if output file specified
    if output_file:
        analyzer.save_results(results, output_file)
        print(f"Individual results saved to: {output_file}")
    
    # Save report if report file specified
    if report_file:
        analyzer.save_report(report, report_file)
        print(f"Summary report saved to: {report_file}")
    
    # Print summary
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    print(f"Total pages analyzed: {report.total_pages_analyzed}")
    print(f"\nKey Metrics:")
    print(f"  • Pages with title tag: {report.pages_with_title_percentage}%")
    print(f"  • Pages with meta description: {report.pages_with_meta_description_percentage}%")
    print(f"  • Pages with proper H1: {report.pages_with_h1_percentage}%")
    print(f"  • Mobile-friendly pages: {report.pages_mobile_friendly_percentage}%")
    print(f"  • Pages using HTTPS: {report.pages_using_https_percentage}%")
    print(f"  • Average alt text coverage: {report.avg_alt_text_coverage}%")
    
    if report.common_issues:
        print(f"\nTop Issues Found:")
        for issue in report.common_issues[:5]:
            print(f"  • {issue['issue']}: {issue['pages_affected']} pages ({issue['percentage']}%)")
