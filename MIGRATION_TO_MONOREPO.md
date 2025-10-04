# Migration to Monorepo - Step-by-Step Guide

**Goal**: Create new `haystack-platform` repo while preserving all git history from `haystack-data-simulator`

---

## Step 1: Create New Repository on GitHub

1. Go to https://github.com/datakwip
2. Click "New repository"
3. Name: `haystack-platform`
4. Description: "Complete building automation data platform with simulator, API, and web interface"
5. **Important**: Do NOT initialize with README, .gitignore, or license (we're bringing our own)
6. Click "Create repository"

---

## Step 2: Clone Existing Repo (With Full History)

```bash
# Clone haystack-data-simulator with all history
git clone git@github.com:datakwip/haystack-data-simulator.git haystack-platform

cd haystack-platform

# Verify we have all history
git log --oneline | head -10
# Should show recent commits like:
#   af8a3d4 Corrected points that weren't generating...
#   b7cb281 Refactoring and Clean Up
#   etc.

# Update remote to point to NEW repo
git remote set-url origin git@github.com:datakwip/haystack-platform.git

# Verify
git remote -v
# Should show:
#   origin  git@github.com:datakwip/haystack-platform.git (fetch)
#   origin  git@github.com:datakwip/haystack-platform.git (push)
```

**What we've done**: We now have all the simulator history, but it will push to the NEW repo!

---

## Step 3: Make Script Executable

```bash
chmod +x restructure-to-monorepo.sh
```

---

## Step 4: Check for db-service-layer

The script will look for `db-service-layer` in the parent directory. If you have it locally:

```bash
# Option A: Already have it?
ls ../db-service-layer
# If yes, the script will copy it

# Option B: Clone it now
cd ..
git clone git@github.com:datakwip/db-service-layer.git
cd haystack-platform
```

If you don't have it, the script will clone it automatically.

---

## Step 5: Run Restructuring Script

```bash
./restructure-to-monorepo.sh
```

**The script will:**
1. ✅ Move simulator code to `simulator/` directory
2. ✅ Copy/clone db-service-layer to `api/` directory
3. ✅ Create webapp skeleton in `webapp/` directory
4. ✅ Update `docker-compose.yaml` for monorepo structure
5. ✅ Update `README.md` with new structure
6. ✅ Update `CLAUDE.md` with monorepo instructions

**Output will look like:**
```
==========================================
🔄 Converting to Monorepo Structure
==========================================

📁 Step 1/6: Moving simulator code to simulator/ directory...
------------------------------------------------------------
  Moving src/ → simulator/src/
  Moving config/ → simulator/config/
  ...
✅ Simulator code moved

🌐 Step 2/6: Adding db-service-layer as api/...
------------------------------------------------------------
  Found db-service-layer in parent directory
  ✅ Copied from ../db-service-layer

🎨 Step 3/6: Creating webapp/ skeleton...
------------------------------------------------------------
✅ Webapp skeleton created

...

==========================================
✅ Restructuring Complete!
==========================================
```

---

## Step 6: Review Changes

```bash
# See what changed
git status

# Should show:
#   renamed:    src/ -> simulator/src/
#   renamed:    config/ -> simulator/config/
#   new file:   api/...
#   new file:   webapp/...
#   modified:   docker-compose.yaml
#   modified:   README.md
#   modified:   CLAUDE.md

# Review the diff (will be large!)
git diff --staged --stat

# Or review specific files
git diff --staged README.md
git diff --staged docker-compose.yaml
```

---

## Step 7: Commit Everything

```bash
git commit -m "Convert to monorepo structure

- Move simulator code to simulator/
- Add db-service-layer as api/
- Create webapp/ skeleton (Next.js)
- Update docker-compose.yaml for all services
- Update documentation for monorepo

This preserves all git history from haystack-data-simulator
while restructuring for multi-service development.

Services:
  - api/        FastAPI backend (port 8000)
  - simulator/  Data generator (port 8080)
  - webapp/     Next.js GUI (port 3000)
"
```

---

## Step 8: Push to New Repository

```bash
# Push to haystack-platform repo
git push -u origin main

# Should see:
#   Enumerating objects: X, done.
#   Writing objects: 100% (X/X), ...
#   To github.com:datakwip/haystack-platform.git
#    * [new branch]      main -> main
```

**Verify on GitHub**: Go to https://github.com/datakwip/haystack-platform

You should see:
- ✅ All your commits in history
- ✅ New folder structure (api/, simulator/, webapp/)
- ✅ Updated README.md

---

## Step 9: Test Locally

```bash
# Make sure you're in the repo root
cd ~/path/to/haystack-platform

# Start all services
docker-compose up

# Check logs in another terminal
docker-compose logs -f api
docker-compose logs -f simulator
docker-compose logs -f webapp

# Access services:
# API:              http://localhost:8000
# API Docs:         http://localhost:8000/docs
# Simulator Health: http://localhost:8080/health
# WebApp:           http://localhost:3000
```

---

## Step 10: Update GitHub Repository Settings (Optional)

1. Go to https://github.com/datakwip/haystack-platform/settings
2. Update description: "Complete building automation data platform"
3. Add topics: `building-automation`, `haystack`, `timescaledb`, `fastapi`, `nextjs`
4. Update website: (if you deploy to Railway)

---

## Step 11: Archive Old Repository (Optional)

Once you're confident the migration worked:

1. Go to https://github.com/datakwip/haystack-data-simulator/settings
2. Scroll to "Danger Zone"
3. Click "Archive this repository"
4. Add a README note at the top:

```markdown
# ⚠️ ARCHIVED - This repository has moved!

**New location**: https://github.com/datakwip/haystack-platform

This repository has been restructured into a monorepo containing:
- API (db-service-layer extensions)
- Simulator (this code)
- WebApp (Next.js GUI)

All git history has been preserved in the new repository.
```

---

## Troubleshooting

### Issue: "db-service-layer not found"

```bash
# Clone it manually
cd ..
git clone git@github.com:datakwip/db-service-layer.git
cd haystack-platform
./restructure-to-monorepo.sh
```

### Issue: "You have uncommitted changes"

```bash
# Stash or commit them first
git status
git add .
git commit -m "WIP: before restructuring"
./restructure-to-monorepo.sh
```

### Issue: Docker compose fails

```bash
# Check that paths are correct
ls -la
# Should show: api/ simulator/ webapp/ schema/

# Rebuild images
docker-compose build --no-cache

# Check logs
docker-compose logs api
```

### Issue: Want to undo restructuring

```bash
# If you haven't pushed yet
git reset --hard HEAD~1  # Undo commit
git clean -fd            # Remove untracked files

# If you have pushed
git revert HEAD
git push
```

---

## Summary

**What we did:**
1. ✅ Created new GitHub repo: `haystack-platform`
2. ✅ Cloned existing repo with **full git history**
3. ✅ Redirected git remote to new repo
4. ✅ Restructured into monorepo (api/, simulator/, webapp/)
5. ✅ Pushed to new repo (with all history preserved!)

**Result:**
- New repo with perfect name
- All git history preserved
- Monorepo structure ready for Claude Code
- Old repo can be archived (optional)

**Next steps:**
- Develop with Claude Code in single session across all services
- Deploy to Railway (3 services)
- Build out webapp features

---

**Questions?** Check:
- `README.md` - Project overview
- `CLAUDE.md` - Development instructions
- `API_EXTENSION_PLAN.md` - Implementation roadmap
