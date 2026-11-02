/**
 * Utilities for cleaning and formatting customer feedback and product catalog text.
 */

export function cleanProductName(name) {
  if (!name) return 'Unknown Product';
  // Scraped Flipkart dataset has runs of '?' where non-ASCII characters or separators were dumped
  let cleaned = name
    .replace(/\?{2,}/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/\s+\(/g, ' (')
    .trim();

  // If corrupted to only symbols, provide clean fallback while preserving original in tooltips
  if (!cleaned || /^[\?\s\-_()]+$/.test(cleaned)) {
    return 'Flipkart Catalog Product';
  }
  return cleaned;
}

export function formatRating(rate) {
  if (rate === null || rate === undefined) return 'N/A';
  const num = parseFloat(rate);
  if (isNaN(num)) return String(rate);
  return Number.isInteger(num) ? `${num}.0` : `${num}`;
}

