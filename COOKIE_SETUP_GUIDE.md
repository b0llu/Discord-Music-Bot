# YouTube Cookie Setup Guide for Render

Based on the [official yt-dlp FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)

## 🚨 The Problem

```
ERROR: [youtube] Sign in to confirm you're not a bot
```

YouTube is blocking your bot because it detects automated requests from cloud servers.

## ✅ Solution: Pass Cookies to yt-dlp

The bot now supports **automatic cookie handling** via environment variables!

---

## 📋 Step-by-Step Setup for Render

### Method 1: Use Browser Extension (Recommended)

#### Step 1: Export Cookies from Browser

1. **Install a cookie export extension:**
   - **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Visit YouTube.com while logged in**
   - Make sure you're signed into your Google/YouTube account
   - Navigate to YouTube.com

3. **Export cookies:**
   - Click the extension icon in your browser
   - Click "Export" or "Download"
   - Save the file as `cookies.txt`

#### Step 2: Convert to Base64

**On Mac/Linux:**
```bash
base64 -i cookies.txt | tr -d '\n' > cookies_base64.txt
```

Then view the content:
```bash
cat cookies_base64.txt
```

**On Windows (PowerShell):**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("cookies.txt")) | Out-File -NoNewline cookies_base64.txt
Get-Content cookies_base64.txt
```

Copy the entire base64 string (it will be very long, that's normal).

#### Step 3: Add to Render Environment Variable

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Select your Discord bot service
3. Click **Environment** tab (left sidebar)
4. Click **Add Environment Variable**
5. Add:
   - **Key:** `YOUTUBE_COOKIES_BASE64`
   - **Value:** (paste the entire base64 string)
6. Click **Save Changes**

Render will automatically redeploy your bot!

---

## 🔄 How It Works

The bot now automatically:

1. ✅ Checks if `cookies.txt` exists in the project
2. ✅ If not, checks for `YOUTUBE_COOKIES_BASE64` environment variable
3. ✅ Decodes the base64 and creates `cookies.txt` automatically
4. ✅ Passes cookies to yt-dlp for all YouTube requests
5. ✅ Prints status messages to logs

---

## 📊 Verify It's Working

### Check Render Logs:

After deployment, check your logs. You should see:

**Success:**
```
Using cookies from YOUTUBE_COOKIES_BASE64 environment variable
Logged in as YourBotName
Slash commands synced!
```

**Warning (if no cookies):**
```
No cookies configured - YouTube may block requests
To fix: Set YOUTUBE_COOKIES_BASE64 environment variable or provide cookies.txt
```

### Test the Bot:

In Discord:
```
/play never gonna give you up
```

If it works, you're all set! 🎉

---

## 🔧 Troubleshooting

### Still Getting "Sign in to confirm you're not a bot"?

**1. Verify cookies are fresh:**
   - Export cookies again from YouTube (make sure you're logged in)
   - Cookies can expire, so use a fresh browser session

**2. Check environment variable:**
   - In Render → Environment tab
   - Make sure `YOUTUBE_COOKIES_BASE64` exists
   - Check it contains a long base64 string (no line breaks!)

**3. Check logs:**
   - Render → Logs tab
   - Look for "Using cookies from..." message
   - If you see "No cookies configured", the environment variable isn't set correctly

**4. Try a different browser:**
   - Export cookies from Firefox (works best according to yt-dlp FAQ)
   - Some users report issues with Edge/Chrome

### "Invalid cookie format" error?

Make sure you're exporting cookies in **Netscape format** (the standard format). The browser extensions mentioned above do this automatically.

### Cookies work locally but not on Render?

- Make sure you converted to base64 properly (no line breaks!)
- Verify the environment variable value in Render is correct
- Try deploying again after updating the environment variable

### "yt-dlp version too old"?

Update requirements.txt:
```
yt-dlp>=2024.11.18
```

Then redeploy.

---

## 🔒 Security Notes

### ⚠️ Important:

- **Never commit `cookies.txt` to Git!** (Already in .gitignore)
- **Never share your cookies** - they give full access to your YouTube account
- **Use environment variables on Render** - this is secure
- **Cookies expire** - you'll need to refresh them periodically (every few weeks)

### Cookie Expiration:

YouTube cookies typically last **2-4 weeks**. When they expire:

1. Export cookies again from your browser
2. Convert to base64
3. Update `YOUTUBE_COOKIES_BASE64` in Render
4. Render will auto-redeploy

---

## 🎯 Quick Reference

### Environment Variables for Render:

```bash
DISCORD_TOKEN=your_discord_bot_token
YOUTUBE_COOKIES_BASE64=your_base64_encoded_cookies
```

### Render Start Command:

```bash
python bot.py
```

That's it! The bot handles cookie decoding automatically.

---

## 🌐 Alternative: Using cookies.txt File Directly (Local Testing)

If you want to test locally:

1. Place `cookies.txt` in your project root
2. Run: `python bot.py`
3. The bot will automatically detect and use it

**Note:** This won't work on Render because files don't persist. Always use the environment variable method for Render.

---

## 📚 Additional Resources

- [yt-dlp FAQ on Cookies](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)
- [yt-dlp Extractors Guide](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)
- [Render Environment Variables Docs](https://render.com/docs/environment-variables)

---

## 💡 Pro Tips

1. **Export cookies every 2 weeks** as a routine maintenance task
2. **Keep your browser updated** - YouTube detection improves with newer browser versions
3. **Use Firefox** - reported to work best with yt-dlp according to the official FAQ
4. **Monitor your Render logs** - they'll tell you if cookies expire

---

## ✅ Summary

1. Export cookies from YouTube using browser extension
2. Convert to base64: `base64 -i cookies.txt | tr -d '\n'`
3. Add to Render as `YOUTUBE_COOKIES_BASE64` environment variable
4. Deploy and test with `/play`

Your bot will now work perfectly with YouTube! 🎵

