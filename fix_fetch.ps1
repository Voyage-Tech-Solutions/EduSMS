$file = "C:\Users\bathini bona\Documents\EduSMS\frontend\src\app\dashboard\teacher\planning\page.tsx"
$content = Get-Content $file -Raw
# Add import after first import line
$content = $content -replace '(import \{ useState, useEffect \} from "react";)', "`$1`nimport { authFetch } from `"@/lib/authFetch`";"
# Replace fetch with authFetch for API calls (double-quoted strings)
$content = $content -replace 'fetch\("/api/v1/', 'authFetch("/api/v1/'
# Replace fetch with authFetch for API calls (template literals)
$content = $content -replace 'fetch\(`/api/v1/', 'authFetch(`/api/v1/'
Set-Content $file $content -NoNewline
Write-Host "Done. Replacements applied."
