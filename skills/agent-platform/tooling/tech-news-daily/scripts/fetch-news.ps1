param($MaxPerSource=20,$TimeoutSec=10)
$ErrorActionPreference="Continue"

$feeds=@(
@{N="The Verge";U="https://www.theverge.com/rss/index.xml";L="en"},
@{N="TechCrunch";U="https://techcrunch.com/feed/";L="en"},
@{N="Ars Technica";U="https://arstechnica.com/feed/";L="en"},
@{N="Wired";U="https://www.wired.com/feed/rss";L="en"},
@{N="MIT Tech Review";U="https://www.technologyreview.com/feed/";L="en"},
@{N="Stratechery";U="https://stratechery.com/feed/";L="en"},
@{N="IEEE Spectrum";U="https://spectrum.ieee.org/feed";L="en"},
@{N="TMTPost";U="https://www.tmtpost.com/rss";L="zh"},
@{N="36Kr";U="https://36kr.com/feed";L="zh"},
@{N="Ifanr";U="https://www.ifanr.com/feed";L="zh"},
@{N="Jiqizhixin";U="https://www.jiqizhixin.com/rss";L="zh"},
@{N="Qbitai";U="https://www.qbitai.com/rss";L="zh"},
@{N="Okjike";U="https://okjike.com/rss";L="zh"}
)

function GTV($v){
    if($v -eq $null){return ""}
    $t = $v.GetType().Name
    if($t -eq "XmlCDataSection"){return $v."#cdata"}
    if($t -eq "XmlElement"){return $v.InnerText}
    return [string]$v
}

$all = @()
$idx = 0
foreach($f in $feeds){
    $idx++
    Write-Host "[$idx] $($f.N) -> $($f.U)" -F Cyan
    try{
        $resp = Invoke-WebRequest -Uri $f.U -TimeoutSec $TimeoutSec -UseBasicParsing
        $xml = [xml]$resp.Content
        $items = $null
        if($xml.rss -and $xml.rss.channel.item){
            $items = $xml.rss.channel.item | Select-Object -First $MaxPerSource
            Write-Host "  RSS format, $($items.Count) items" -F Yellow
            foreach($i in $items){
                $title = GTV($i.title)
                $link = GTV($i.link)
                $desc = GTV($i.description)
                $pd = $i.pubDate
                $all += @{
                    Title = $title.Trim()
                    Link = $link.Trim()
                    PubDate = if($pd){$pd.ToString()}else{""}
                    Source = $f.N
                    Lang = $f.L
                    Description = if($desc.Length -gt 200){$desc.Substring(0,200)+"..."}else{$desc}
                }
            }
        }elseif($xml.feed -and $xml.feed.entry){
            $items = $xml.feed.entry | Select-Object -First $MaxPerSource
            Write-Host "  Atom format, $($items.Count) items" -F Yellow
            foreach($i in $items){
                $title = GTV($i.title)
                $lk = $i.link
                if($lk -ne $null -and $lk.href -ne $null){$lk = $lk.href.ToString()}else{$lk = ""}
                $sum = $i.summary; if($sum -eq $null){$sum = $i.content}
                $sum = GTV($sum)
                $pd = if($i.published){$i.published}elseif($i.updated){$i.updated}else{""}
                $all += @{
                    Title = $title.Trim()
                    Link = $lk.Trim()
                    PubDate = if($pd){$pd.ToString()}else{""}
                    Source = $f.N
                    Lang = $f.L
                    Description = if($sum.Length -gt 200){$sum.Substring(0,200)+"..."}else{$sum}
                }
            }
        }else{
            Write-Host "  Unknown XML structure" -F Red
        }
        Write-Host "  -> $($items.Count) items" -F Green
    }catch{
        Write-Host "  -> FAILED: $($_.Exception.Message)" -F Red
    }
}
Write-Host ""
Write-Host "[Total] $($all.Count) items" -F Yellow
$all | ConvertTo-Json -Depth 5
