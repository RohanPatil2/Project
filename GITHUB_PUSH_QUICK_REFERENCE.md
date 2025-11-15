# Quick Reference: Push to GitHub

## 🎯 Repository
**https://github.com/RohanPatil2/uncertainty-aware-slam.git**

---

## ⚡ Three Ways to Push

### Method 1: Double-Click (Windows) ✨ EASIEST
1. **Double-click** `push_to_github.bat` in File Explorer
2. When prompted for password, use your **GitHub Personal Access Token**
3. Get token at: https://github.com/settings/tokens

### Method 2: WSL Terminal (Linux)
```bash
cd /home/rohan/slam_uncertainty_ws
chmod +x push_to_github.sh
./push_to_github.sh
```

### Method 3: Manual Git Commands
```bash
cd /home/rohan/slam_uncertainty_ws
git init
git remote add origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main
```

---

## 🔑 Authentication

### Get Personal Access Token (PAT)
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "SLAM Push"
4. Select: ✅ `repo` (Full control)
5. Click "Generate"
6. **Copy the token** (you won't see it again!)

### Use the Token
- **Username**: RohanPatil2
- **Password**: *paste your token here*

---

## 📦 What Gets Pushed

### ✅ Included
- Source code (`src/`)
- Documentation (`.md` files)
- Configuration files
- Launch files
- Scripts
- World files
- Package files

### ❌ Excluded (via .gitignore)
- Build artifacts (`build/`, `install/`)
- Log files (`log/`)
- Python cache
- IDE settings
- Results data
- Bag files

---

## 🔧 Troubleshooting

### "Authentication failed"
→ Use Personal Access Token, not password

### "Remote already exists"
```bash
git remote set-url origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
```

### "Repository not empty"
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Force push (⚠️ overwrites remote)
```bash
git push -u origin main --force
```

---

## 🔄 Future Updates

After initial push:
```bash
cd /home/rohan/slam_uncertainty_ws
git add .
git commit -m "Your update message"
git push origin main
```

Or just run `push_to_github.bat` again!

---

## ✅ Verify

After pushing, check:
- https://github.com/RohanPatil2/uncertainty-aware-slam
- All files should be visible
- README.md should display

---

## 📞 Need More Help?

See detailed guide: **PUSH_TO_GITHUB.md**

---

**Quick Command for Copy-Paste:**
```bash
cd /home/rohan/slam_uncertainty_ws && git init && git remote add origin https://github.com/RohanPatil2/uncertainty-aware-slam.git && git add . && git commit -m "Initial commit" && git branch -M main && git push -u origin main
```

