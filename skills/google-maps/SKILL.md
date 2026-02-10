# Google Maps Skill

Extract and display information from Google Maps URLs and search for places.

## Usage

### When a user shares a Google Maps link:

The skill automatically extracts and displays:
- Place name
- Rating
- Address
- Phone number
- Hours of operation
- Open/closed status
- Directions link

### Direct Commands

#### Search for places
```
Search for <query> on Google Maps
Find <place type> near <location>
Google Maps search: <query>
```

#### Get place details
```
What's at this Google Maps link?
Extract info from: <URL>
Get details for <URL>
```

#### Check hours
```
What are the hours for <place>?
Get hours for <URL>
Is <place> open now?
```

#### Check open status
```
Is <place> open?
Check if <URL> is open
Is this place currently open?
```

#### Get phone number
```
What's the phone number for <place>?
Get phone for <URL>
Contact info for <place>
```

#### Get directions
```
How do I get to <place>?
Get directions to <URL>
Directions to <place>
```

## Functions

### `extractFromUrl(url)`
Extract all available information from a Google Maps URL.

**Parameters:**
- `url` (string): Google Maps URL

**Returns:**
```json
{
  "name": "Place Name",
  "rating": 4.5,
  "address": "123 Main St, City, State",
  "phone": "+1 (555) 123-4567",
  "hours": "9:00 AM - 9:00 PM",
  "isOpen": true,
  "directions": "https://maps.google.com/..."
}
```

### `searchPlaces(query)`
Search for places on Google Maps.

**Parameters:**
- `query` (string): Search query

**Returns:**
```json
{
  "query": "coffee shops",
  "results": [
    {
      "name": "Coffee Shop 1",
      "rating": 4.5,
      "address": "123 St"
    }
  ],
  "searchUrl": "https://maps.google.com/..."
}
```

### `getHours(url)`
Get hours of operation for a place.

**Parameters:**
- `url` (string): Google Maps URL

**Returns:**
```json
{
  "name": "Place Name",
  "hours": "9:00 AM - 9:00 PM",
  "url": "https://maps.google.com/..."
}
```

### `checkOpenStatus(url)`
Check if a place is currently open.

**Parameters:**
- `url` (string): Google Maps URL

**Returns:**
```json
{
  "name": "Place Name",
  "isOpen": true,
  "hours": "9:00 AM - 9:00 PM"
}
```

### `getPhone(url)`
Get phone number for a place.

**Parameters:**
- `url` (string): Google Maps URL

**Returns:**
```json
{
  "name": "Place Name",
  "phone": "+1 (555) 123-4567"
}
```

### `getDirections(url)`
Get directions to a place.

**Parameters:**
- `url` (string): Google Maps URL

**Returns:**
```json
{
  "name": "Place Name",
  "address": "123 Main St",
  "directionsUrl": "https://maps.google.com/dir/..."
}
```

### `getPlaceDetails(url)`
Get complete place details.

**Parameters:**
- `url` (string): Google Maps URL

**Returns:**
Complete information object with all available details.

## Examples

### Example 1: User shares a Google Maps link
**User:** "Check out this restaurant: https://maps.google.com/..."

**Bot Response:**
```
📍 **Restaurant Name**
⭐ 4.5/5 rating
📍 123 Main Street, City
📞 (555) 123-4567
🕐 11:00 AM - 10:00 PM
✅ Currently Open
🧭 [Get Directions](https://maps.google.com/...)
```

### Example 2: Search for places
**User:** "Find coffee shops near downtown"

**Bot Response:**
```
☕ **Coffee Shops Near Downtown**

1. **Downtown Coffee Co.** ⭐ 4.8
   456 Main St

2. **Espresso Bar** ⭐ 4.5
   789 Oak Ave

[View on Google Maps](https://maps.google.com/search/coffee+shops+downtown)
```

### Example 3: Check if open
**User:** "Is that pizza place open right now?"

**Bot Response:**
```
✅ **Tony's Pizza** is currently open
🕐 11:00 AM - 11:00 PM
```

## URL Formats Supported

- `https://maps.google.com/...`
- `https://www.google.com/maps/place/...`
- Google Maps share links

## Notes

- The skill uses web_fetch to extract information from Google Maps pages
- Some information may not be available for all places
- Opening hours may vary by day
- Ratings are user-submitted and may not be current
