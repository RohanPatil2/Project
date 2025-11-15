# How to Push Your Code to GitHub

## Repository
https://github.com/RohanPatil2/uncertainty-aware-slam.git

## Method 1: Using the Provided Script (Recommended)

### Step 1: Open WSL Terminal
Open a WSL Ubuntu terminal (not PowerShell)

### Step 2: Navigate to workspace
```bash
cd /home/rohan/slam_uncertainty_ws
```

### Step 3: Make script executable
```bash
chmod +x push_to_github.sh
```

### Step 4: Run the script
```bash
./push_to_github.sh
```

The script will:
- Initialize git repository
- Add all files
- Create a commit
- Push to GitHub

### Step 5: Authenticate
When prompted, you'll need to authenticate with GitHub. You have two options:

#### Option A: Personal Access Token (PAT) - Recommended
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "SLAM Uncertainty Push"
4. Select scope: `repo` (full control of private repositories)
5. Click "Generate token"
6. Copy the token (you won't see it again!)
7. When git asks for password, paste the token

#### Option B: SSH Key
If you already have SSH keys set up with GitHub, the push will work automatically.

---

## Method 2: Manual Commands

If the script doesn't work, run these commands manually in WSL:

```bash
# Navigate to workspace
cd /home/rohan/slam_uncertainty_ws

# Initialize git (if not already done)
git init

# Configure git
git config user.name "RohanPatil2"
git config user.email "your-email@example.com"  # Update with your email

# Add remote
git remote add origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
# OR if remote already exists:
git remote set-url origin https://github.com/RohanPatil2/uncertainty-aware-slam.git

# Stage all files
git add .

# Create commit
git commit -m "Complete uncertainty-aware SLAM implementation"

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## Method 3: Using GitHub Desktop (Easiest for Windows)

1. Download and install GitHub Desktop: https://desktop.github.com/
2. Open GitHub Desktop
3. File → Add Local Repository
4. Browse to: `\\wsl.localhost\Ubuntu-22.04\home\rohan\slam_uncertainty_ws`
5. Click "Add Repository"
6. Click "Publish repository"
7. Select: RohanPatil2/uncertainty-aware-slam
8. Click "Publish"

---

## Troubleshooting

### Authentication Failed
- Use a Personal Access Token (PAT) instead of your password
- Generate at: https://github.com/settings/tokens
- When git asks for password, paste the PAT token

### Permission Denied
```bash
# Check SSH key
ssh -T git@github.com

# Or switch to HTTPS
git remote set-url origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
```

### Files Already Exist on Remote
If the remote repository already has files, you may need to pull first:
```bash
git pull origin main --allow-unrelated-histories
# Then push
git push -u origin main
```

### Force Push (if needed)
⚠️ WARNING: This will overwrite remote repository!
```bash
git push -u origin main --force
```

---

## What Gets Pushed

The following will be included:
- ✅ Source code (`src/`)
- ✅ Documentation (`.md` files)
- ✅ Configuration files
- ✅ Launch files
- ✅ Scripts
- ✅ World files

The following will be excluded (via `.gitignore`):
- ❌ Build artifacts (`build/`, `install/`)
- ❌ Log files (`log/`)
- ❌ Python cache (`__pycache__/`)
- ❌ IDE settings (`.vscode/`)
- ❌ Results data (`results/`)
- ❌ Bag files (`.bag`, `.db3`)

---

## After Pushing

1. Verify on GitHub: https://github.com/RohanPatil2/uncertainty-aware-slam
2. The README.md will be displayed on the repository page
3. Check that all files are present
4. You can now clone on other machines:
   ```bash
   git clone https://github.com/RohanPatil2/uncertainty-aware-slam.git
   ```

---

## Making Future Updates

After the initial push, you can update with:

```bash
cd /home/rohan/slam_uncertainty_ws

# Stage changes
git add .

# Commit
git commit -m "Description of your changes"

# Push
git push origin main
```

---

## Need Help?

If you encounter issues:
1. Check that you're in the correct directory
2. Verify git is installed: `git --version`
3. Check your internet connection
4. Ensure you have permissions for the repository
5. Try using a Personal Access Token for authentication

For more help: https://docs.github.com/en/get-started/using-git

