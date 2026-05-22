[System.Reflection.Assembly]::LoadWithPartialName('System.IO.Compression') | Out-Null

$Keywords = "template|for|coding"
$Url = "https://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
$OutputFile = "found_domains.txt"

Write-Host "Downloading and filtering domains..."
$WebClient = New-Object System.Net.WebClient
$ZipBytes = $WebClient.DownloadData($Url)
$Stream = New-Object System.IO.MemoryStream(,$ZipBytes)
$Archive = New-Object System.IO.Compression.ZipArchive($Stream)
$Entry = $Archive.Entries[0]
$Reader = New-Object System.IO.StreamReader($Entry.Open())

$MatchedDomains = @()
while (($Line = $Reader.ReadLine()) -ne $null) {
    if ($Line -match ",.*($($Keywords))") {
        $Domain = $Line.Split(",")[1].Trim()
        $MatchedDomains += "http://$Domain"
    }
}
$Reader.Close(); $Archive.Dispose(); $Stream.Dispose()

Write-Host "Testing $($MatchedDomains.Count) domains for active HTTP 200 status..."

$LiveDomains = @()
$MatchedDomains | ForEach-Object {
    try {
        $Req = [System.Net.HttpWebRequest]::Create($_)
        $Req.Timeout = 5000
        $Req.AllowAutoRedirect = $true
        $Res = $Req.GetResponse()
        if ([int]$Res.StatusCode -eq 200) {
            Write-Host " [+] [LIVE] $_" -ForegroundColor Green
            $LiveDomains += $_
        }
        $Res.Close()
    } catch {}
}

$LiveDomains | Out-File -FilePath $OutputFile
Write-Host "Results saved to $OutputFile"