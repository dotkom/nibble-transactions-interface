# format:
# VAR1=value1
# VAR2=value2

$envFilePath = "windows_env.txt"

Get-Content $envFilePath | ForEach-Object {
    $parts = $_ -split '='
    $name = $parts[0]
    $value = $parts[1]
    [System.Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
}
