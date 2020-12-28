$date = Get-Date
$Timestamp = $date.ToString("u")
$Timestamp + '  ps_version=' + $PSVersionTable.PSVersion
if(Test-Path D:\Marriott\MPCM-Opera\ssl\ssl-opera.epf -PathType Leaf)
{

    $content = get-content D:\Marriott\MPCM-Opera\ssl\ssl-opera.epf | select-string "ou=opera"
    if($content -ne $null)
    {
        $lastModifiedDate = (Get-Item "D:\Marriott\MPCM-Opera\ssl\ssl-opera.epf").LastWriteTime;
        $Timestamp + ' ssl_last_update=' + $lastModifiedDate 
        $Timestamp + ' ssl_' + $content 
    }
    else
    {
        $Timestamp + ' ssl_last_update=file_not_found'
        $Timestamp + ' ssl_name=file_not_found' 
    }
    
}
else
{
     $Timestamp + ' ssl_last_update=file_not_found'
     $Timestamp + ' ssl_name=file_not_found' 
}

if(Test-Path D:\Marriott\MPCM-Opera\OXI\OXI-opera.epf -PathType Leaf)
{

    $content = get-content D:\Marriott\MPCM-Opera\OXI\OXI-opera.epf | select-string "ou=oxi"
    if($content -ne $null)
    {
        $lastModifiedDate = (Get-Item "D:\Marriott\MPCM-Opera\OXI\OXI-opera.epf").LastWriteTime;
        $Timestamp + ' oxi_last_update=' + $lastModifiedDate 
        $Timestamp + ' oxi_' + $content 
       
    }
    else
    {
        $Timestamp + ' oxi_last_update=file_not_found' 
        $Timestamp + ' oxi_name=file_not_found' 
    }
}
else
{
     $Timestamp + ' oxi_last_update=file_not_found' 
     $Timestamp + ' oxi_name=file_not_found' 
}

if(Test-Path D:\Marriott\MPCM-Opera\token\token*.epf -PathType Leaf)
{

    $content = get-content D:\Marriott\MPCM-Opera\token\token*.epf | select-string "ou=opera"
    if($content -ne $null)
    {
        $lastModifiedDate = (Get-Item "D:\Marriott\MPCM-Opera\token\token*.epf").LastWriteTime;
        $Timestamp + ' token_last_update=' + $lastModifiedDate 
        $Timestamp + ' token_' + $content 
    }
    else
    {
        $Timestamp + ' token_last_update=file_not_found'
        $Timestamp + ' token_name=file_not_found' 
    }
}
else
{
    $Timestamp + ' token_last_update=file_not_found'
    $Timestamp + ' token_name=file_not_found'
}

if(Test-Path D:\Marriott\MPCM-Opera\SOA\Soa-opera.epf -PathType Leaf)
{

    $content = get-content D:\Marriott\MPCM-Opera\SOA\Soa-opera.epf | select-string "ou=Opera"
    if($content -ne $null)
    {
        $lastModifiedDate = (Get-Item "D:\Marriott\MPCM-Opera\SOA\Soa-opera.epf").LastWriteTime;
        $Timestamp + ' soa_last_update=' + $lastModifiedDate 
        $Timestamp + ' soa_' + $content 
		$Timestamp + ' unmanaged_soa_last_update=wallet_installed'
		$Timestamp + ' unmanaged_soa=wallet_installed'
       
    }
    else
    {
        $Timestamp + ' soa_last_update=file_not_found'
        $Timestamp + ' soa_name=file_not_found'
    }

}
else
{ 
	$Timestamp + ' soa_last_update=file_not_found'
	$Timestamp + ' soa_name=file_not_found'
	if(Test-Path D:\oracle\admin\OPERA\wallets\Marriott\ewallet.p12 -PathType Leaf)
	{
		
		
			$lastModifiedDate = (Get-Item "D:\oracle\admin\OPERA\wallets\Marriott\ewallet.p12").LastWriteTime;
			$Timestamp + ' unmanaged_soa_last_update=' + $lastModifiedDate 
			$Timestamp + ' unmanaged_soa=wallet_installed'  
       
	}	
	else
	{
		$Timestamp + ' unmanaged_soa_last_update=file_not_found' 
		$Timestamp + ' unmanaged_soa=file_not_found' 
	}
}

$flag = $false
Foreach ($cert in (ls Cert:\LocalMachine\My ))
{
                if($cert.Subject | select-string "oxi")
                {              
                                $Timestamp + ' mimpg_last_update=' + $cert.NotBefore
                                $Timestamp + ' mimpg_name=' + $cert.Subject
				$flag = $true
                }
}
if(!$flag)
{
    $Timestamp + '  mimpg_last_update=file_not_found'
    $Timestamp + '  mimpg_name=file_not_found'
    $flag = $true
}



