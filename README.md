
# Pants ORAS plugin 

This plugin lets you upload arbitrary files as ORAS artifacts. ORAS lets you
use OCI registries for storing artifacts with metadata.

## Testing

Spin up a local Zot registry with 
```
docker run -d -p 5000:5000 --name zot ghcr.io/project-zot/zot-linux-arm64:latest
```

After that, you can run this command to publish this projects' README file to `hello-from-pants`:

```
pants publish :test-oras
```
