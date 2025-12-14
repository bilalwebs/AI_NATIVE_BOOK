#!/bin/bash

# Script to initialize git and push to the GitHub repository
# Usage: bash setup_git.sh <github-repo-url>

# Check if repository URL is provided
if [ -z "$1" ]; then
    echo "Usage: bash setup_git.sh <github-repo-url>"
    echo "Example: bash setup_git.sh https://github.com/username/ai-humanoid-book-rag.git"
    exit 1
fi

REPO_URL=$1

echo "Setting up git and pushing to repository: $REPO_URL"

# Initialize git if not already initialized
if [ ! -d .git ]; then
    git init
fi

# Add all files
git add .

# Create initial commit if no commits exist
if [ -z "$(git log --oneline -1 2>/dev/null)" ]; then
    git config --global init.defaultBranch main
    git commit -m "Initial commit: AI Humanoid Book RAG system

This repository contains a comprehensive textbook and research material on Physical AI & Humanoid Robotics with Retrieval-Augmented Generation (RAG) capabilities.

Features:
- Interactive AI assistant for textbook content
- Retrieval-Augmented Generation for accurate responses
- Comprehensive coverage of Physical AI & Humanoid Robotics concepts"
fi

# Add the remote origin
git remote add origin $REPO_URL

# Push to main branch
git branch -M main
git push -u origin main

echo "Successfully pushed to GitHub repository!"