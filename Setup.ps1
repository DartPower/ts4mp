function Main() {
	Write-Host "==== ts4multiplayer ===="

	$config = @{
		mode = GetModeString (PromptUntilValid 'Server (s) or Client (c)' '[sc]')
		host = Read-Host -Prompt 'Host'
		port = Read-Host -Prompt 'Port'
	}

	SetupMod (New-Object -TypeName psobject -Prop $config)

	return
}

function SetupMod($config) {
	CreateMarkerFile $config

	UpdateConfig $config
}

function GetModeString ($mode) {
	If ($mode -match 's') {
		return 'server'
	}
	Else {
		return 'client'
	}
}

$coreDirectory = 'srcScripts\ts4mp\core'

function CreateMarkerFile($config) {
	ClearExistingSetup

	$mode = $config.mode

	New-Item "srcScripts\ts4mp\core\$mode.txt"
}

function ClearExistingSetup() {
	$paths = ".\$coreDirectory\client.txt", ".\$coreDirectory\server.txt"

	Write-Host "Checking for $paths"

	ForEach ($path in $paths) {
		If (Test-Path $path) {
			Write-Host "Removing $path"
			Remove-Item $path | Out-Null
		}
	}
}

function UpdateConfig($config) {
	$mode = $config.mode
	$sourceFilePath = Resolve-Path "$coreDirectory\multiplayer_$mode.py"

	Write-Host "Updating $sourceFilePath $config"

	(Get-Content -Path "$sourceFilePath.tmp") | ForEach-Object {$_ -Replace '\$\{serverHost\}', $config.host -Replace '\$\{serverPort\}', $config.port} | Set-Content -Path $sourceFilePath
}

function PromptUntilValid($prompt, $pattern) {
	$value = $null
	While (($value = Prompt $prompt) -notmatch $pattern) {}

	return $value
}

function Prompt($prompt) {
	return (Read-Host -Prompt $prompt)
}

Main
