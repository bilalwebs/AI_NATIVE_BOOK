# GitHub Repository Setup Instructions

This guide will help you create and set up the GitHub repository for the AI Humanoid Book RAG project.

## Step 1: Create a GitHub Personal Access Token

1. Go to GitHub.com and sign in to your account
2. Click on your profile picture in the top-right corner and select "Settings"
3. In the left sidebar, click on "Developer settings"
4. Click on "Personal access tokens" and then "Tokens (classic)"
5. Click "Generate new token"
6. Select the following scopes:
   - `repo` - to create and manage repositories
   - `read:org` - if you want to create repositories under an organization
7. Click "Generate token"
8. Copy the generated token (you won't be able to see it again)

## Step 2: Create the Repository

1. Open the `create_repo.sh` script in this directory
2. Replace `YOUR_TOKEN` with your actual GitHub personal access token
3. Save the file
4. Run the script:
   ```bash
   bash create_repo.sh
   ```

## Step 3: Push the Code to GitHub

After the repository is created, you'll need to push the code:

1. Copy the repository URL from GitHub (e.g., `https://github.com/username/ai-humanoid-book-rag.git`)

2. Add the remote origin:
   ```bash
   git remote add origin https://github.com/username/ai-humanoid-book-rag.git
   ```

3. Push the code:
   ```bash
   git branch -M main
   git push -u origin main
   ```

## Alternative Method: Using GitHub CLI

If you prefer to use the GitHub CLI directly:

1. Install GitHub CLI (instructions vary by platform)
2. Authenticate:
   ```bash
   gh auth login
   ```
3. Create the repository:
   ```bash
   gh repo create ai-humanoid-book-rag --public --description "A comprehensive textbook and research repository on Physical AI & Humanoid Robotics with Retrieval-Augmented Generation (RAG) capabilities."
   ```
4. Push the code:
   ```bash
   git remote add origin https://github.com/username/ai-humanoid-book-rag.git
   git branch -M main
   git push -u origin main
   ```