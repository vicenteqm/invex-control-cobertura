# Programa INVEX todos los días, de 08:00 a 18:00, en la sesión del usuario.
$ErrorActionPreference = 'Stop'
$proyecto = Split-Path -Parent $PSScriptRoot
$ejecutor = Join-Path $proyecto 'ACTUALIZAR_INVEX.bat'
if (-not (Test-Path -LiteralPath $ejecutor)) { throw 'No se encuentra ACTUALIZAR_INVEX.bat.' }
$nombre = 'INVEX - Actualizar cobertura cada hora'
$ahora = Get-Date
$disparadores = @(foreach ($hora in 8..18) {
    $inicio = $ahora.Date.AddHours($hora)
    if ($inicio -le $ahora) { $inicio = $inicio.AddDays(1) }
    New-ScheduledTaskTrigger -Daily -At $inicio
})
# La redirección evita dejar consolas esperando la tecla final del BAT.
$accion = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/d /c ""' + $ejecutor + '" <nul"') -WorkingDirectory $proyecto
$usuario = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$principal = New-ScheduledTaskPrincipal -UserId $usuario -LogonType Interactive -RunLevel Limited
$ajustes = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 55) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparadores -Principal $principal -Settings $ajustes -Description 'INVEX: lunes a domingo, 08:00, 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00 y 18:00. Requiere sesión Windows abierta; Pandape puede pedir ingreso manual.' -Force | Out-Null
$tarea = Get-ScheduledTask -TaskName $nombre
$info = Get-ScheduledTaskInfo -TaskName $nombre
[pscustomobject]@{Tarea=$nombre;Estado=$tarea.State;ProximaEjecucion=$info.NextRunTime;Horarios=@($tarea.Triggers | ForEach-Object {$_.StartBoundary});Instancias=$tarea.Settings.MultipleInstances;Accion=$tarea.Actions.Arguments} | ConvertTo-Json -Depth 4
