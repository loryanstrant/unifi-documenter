# GitHub Setup and GHCR Publishing Guide

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and log in
2. Click "New repository" (green button)
3. Set repository name: `unifi-documenter`
4. Make it public (required for free GHCR)
5. Don't initialize with README (we already have files)
6. Click "Create repository"

## Step 2: Push Code to GitHub

After creating the repository, GitHub will show you the remote URL. Run these commands:

```bash
cd /workspaces/unifi-documenter

# Add GitHub as remote (replace with your actual repository URL)
git remote add origin https://github.com/loryanstrant/unifi-documenter.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click on "Actions" tab
3. GitHub Actions should be enabled by default
4. The workflow will automatically trigger on the first push

## Step 4: Monitor the Build

1. After pushing, go to "Actions" tab in your GitHub repository
2. You should see "Build and Push Docker Image" workflow running
3. Click on it to monitor progress
4. The build will create multi-architecture images (AMD64 and ARM64)

## Step 5: Using the Published Image

Once the GitHub Action completes, your Docker image will be available at:
```
ghcr.io/loryanstrant/unifi-documenter:latest
```

### Pull and Use the Image

```bash
# Pull the image
docker pull ghcr.io/loryanstrant/unifi-documenter:latest

# Or use docker-compose (already configured)
docker-compose up -d
```

## Step 6: Verify GHCR Package

1. Go to your GitHub profile
2. Click "Packages" tab
3. You should see `unifi-documenter` package listed
4. Click on it to see versions and usage instructions

## Available Image Tags

The GitHub Actions workflow creates these tags:
- `latest` - Latest build from main branch
- `main` - Same as latest
- `v1.0.0` - When you create version tags
- `1.0` - Major.minor version

## Manual Build (Alternative)

If you prefer to build and push manually:

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/loryanstrant/unifi-documenter:latest \
  --push .

# Login to GHCR first
echo $GITHUB_TOKEN | docker login ghcr.io -u loryanstrant --password-stdin
```

## Troubleshooting

### GitHub Actions Issues
- Ensure repository is public (for free GHCR)
- Check Actions tab for error details
- Verify GitHub token permissions

### Docker Build Issues
- Check Dockerfile syntax
- Verify all files are committed
- Review build logs in Actions tab

### Permission Issues
- Ensure GitHub Actions has package write permissions
- Check if organization settings allow package creation

## Next Steps

1. Create releases with version tags (e.g., `v1.0.0`)
2. Add issue templates for bug reports
3. Set up dependabot for security updates
4. Add contribution guidelines

The automated build will handle everything once you push to GitHub!