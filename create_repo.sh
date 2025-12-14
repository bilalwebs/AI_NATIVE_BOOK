#!/bin/bash

# Script to create a GitHub repository for the AI Humanoid Book RAG project
# Usage:
# 1. Replace YOUR_TOKEN with your actual GitHub personal access token
# 2. Run this script: bash create_repo.sh

# GitHub personal access token (replace with your actual token)
TOKEN="YOUR_TOKEN"

# Repository details
REPO_NAME="ai-humanoid-book-rag"
REPO_DESC="A comprehensive textbook and research repository on Physical AI & Humanoid Robotics with Retrieval-Augmented Generation (RAG) capabilities."
PRIVATE=false

# Check if token is set
if [ "$TOKEN" = "YOUR_TOKEN" ]; then
    echo "Please update the TOKEN variable with your GitHub personal access token"
    exit 1
fi

# Create the repository using GitHub API
echo "Creating GitHub repository: $REPO_NAME"

curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $TOKEN" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"$REPO_DESC\",
    \"private\": $PRIVATE,
    \"auto_init\": false,
    \"gitignore_template\": \"Node\"
  }"

echo "Repository creation request sent. Check your GitHub account for the new repository."