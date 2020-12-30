$date = Get-Date -format o
$file_name = "C:\Program Files\SplunkUniversalForwarder\etc\apps\pms_opera_custom_apps\lookups\opera_connections.csv"
$Timestamp = $date.ToString()
$Timestamp + '  ps_version=' + $PSVersionTable.PSVersion
$csv = Import-csv  $file_name

                                  
foreach($interfaces in $csv)
{
    $t = New-Object Net.Sockets.TcpClient
    # We use Try\Catch to remove exception info from console if we can't connect
    try
    {
        $port = $interfaces.port
        $t.Connect($interfaces.hostname,$port)
    } catch
    {
   
       
    }

    if($t.Connected)
    {
        $t.Close()
        $msg = $interfaces.hostname +",$port,open"
        $Timestamp + '  ' + $msg
    }
    else
    {
        $msg = $interfaces.hostname +",$port,closed" 
        $Timestamp + '  ' + $msg                            
    }
    
 }