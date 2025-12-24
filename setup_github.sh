#!/bin/bash

# Script to set up GitHub remote for AI Native Book repository

echo "Setting up GitHub remote for AI Native Book repository..."

# Add the remote origin
git remote add origin https://github.com/bilalwebs/AI_Native_Book.git

# Verify the remote was added
git remote -v

echo "Remote origin added successfully!"
echo ""
echo "To push your code to GitHub, run:"
echo "git branch -M main"
echo "git push -u origin main"