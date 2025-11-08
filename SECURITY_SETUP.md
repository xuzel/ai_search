# Security Setup Guide

## API Key Management

### ⚠️ CRITICAL: .env File Security

The `.env` file contains sensitive API keys and **MUST NEVER** be committed to git.

### Setup Instructions

1. **Copy the template:**
   ```bash
   cp .env.template .env
   ```

2. **Edit `.env` with your actual API keys:**
   ```bash
   # Use your preferred editor
   nano .env
   # OR
   vim .env
   # OR
   code .env
   ```

3. **Verify `.env` is in `.gitignore`:**
   ```bash
   grep "^\.env$" .gitignore
   # Should output: .env
   ```

### Required API Keys

#### LLM Providers (at least one required):

- **OpenAI**: Get from https://platform.openai.com/api-keys
- **Aliyun DashScope** (Qwen): Get from https://dashscope.console.aliyun.com/apiKey
- **Anthropic** (Claude): Get from https://console.anthropic.com/settings/keys
- **DeepSeek**: Get from https://platform.deepseek.com/api_keys

#### Search API (required for Research mode):

- **SerpAPI**: Get from https://serpapi.com/manage-api-key

#### Optional Domain APIs:

- **OpenWeather**: Get from https://home.openweathermap.org/api_keys
- **Alpha Vantage**: Get from https://www.alphavantage.co/support/#api-key

### Checking Your Configuration

Run this command to verify your API keys are loaded (without exposing them):

```bash
python3 << 'EOF'
from src.utils.config import get_config
import os

config = get_config()
print("\n🔑 API Key Status:")
print(f"  OpenAI: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
print(f"  DashScope: {'✅ Set' if os.getenv('DASHSCOPE_API_KEY') else '❌ Missing'}")
print(f"  SerpAPI: {'✅ Set' if os.getenv('SERPAPI_API_KEY') else '❌ Missing'}")
print(f"  OpenWeather: {'✅ Set' if os.getenv('OPENWEATHER_API_KEY') else '❌ Missing'}")
print(f"  Alpha Vantage: {'✅ Set' if os.getenv('ALPHA_VANTAGE_API_KEY') else '❌ Missing'}")
EOF
```

---

## 🚨 Git History Cleanup (If .env Was Previously Committed)

**WARNING**: The `.env` file was found in git history (commits c8cdb12 and e4ac31d). If this repository contains real API keys, they are exposed and should be **rotated immediately**.

### Step 1: Rotate All Compromised API Keys

Before cleaning git history, rotate (regenerate) all API keys that were in the committed `.env` file:

1. **OpenAI**: https://platform.openai.com/api-keys → Revoke old key → Create new
2. **DashScope**: https://dashscope.console.aliyun.com/apiKey → Delete old → Create new
3. **SerpAPI**: https://serpapi.com/manage-api-key → Regenerate
4. **Others**: Regenerate all other exposed keys

### Step 2: Remove .env from Git History

⚠️ **WARNING**: This will rewrite git history. Coordinate with all collaborators first.

#### Option A: Using git filter-repo (Recommended)

```bash
# Install git-filter-repo if not installed
# macOS: brew install git-filter-repo
# Linux: pip3 install git-filter-repo

# Backup your repository first!
cd /Users/sudo/PycharmProjects/ai_search
cp -r . ../ai_search_backup

# Remove .env from all commits
git filter-repo --path .env --invert-paths --force

# Re-add the remote (filter-repo removes it for safety)
git remote add origin <your-remote-url>

# Force push (WARNING: destructive operation)
git push origin --force --all
git push origin --force --tags
```

#### Option B: Using BFG Repo-Cleaner

```bash
# Download BFG from https://rtyley.github.io/bfg-repo-cleaner/

# Backup first!
cp -r . ../ai_search_backup

# Remove .env file
java -jar bfg.jar --delete-files .env

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

#### Option C: Manual Filter-Branch (Last Resort)

```bash
# Backup first!
cp -r . ../ai_search_backup

# Remove .env from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

### Step 3: Verify Cleanup

```bash
# Check that .env is gone from history
git log --all --full-history -- .env
# Should return nothing

# Verify .env is in .gitignore
cat .gitignore | grep "^\.env$"
# Should output: .env

# Check current status
git status
# .env should NOT appear in "Changes to be committed" or "Untracked files"
# (It will still exist locally, which is correct)
```

### Step 4: Notify Collaborators

If this is a shared repository, all collaborators must:

```bash
# Fetch the cleaned history
git fetch origin

# Reset their local branch (WARNING: loses local changes)
git reset --hard origin/main  # or master

# Clean up old references
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

## Best Practices

### ✅ DO:
- Keep API keys in `.env` file only
- Use `.env.template` for documentation
- Rotate keys regularly (every 90 days)
- Use different keys for dev/staging/production
- Set up key expiration if provider supports it
- Monitor API usage for anomalies

### ❌ DON'T:
- Never commit `.env` to git
- Never share API keys in chat/email
- Never hardcode keys in source code
- Never use production keys in development
- Never commit `config.yaml` with real keys
- Never screenshot or log API keys

---

## Environment-Specific Configuration

### Development
```bash
# .env
ENVIRONMENT=development
# Use free-tier or test API keys
```

### Staging
```bash
# .env
ENVIRONMENT=staging
# Use separate staging keys with rate limits
```

### Production
```bash
# .env
ENVIRONMENT=production
# Use production keys with monitoring
```

---

## Troubleshooting

### "No LLM providers available"
- Check that at least one LLM API key is set in `.env`
- Verify the key is valid (not expired/revoked)
- Check `config.yaml` has `enabled: true` for that provider

### "Search failed"
- Verify `SERPAPI_API_KEY` is set in `.env`
- Check SerpAPI quota hasn't been exceeded

### Keys not loading
```bash
# Verify .env file exists
ls -la .env

# Check file permissions (should be readable)
chmod 600 .env

# Test loading manually
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Keys loaded:', bool(os.getenv('DASHSCOPE_API_KEY')))"
```

---

## Additional Security Measures

### 1. File Permissions
```bash
# Restrict .env to owner only
chmod 600 .env
```

### 2. Git Hooks
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
if git diff --cached --name-only | grep -q "^\.env$"; then
    echo "❌ ERROR: Attempting to commit .env file!"
    echo "This file contains sensitive API keys."
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### 3. Secrets Scanning
Consider using tools like:
- **git-secrets**: https://github.com/awslabs/git-secrets
- **truffleHog**: https://github.com/trufflesecurity/truffleHog
- **GitHub Secret Scanning**: Enable in repo settings

---

## Contact

If you believe API keys were exposed:
1. Rotate all keys immediately
2. Review access logs on provider dashboards
3. Report to security team if applicable
4. Follow git history cleanup steps above

Last Updated: 2025-11-04
