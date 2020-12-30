$date = Get-Date
$Timestamp = $date.ToString("s")
$mname = hostname
$mname = 'host=' + $mname
$formsweb = 'D:\oracle\10gappr2\forms\server\formsweb.cfg'
#$outfile = 'C:\TEMP\property_scan.txt'
#if D:\oracle\10gappr2\forms\server\formsweb.cfg exists
if(Test-Path $formsweb)
{
#here we check the userid field
$content2 = get-content $formsweb | select-string 'userid='
foreach($user in $content2)
{
if($user -like '*/*' )
{
$userid= 'userid=fail'
break
}
else
{
$userid= 'userid=pass'
}
}
#here we evaluate the encrypted field
$content3 = get-content $formsweb | select-string 'encrypted='
foreach($encrypt in $content3)
{
if($encrypt -like 'encrypted=0')
{
$encrypted='encrypted=fail'
break
}
else
{
$encrypted='encrypted=pass'
}
}
$Timestamp + ' ' + $EncryptConfig + ' ' + $userid + ' ' + $encrypted
$output = $Timestamp + ' ' + $mname + ' ' + $EncryptConfig + ' ' + $userid + ' ' + $encrypted
#Out-File $outfile -InputObject $output -Encoding utf8
}
#if D:\oracle\10gappr2\forms\server\formsweb.cfg does not exist
else
{
$EncryptConfig='encryptconfig=na'
$userid='userid=na'
$encrypted='encrypted=na'
$Timestamp + ' ' + $EncryptConfig + ' ' + $userid + ' ' + $encrypted
$output = $Timestamp + ' ' + $mname + ' ' + $EncryptConfig + ' ' + $userid + ' ' + $encrypted
#Out-File $outfile -InputObject $output -Encoding utf8
}