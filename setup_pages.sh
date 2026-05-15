#!/bin/bash
# Setup GitHub Pages for sales-dashboard

curl -s -u "naichaniuniu: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" \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/naichaniuiu/sales-dashboard/pages \
  -d '{
    "source": {
      "branch": "master",
      "path": "/"
    }
  }'
