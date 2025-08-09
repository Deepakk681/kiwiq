"""
Technical SEO utilities: Scrapy analyzer and date parser.

This package provides:
- ScrapySEOAnalyzer: per-page high-accuracy technical SEO extraction
- PageDateParser: robust published/updated date extraction from HTML

The Scrapy analyzer is preferred over BeautifulSoup to avoid duplicate parsing.
"""

from .technical_seo import (
    TitleAnalysis,
    HeaderStructure,
    MetaTagsAnalysis,
    CanonicalAnalysis,
    LinkAnalysis,
    ImageAnalysis,
    TechnicalFactors,
    OpenGraphAnalysis,
    StructuredContent,
    SchemaMarkup,
    SEOAnalysisResult,
    SummaryReport,
    compute_summary_from_documents,
    ScrapySEOAnalyzer,
)

from .date_parser import PageDateParser  # type: ignore

__all__ = [
    "TitleAnalysis",
    "HeaderStructure",
    "MetaTagsAnalysis",
    "CanonicalAnalysis",
    "LinkAnalysis",
    "ImageAnalysis",
    "TechnicalFactors",
    "OpenGraphAnalysis",
    "StructuredContent",
    "SchemaMarkup",
    "SEOAnalysisResult",
    "SummaryReport",
    "ScrapySEOAnalyzer",
    "PageDateParser",
    "compute_summary_from_documents",
]


