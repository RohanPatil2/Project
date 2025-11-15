#!/bin/bash

# Script to push code to GitHub repository
# Repository: https://github.com/RohanPatil2/uncertainty-aware-slam.git

set -e  # Exit on error

echo "========================================="
echo "Pushing code to GitHub"
echo "Repository: https://github.com/RohanPatil2/uncertainty-aware-slam.git"
echo "========================================="

# Navigate to workspace
cd /home/rohan/slam_uncertainty_ws

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    echo "Git repository initialized."
fi

# Configure git (update with your details if needed)
echo "Configuring git..."
git config user.name "RohanPatil2"
git config user.email "rohanpatil@example.com"

# Add remote if not already added
if ! git remote | grep -q "origin"; then
    echo "Adding remote origin..."
    git remote add origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
else
    echo "Remote origin already exists. Updating URL..."
    git remote set-url origin https://github.com/RohanPatil2/uncertainty-aware-slam.git
fi

# Check if .gitignore exists
if [ -f ".gitignore" ]; then
    echo ".gitignore already exists - keeping existing file."
else
    echo "Warning: No .gitignore found. Consider creating one."
fi

echo "Staging all files..."
git add .

echo "Creating commit..."
git commit -m "Complete uncertainty-aware SLAM implementation

- Real-time entropy quantification
- Synthetic robot for testing
- Advanced exploration algorithms  
- Active SLAM with frontier detection
- Publication-quality visualizations
- Complete system launcher
- Comprehensive documentation" || echo "No changes to commit or commit already exists"

# Check if we're on main branch, if not create it
CURRENT_BRANCH=$(git branch --show-current)
if [ -z "$CURRENT_BRANCH" ]; then
    echo "Creating main branch..."
    git branch -M main
elif [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Renaming branch to main..."
    git branch -M main
fi

echo ""
echo "========================================="
echo "Ready to push to GitHub!"
echo "========================================="
echo ""
echo "IMPORTANT: You need to authenticate with GitHub"
echo ""
echo "Options:"
echo "1. Use Personal Access Token (PAT)"
echo "2. Use SSH key"
echo ""
echo "For PAT: https://github.com/settings/tokens"
echo "Create a token with 'repo' permissions"
echo ""
echo "Attempting to push..."
echo ""

# Try to push
git push -u origin main

echo ""
echo "========================================="
echo "✅ Successfully pushed to GitHub!"
echo "========================================="
echo ""
echo "View your repository at:"
echo "https://github.com/RohanPatil2/uncertainty-aware-slam"

