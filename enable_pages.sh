#!/bin/bash
# Enable GitHub Pages for the sales-dashboard repository

curl -s -u "naichaniuniu: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" \
  -X PUT \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/naichaniunu/sales-dashboard/pages \
  -d '{
    "source": {
      "branch": "master",
      "path": "/"
    }
  }'
