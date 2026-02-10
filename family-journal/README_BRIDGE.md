# Discord-to-Family-Journal Bridge Integration

This integration automatically creates journal entries and emails them to the kids when messages/photos/videos are posted in the Discord #family-journal channel.

## Files

- `discord_journal_bridge.py` - Main Python bridge script
- `bridge.sh` - Simple shell wrapper script

## Prerequisites

- Python 3.7+
- Required Python packages (install from family-journal-app/venv):
  - `pyyaml`
  - `requests`
  - `Pillow` (for image processing)

## Configuration

The bridge uses `/root/.openclaw/workspace/family-journal/config.yaml` for settings:
- SMTP email credentials
- Kid profiles (names and email addresses)

**Email Settings:**
```yaml
email:
  sender_email: "landon.gennetten@gmail.com"
  sender_password: "your-app-password"  # App password, not regular password
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
```

**Kid Recipients:**
```yaml
kids:
  - name: "Diana Atlas"
    email: "buddhababediana@gmail.com"
  - name: "Jade Atlas"
    email: "buddhababejade@gmail.com"
  - name: "Julian Atlas"
    email: "buddhababejulian@gmail.com"
```

## Usage

### Option 1: Python Script (Recommended)

```bash
# Auto-detect @mentions and #hashtags from message
python3 discord_journal_bridge.py --message "Hey @Diana check this out!"
python3 discord_journal_bridge.py --message "Hello #Jade and #Julian!"

# Send to all kids with a message
python3 discord_journal_bridge.py --message "Today was amazing!" \
  --attachments "https://cdn.discord.com/attachments/123/photo.jpg"

# Send to specific kids (overrides auto-detection)
python3 discord_journal_bridge.py --message "Hello Diana!" \
  --kids "Diana"

# Multiple attachments
python3 discord_journal_bridge.py --message "Check these out!" \
  --attachments "url1.jpg,url2.png,url3.mp4"

# TEST MODE: Send to Landon first before sending to kids
python3 discord_journal_bridge.py --message "Testing the bridge!" --test-mode
```

### Option 2: Shell Script

```bash
# Auto-detect @mentions and send to those kids
./bridge.sh "Hey @Diana check this out!"
./bridge.sh "Hello #Jade and #Julian!"

# Send to all kids
./bridge.sh "Today was amazing!"

# Send with attachments
./bridge.sh "Check out this photo!" "https://example.com/photo.jpg"

# Send to specific kids
./bridge.sh "Hello Diana!" "" "Diana"

# TEST MODE - Send to Landon for testing
./bridge.sh --test "Testing the bridge!"
```

### Option 3: In OpenClaw Discord Integration

OpenClaw can automatically call the bridge when messages are posted:

```python
# In Discord message handler
if channel_id == "1468850376210612256":  # #family-journal channel
    if message_content or attachments:
        subprocess.run([
            "python3", "discord_journal_bridge.py",
            "--message", message_content,
            "--attachments", ",".join([a.url for a in attachments]),
            "--author", author_name
        ])
```

## Auto-Detection of Recipients

The bridge automatically detects which kids to email based on:

| Format | Example | Notes |
|--------|---------|-------|
| `@Diana` | `@Diana check this out!` | Discord mention format |
| `@Jade` | `Hey @Jade!` | Discord mention format |
| `@Julian` | `@Julian look!` | Discord mention format |
| `#Diana` | `#Diana had fun today` | Hashtag format |
| `#Jade` | `#Jade is awesome` | Hashtag format |
| `#Julian` | `#Julian #Jade` | Multiple hashtags |

**Rules:**
- If `@mentions` or `#hashtags` are found → email only those kids
- If no mentions found → email **all 3 kids** (Diana, Jade, Julian)
- Case-insensitive: `@diana`, `@Diana`, and `@DIANA` all work
- Override with explicit `--kids` parameter

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--message` | `-m` | Discord message text (required) |
| `--attachments` | `-a` | Comma-separated attachment URLs |
| `--kids` | `-k` | Comma-separated kid names (default: auto-detect from @mentions) |
| `--config` | `-c` | Path to config.yaml |
| `--author` | `-n` | Author name for story credit (default: "Discord") |
| `--test-mode` | `-t` | TEST MODE: Send to landon.gennetten@gmail.com first |

## Kid Name Options

| Name | Email |
|------|-------|
| Diana | buddhababediana@gmail.com |
| Jade | buddhababejade@gmail.com |
| Julian | buddhababejulian@gmail.com |

## TEST MODE

Use TEST MODE to test the bridge before sending to kids:

```bash
python3 discord_journal_bridge.py --message "Test message" --test-mode
./bridge.sh --test "Test message"
```

**TEST MODE behavior:**
1. Sends the email to `landon.gennetten@gmail.com` instead of the kids
2. Useful for verifying attachments download correctly
3. Helps check email formatting before the kids receive it
4. Great for debugging issues

## How It Works

1. **Detects Recipients**: Scans message for `@Diana`, `@Jade`, `@Julian` or `#Diana`, `#Jade`, `#Julian`
2. **Downloads Attachments**: Downloads media from Discord URLs to `/root/.openclaw/workspace/family-journal/uploads/`
3. **Compiles Story**: Creates an HTML-formatted story from the message text
4. **Sends Emails**: Uses SMTP to send the story (with attachments) to the selected kids

## Troubleshooting

### "No module named 'email_sender'"
Ensure the family-journal-app directory is accessible at the correct path.

### Email Fails
- Verify SMTP credentials in config.yaml
- Ensure sender email has an app password generated (not regular password)
- Check that the SMTP port (587) is accessible

### Attachment Download Fails
- Verify Discord attachment URLs are still valid
- Ensure the server can access external URLs
- Check file size limits (100MB max per config)

### Wrong Recipients
- Check that you're using `@` or `#` prefixes (not just the name)
- Verify case-insensitive matching is working
- Use explicit `--kids` parameter to override auto-detection

## Example Discord Integration

For OpenClaw to automatically process Discord messages:

1. Configure Discord channel watch for channel ID `1468850376210612256`
2. On new message, extract:
   - `message.content` - the text
   - `message.attachments` - list of attachment URLs
3. Call the bridge script with extracted data
4. The bridge auto-detects @mentions and sends to appropriate kids
