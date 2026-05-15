#!/bin/bash
curl -s -u naichaniuniu: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 \
  -H "Content-Type: application/json" \
  https://api.github.com/user/repos \
  -d '{"name":"sales-dashboard","description":"Sales Dashboard","private":true,"has_issues":true,"has_wiki":false}'
