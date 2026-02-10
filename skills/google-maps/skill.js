/**
 * Google Maps Skill for OpenClaw
 * Extracts and displays information from Google Maps URLs
 */

const webFetch = require('../tools/web_fetch');

// Parse Google Maps URL to extract place ID
function parseGoogleMapsUrl(url) {
  const placeIdMatch = url.match(/place\/([^/]+)/);
  if (placeIdMatch) {
    return { placeId: placeIdMatch[1] };
  }
  return null;
}

/**
 * Extract information from a Google Maps URL
 * @param {string} url - Google Maps URL
 * @returns {Promise<object>} - Extracted information
 */
async function extractFromUrl(url) {
  if (!url.includes('google.com/maps')) {
    return { error: 'Invalid Google Maps URL' };
  }

  try {
    const content = await web_fetch({ url, extractMode: 'text' });
    
    // Extract relevant information from the page
    const info = {
      url,
      name: extractName(content),
      rating: extractRating(content),
      address: extractAddress(content),
      phone: extractPhone(content),
      hours: extractHours(content),
      isOpen: checkIfOpen(content),
      directions: extractDirectionsUrl(url),
    };

    return info;
  } catch (error) {
    return { error: error.message };
  }
}

function extractName(content) {
  const nameMatch = content.match(/<h1[^>]*>([^<]+)<\/h1>/i);
  return nameMatch ? nameMatch[1].trim() : null;
}

function extractRating(content) {
  const ratingMatch = content.match(/(\d+\.?\d*)\s*★/);
  return ratingMatch ? parseFloat(ratingMatch[1]) : null;
}

function extractAddress(content) {
  const addressMatch = content.search(/<button[^>]*data-value="Address"[^>]*>([^<]+)<\/button>/i) >= 0 
    ? content.match(/<button[^>]*data-value="Address"[^>]*>([^<]+)<\/button>/i)
    : null;
  return addressMatch ? addressMatch[1].trim() : null;
}

function extractPhone(content) {
  const phoneMatch = content.match(/<a[^>]*href="tel:([^"]+)"[^>]*>([^<]+)<\/a>/i);
  return phoneMatch ? phoneMatch[2].trim() : null;
}

function extractHours(content) {
  const hoursSection = content.match(/<span[^>]*aria-label="Hours"[^>]*>([^<]+)<\/span>/i);
  return hoursSection ? hoursSection[1].trim() : null;
}

function checkIfOpen(content) {
  const openMatch = content.match(/Closed|Open now/i);
  if (openMatch) {
    return openMatch[0] === 'Open now';
  }
  return null;
}

function extractDirectionsUrl(url) {
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(url)}`;
}

/**
 * Search for places on Google Maps
 * @param {string} query - Search query
 * @returns {Promise<object>} - Search results
 */
async function searchPlaces(query) {
  const searchUrl = `https://www.google.com/maps/search/${encodeURIComponent(query)}`;
  
  try {
    const content = await web_fetch({ url: searchUrl, extractMode: 'text' });
    
    // Parse search results
    const results = parseSearchResults(content);
    
    return {
      query,
      results,
      searchUrl
    };
  } catch (error) {
    return { error: error.message };
  }
}

function parseSearchResults(content) {
  // Parse Google Maps search results from the page
  const results = [];
  const resultRegex = /<div[^>]*class="[^"]*result[^"]*"[^>]*>([\s\S]*?)<\/div>/gi;
  let match;
  
  while ((match = resultRegex.exec(content)) !== null) {
    const resultHtml = match[1];
    const name = extractName(resultHtml);
    const rating = extractRating(resultHtml);
    const address = extractAddress(resultHtml);
    
    if (name) {
      results.push({ name, rating, address });
    }
  }
  
  return results;
}

/**
 * Get hours for a place
 * @param {string} url - Google Maps URL
 * @returns {Promise<object>} - Hours information
 */
async function getHours(url) {
  const info = await extractFromUrl(url);
  
  if (info.error) {
    return info;
  }
  
  return {
    name: info.name,
    hours: info.hours,
    url
  };
}

/**
 * Check if a place is currently open
 * @param {string} url - Google Maps URL
 * @returns {Promise<object>} - Open status
 */
async function checkOpenStatus(url) {
  const info = await extractFromUrl(url);
  
  if (info.error) {
    return info;
  }
  
  return {
    name: info.name,
    isOpen: info.isOpen,
    hours: info.hours,
    url
  };
}

/**
 * Get phone number for a place
 * @param {string} url - Google Maps URL
 * @returns {Promise<object>} - Phone information
 */
async function getPhone(url) {
  const info = await extractFromUrl(url);
  
  if (info.error) {
    return info;
  }
  
  return {
    name: info.name,
    phone: info.phone,
    url
  };
}

/**
 * Get directions to a place
 * @param {string} url - Google Maps URL
 * @returns {Promise<object>} - Directions link
 */
async function getDirections(url) {
  const info = await extractFromUrl(url);
  
  if (info.error) {
    return info;
  }
  
  return {
    name: info.name,
    address: info.address,
    directionsUrl: extractDirectionsUrl(url),
    url
  };
}

/**
 * Get full place details
 * @param {string} url - Google Maps URL
 * @returns {Promise<object>} - Complete place information
 */
async function getPlaceDetails(url) {
  return extractFromUrl(url);
}

module.exports = {
  name: 'google-maps',
  description: 'Extract and display information from Google Maps URLs',
  extractFromUrl,
  searchPlaces,
  getHours,
  checkOpenStatus,
  getPhone,
  getDirections,
  getPlaceDetails
};
