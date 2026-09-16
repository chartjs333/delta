param(
    [switch]$Offline,
    [int]$Port = 0,
    [switch]$NoBrowser,
    [switch]$PrepareOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-ExitCode {
    param([Parameter(Mandatory = $true)][string]$Operation)
    if ($LASTEXITCODE -ne 0) {
        throw "$Operation failed with exit code $LASTEXITCODE"
    }
}

function Assert-NoInjectedJavaOptions {
    foreach ($variableName in @("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS")) {
        $value = [Environment]::GetEnvironmentVariable($variableName, "Process")
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            throw "Refusing injected JVM options from $variableName"
        }
    }
}

function Test-FileIdentity {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][long]$ExpectedLength,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -ne $ExpectedLength) {
        return $false
    }
    $actualHash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    return $actualHash -eq $ExpectedSha256.ToLowerInvariant()
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Test-LockedJdkInstallation {
    param(
        [Parameter(Mandatory = $true)][string]$InstallHome,
        [Parameter(Mandatory = $true)][pscustomobject]$ToolchainLock
    )

    $java = Join-Path $InstallHome "bin/java.exe"
    $javac = Join-Path $InstallHome "bin/javac.exe"
    $jar = Join-Path $InstallHome "bin/jar.exe"
    $release = Join-Path $InstallHome "release"
    $markerPath = Join-Path $InstallHome ".delta-mnist-toolchain.json"
    foreach ($requiredFile in @($java, $javac, $jar, $release, $markerPath)) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            return $false
        }
        $item = Get-Item -LiteralPath $requiredFile -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $false
        }
    }

    try {
        $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
        if ($marker.type_name -ne "MNIST_DELTA_DEMO_JDK_INSTALLATION" -or
            $marker.schema_version -ne "1.0.0" -or
            $marker.vendor -ne [string]$ToolchainLock.vendor -or
            $marker.version -ne [string]$ToolchainLock.version -or
            $marker.archive_sha256 -ne ([string]$ToolchainLock.archive_sha256).ToLowerInvariant() -or
            $marker.release_sha256 -ne (Get-Sha256 -Path $release) -or
            $marker.java_sha256 -ne (Get-Sha256 -Path $java) -or
            $marker.javac_sha256 -ne (Get-Sha256 -Path $javac)) {
            return $false
        }
        $releaseText = Get-Content -LiteralPath $release -Raw
        if ($releaseText -notmatch '(?m)^IMPLEMENTOR="Eclipse Adoptium"\r?$' -or
            $releaseText -notmatch ('(?m)^SEMANTIC_VERSION="' +
                [regex]::Escape([string]$ToolchainLock.version) + '"\r?$') -or
            $releaseText -notmatch '(?m)^OS_NAME="Windows"\r?$' -or
            $releaseText -notmatch '(?m)^OS_ARCH="x86_64"\r?$') {
            return $false
        }
    }
    catch {
        return $false
    }
    return $true
}

function Assert-SafeJdkArchiveLayout {
    param([Parameter(Mandatory = $true)][string]$Archive)

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $topLevelNames = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        foreach ($entry in $zip.Entries) {
            $normalized = $entry.FullName.Replace('\', '/')
            if ([string]::IsNullOrWhiteSpace($normalized) -or
                $normalized.StartsWith('/', [System.StringComparison]::Ordinal) -or
                $normalized -match '^[A-Za-z]:' -or
                $normalized.IndexOf([char]0) -ge 0) {
                throw "Pinned JDK archive contains an unsafe entry"
            }
            $segments = @($normalized.Split('/') | Where-Object { $_ -ne "" })
            if ($segments.Count -eq 0 -or
                $segments -contains "." -or
                $segments -contains "..") {
                throw "Pinned JDK archive contains an unsafe entry"
            }
            [void]$topLevelNames.Add($segments[0])
        }
    }
    finally {
        $zip.Dispose()
    }
    if ($topLevelNames.Count -ne 1) {
        throw "Pinned JDK archive has an unexpected layout"
    }
}

function Resolve-JavaToolchain {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][bool]$NetworkDisabled
    )

    $toolchainLockPath = Join-Path $RepositoryRoot "integration/mnist-delta/windows-toolchain.lock.json"
    $toolchainLock = Get-Content -LiteralPath $toolchainLockPath -Raw | ConvertFrom-Json
    if ($toolchainLock.type_name -ne "MNIST_DELTA_DEMO_WINDOWS_TOOLCHAIN_LOCK" -or
        $toolchainLock.schema_version -ne "1.0.0" -or
        $toolchainLock.vendor -ne "Eclipse Temurin" -or
        $toolchainLock.os -ne "windows" -or
        $toolchainLock.architecture -ne "x64" -or
        [int]$toolchainLock.feature -ne 25 -or
        [long]$toolchainLock.archive_size_bytes -le 0 -or
        [string]$toolchainLock.archive_sha256 -notmatch '^[0-9a-f]{64}$') {
        throw "Invalid MNIST demo Windows toolchain lock"
    }
    $archiveUri = [uri][string]$toolchainLock.archive_url
    if (-not $archiveUri.IsAbsoluteUri -or $archiveUri.Scheme -ne "https") {
        throw "Pinned JDK archive URL must use HTTPS"
    }

    $toolchainCache = Join-Path $RepositoryRoot "artifacts/local/mnist-delta-toolchain/jdk25"
    New-Item -ItemType Directory -Force -Path $toolchainCache | Out-Null
    $expectedArchiveHash = ([string]$toolchainLock.archive_sha256).ToLowerInvariant()
    $lockedHome = Join-Path $toolchainCache (
        "temurin-$($toolchainLock.version)-$($expectedArchiveHash.Substring(0, 16))"
    )
    if (Test-Path -LiteralPath $lockedHome) {
        if (-not (Test-LockedJdkInstallation `
                -InstallHome $lockedHome `
                -ToolchainLock $toolchainLock)) {
            throw "Content-addressed JDK installation failed validation: $lockedHome"
        }
    }
    else {
        $archiveName = [System.IO.Path]::GetFileName($archiveUri.LocalPath)
        if ([string]::IsNullOrWhiteSpace($archiveName)) {
            throw "Pinned JDK archive URL has no file name"
        }
        $contentArchive = Join-Path $toolchainCache "jdk-$expectedArchiveHash.zip"
        $legacyArchive = Join-Path $toolchainCache $archiveName
        $archive = $null
        foreach ($candidateArchive in @($contentArchive, $legacyArchive)) {
            if (Test-FileIdentity `
                    -Path $candidateArchive `
                    -ExpectedLength ([long]$toolchainLock.archive_size_bytes) `
                    -ExpectedSha256 $expectedArchiveHash) {
                $archive = (Resolve-Path -LiteralPath $candidateArchive).Path
                break
            }
        }

        if ($null -eq $archive) {
            if ($NetworkDisabled) {
                throw "The exact pinned JDK 25 archive is absent in offline mode"
            }
            if (Test-Path -LiteralPath $contentArchive) {
                throw "Corrupt content-addressed JDK archive: $contentArchive"
            }
            $partial = "$contentArchive.download-$PID-$([guid]::NewGuid().ToString('N'))"
            try {
                Invoke-WebRequest `
                    -UseBasicParsing `
                    -Uri ([string]$toolchainLock.archive_url) `
                    -OutFile $partial
                if (-not (Test-FileIdentity `
                        -Path $partial `
                        -ExpectedLength ([long]$toolchainLock.archive_size_bytes) `
                        -ExpectedSha256 $expectedArchiveHash)) {
                    throw "Pinned JDK 25 digest mismatch"
                }
                if (Test-Path -LiteralPath $contentArchive) {
                    if (-not (Test-FileIdentity `
                            -Path $contentArchive `
                            -ExpectedLength ([long]$toolchainLock.archive_size_bytes) `
                            -ExpectedSha256 $expectedArchiveHash)) {
                        throw "Concurrent JDK cache write produced invalid bytes"
                    }
                }
                else {
                    Move-Item -LiteralPath $partial -Destination $contentArchive
                }
                $archive = (Resolve-Path -LiteralPath $contentArchive).Path
            }
            finally {
                if (Test-Path -LiteralPath $partial -PathType Leaf) {
                    Remove-Item -LiteralPath $partial -Force
                }
            }
        }

        Assert-SafeJdkArchiveLayout -Archive $archive
        $extractRoot = Join-Path $toolchainCache (
            "extracting-$PID-$([guid]::NewGuid().ToString('N'))"
        )
        New-Item -ItemType Directory -Path $extractRoot | Out-Null
        Expand-Archive -LiteralPath $archive -DestinationPath $extractRoot
        $extractedHomes = @(Get-ChildItem -LiteralPath $extractRoot -Directory)
        if ($extractedHomes.Count -ne 1) {
            throw "Pinned JDK 25 archive has an unexpected extracted layout: $extractRoot"
        }

        $extractedHome = $extractedHomes[0].FullName
        $javaCandidate = Join-Path $extractedHome "bin/java.exe"
        $javacCandidate = Join-Path $extractedHome "bin/javac.exe"
        $jarCandidate = Join-Path $extractedHome "bin/jar.exe"
        $releaseCandidate = Join-Path $extractedHome "release"
        foreach ($requiredFile in @($javaCandidate, $javacCandidate, $jarCandidate, $releaseCandidate)) {
            if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
                throw "Pinned JDK archive is missing a required file: $requiredFile"
            }
        }
        $marker = [ordered]@{
            archive_sha256 = $expectedArchiveHash
            archive_size_bytes = [long]$toolchainLock.archive_size_bytes
            java_sha256 = Get-Sha256 -Path $javaCandidate
            javac_sha256 = Get-Sha256 -Path $javacCandidate
            release_sha256 = Get-Sha256 -Path $releaseCandidate
            schema_version = "1.0.0"
            type_name = "MNIST_DELTA_DEMO_JDK_INSTALLATION"
            vendor = [string]$toolchainLock.vendor
            version = [string]$toolchainLock.version
        }
        $markerPath = Join-Path $extractedHome ".delta-mnist-toolchain.json"
        $marker | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $markerPath -Encoding utf8

        if (Test-Path -LiteralPath $lockedHome) {
            throw "Concurrent JDK installation already created: $lockedHome"
        }
        Move-Item -LiteralPath $extractedHome -Destination $lockedHome
        Remove-Item -LiteralPath $extractRoot -Force
        if (-not (Test-LockedJdkInstallation `
                -InstallHome $lockedHome `
                -ToolchainLock $toolchainLock)) {
            throw "Pinned JDK 25 installation failed validation"
        }
    }

    $javaCandidate = Join-Path $lockedHome "bin/java.exe"
    $javacCandidate = Join-Path $lockedHome "bin/javac.exe"
    $jarCandidate = Join-Path $lockedHome "bin/jar.exe"
    $priorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $versionText = (& $javaCandidate -version 2>&1 | Out-String)
    }
    finally {
        $ErrorActionPreference = $priorPreference
    }
    if ($versionText -notmatch 'version "25(?:[.\"]|$)') {
        throw "Pinned JDK 25 installation failed validation"
    }
    return @{
        ArchiveSha256 = $expectedArchiveHash
        Home = (Resolve-Path -LiteralPath $lockedHome).Path
        Java = (Resolve-Path -LiteralPath $javaCandidate).Path
        JavaSha256 = Get-Sha256 -Path $javaCandidate
        Jar = (Resolve-Path -LiteralPath $jarCandidate).Path
        JarSha256 = Get-Sha256 -Path $jarCandidate
        Javac = (Resolve-Path -LiteralPath $javacCandidate).Path
        JavacSha256 = Get-Sha256 -Path $javacCandidate
        Major = 25
    }
}

function Get-LockedNettyClasspath {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$DependencyDirectory,
        [Parameter(Mandatory = $true)][bool]$NetworkDisabled
    )

    $lockPath = Join-Path $RepositoryRoot "delta-node-java/distribution-dependencies.lock.json"
    $lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json
    if ($lock.type_name -ne "DISTRIBUTION_DEPENDENCY_LOCK" -or
        [int]$lock.format_version -ne 1 -or
        [int]$lock.java.primary_feature -ne 25) {
        throw "Invalid Delta Java dependency lock"
    }
    New-Item -ItemType Directory -Force -Path $DependencyDirectory | Out-Null
    $resolved = [System.Collections.Generic.List[string]]::new()
    $coordinates = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    $fileNames = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )

    foreach ($artifact in $lock.maven_artifacts) {
        $artifactUri = [uri][string]$artifact.url
        $expectedHash = ([string]$artifact.sha256).ToLowerInvariant()
        $coordinate = [string]$artifact.coordinate
        $fileName = [System.IO.Path]::GetFileName($artifactUri.LocalPath)
        if (-not $artifactUri.IsAbsoluteUri -or $artifactUri.Scheme -ne "https" -or
            [long]$artifact.length -le 0 -or
            $expectedHash -notmatch '^[0-9a-f]{64}$' -or
            [string]::IsNullOrWhiteSpace($coordinate) -or
            [string]::IsNullOrWhiteSpace($fileName) -or
            -not $coordinates.Add($coordinate) -or
            -not $fileNames.Add($fileName)) {
            throw "Invalid or duplicate pinned Java dependency entry"
        }
        $target = Join-Path $DependencyDirectory $fileName
        $contentTarget = Join-Path $DependencyDirectory (
            "$([System.IO.Path]::GetFileNameWithoutExtension($fileName))-$expectedHash.jar"
        )
        $selectedTarget = $null
        foreach ($candidateTarget in @($target, $contentTarget)) {
            if (Test-FileIdentity `
                    -Path $candidateTarget `
                    -ExpectedLength ([long]$artifact.length) `
                    -ExpectedSha256 $expectedHash) {
                $selectedTarget = $candidateTarget
                break
            }
        }
        if ($null -eq $selectedTarget) {
            if ($NetworkDisabled) {
                throw "Pinned dependency is absent or invalid in offline mode: $coordinate"
            }
            if (Test-Path -LiteralPath $contentTarget) {
                throw "Corrupt content-addressed Java dependency: $contentTarget"
            }
            $partial = "$contentTarget.download-$PID-$([guid]::NewGuid().ToString('N'))"
            try {
                Invoke-WebRequest -UseBasicParsing -Uri ([string]$artifact.url) -OutFile $partial
                if (-not (Test-FileIdentity `
                        -Path $partial `
                        -ExpectedLength ([long]$artifact.length) `
                        -ExpectedSha256 $expectedHash)) {
                    throw "Pinned dependency digest mismatch: $coordinate"
                }
                if (Test-Path -LiteralPath $contentTarget) {
                    if (-not (Test-FileIdentity `
                            -Path $contentTarget `
                            -ExpectedLength ([long]$artifact.length) `
                            -ExpectedSha256 $expectedHash)) {
                        throw "Concurrent Java dependency cache write produced invalid bytes"
                    }
                }
                else {
                    Move-Item -LiteralPath $partial -Destination $contentTarget
                }
                $selectedTarget = $contentTarget
            }
            finally {
                if (Test-Path -LiteralPath $partial -PathType Leaf) {
                    Remove-Item -LiteralPath $partial -Force
                }
            }
        }
        $resolved.Add((Resolve-Path -LiteralPath $selectedTarget).Path)
    }
    if ($resolved.Count -eq 0) {
        throw "Delta Java dependency lock contains no artifacts"
    }
    return [string]::Join([System.IO.Path]::PathSeparator, $resolved)
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$buildRoot = Join-Path $repoRoot "out/build/mnist-delta"
$stageCBuildRoot = Join-Path $repoRoot "out/build/cpp20"
$nativeSource = Join-Path $repoRoot "integration/mnist-delta"
$javaClassesRoot = Join-Path $buildRoot "java-classes"
$javaDependencies = Join-Path $repoRoot "artifacts/local/mnist-delta-toolchain/netty"
$cacheDir = Join-Path $repoRoot "artifacts/local/mnist-cache"
$outputRoot = Join-Path $repoRoot "artifacts/local/mnist-demo"

Push-Location $repoRoot
try {
    Assert-NoInjectedJavaOptions

    Write-Host "[1/5] Building the Delta native MNIST node adapter..."
    & cmake -S $nativeSource -B $buildRoot "-DDELTA_SOURCE_ROOT=$repoRoot" "-DDELTA_WARNINGS_AS_ERRORS=ON"
    Assert-ExitCode "CMake configure"
    & cmake --build $buildRoot --config Release --target delta_mnist_native_node --parallel 2
    Assert-ExitCode "CMake native build"

    $nativeCandidates = @(
        (Join-Path $buildRoot "Release/delta_mnist_native_node.exe"),
        (Join-Path $buildRoot "delta_mnist_native_node.exe"),
        (Join-Path $buildRoot "delta_mnist_native_node")
    )
    $nativeExecutable = $nativeCandidates |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
        Select-Object -First 1
    if (-not $nativeExecutable) {
        throw "CMake did not produce delta_mnist_native_node"
    }

    Write-Host "[2/5] Building the Stage C REAL_DRQ1 native sidecar..."
    & cmake --preset cpp20
    Assert-ExitCode "Stage C CMake configure"
    & cmake --build --preset cpp20 --target delta_benchmark_sidecar --parallel 2
    Assert-ExitCode "Stage C sidecar build"
    $stageCSidecarCandidates = @(
        (Join-Path $stageCBuildRoot "Debug/delta_benchmark_sidecar.exe"),
        (Join-Path $stageCBuildRoot "Release/delta_benchmark_sidecar.exe"),
        (Join-Path $stageCBuildRoot "delta_benchmark_sidecar.exe"),
        (Join-Path $stageCBuildRoot "delta_benchmark_sidecar")
    )
    $stageCSidecar = $stageCSidecarCandidates |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
        Select-Object -First 1
    if (-not $stageCSidecar) {
        throw "CMake did not produce delta_benchmark_sidecar"
    }

    Write-Host "[3/5] Resolving the Java toolchain and locked Netty runtime..."
    $javaToolchain = Resolve-JavaToolchain `
        -RepositoryRoot $repoRoot `
        -NetworkDisabled ([bool]$Offline)
    $nettyClasspath = Get-LockedNettyClasspath `
        -RepositoryRoot $repoRoot `
        -DependencyDirectory $javaDependencies `
        -NetworkDisabled ([bool]$Offline)

    Write-Host "[4/5] Compiling the real Netty relay and Stage C transport helpers..."
    New-Item -ItemType Directory -Force -Path $javaClassesRoot | Out-Null
    $javaClasses = Join-Path $javaClassesRoot (
        "compile-$PID-$([guid]::NewGuid().ToString('N'))"
    )
    New-Item -ItemType Directory -Path $javaClasses | Out-Null
    $benchmarkSources = Get-ChildItem `
        -LiteralPath (Join-Path $repoRoot "delta-node-java/src/main/java/io/deltareduce/node/benchmark") `
        -Filter "*.java" |
        Sort-Object FullName |
        ForEach-Object { $_.FullName }
    $javaSources = @()
    $javaSources += $benchmarkSources
    $javaSources += (Join-Path $repoRoot "integration/mnist-delta/java/io/deltareduce/demo/MnistDeltaNettyRelay.java")
    $javacArguments = @(
        "--release", "$($javaToolchain.Major)",
        "-Xlint:all", "-Werror",
        "-cp", $nettyClasspath,
        "-d", $javaClasses
    ) + $javaSources
    & $javaToolchain.Javac @javacArguments
    Assert-ExitCode "Java relay compilation"
    $stageCHarness = Join-Path $javaClassesRoot (
        "stagec-transport-$PID-$([guid]::NewGuid().ToString('N')).jar"
    )
    & $javaToolchain.Jar "--create" "--file" $stageCHarness "-C" $javaClasses "."
    Assert-ExitCode "Stage C transport jar creation"

    $env:DELTA_MNIST_NATIVE_NODE = (Resolve-Path -LiteralPath $nativeExecutable).Path
    $env:DELTA_MNIST_JAVA = $javaToolchain.Java
    $env:DELTA_MNIST_JAVA_HOME = $javaToolchain.Home
    $env:DELTA_MNIST_RELAY_CLASSPATH = [string]::Join(
        [System.IO.Path]::PathSeparator,
        @((Resolve-Path -LiteralPath $javaClasses).Path, $nettyClasspath)
    )
    $env:DELTA_STAGEC_JAVA = $javaToolchain.Java
    $env:DELTA_STAGEC_NATIVE_SIDECAR = (Resolve-Path -LiteralPath $stageCSidecar).Path
    $env:DELTA_STAGEC_TRANSPORT_HARNESS = (Resolve-Path -LiteralPath $stageCHarness).Path
    $env:DELTA_STAGEC_NETTY_CLASSPATH = $nettyClasspath

    if ($PrepareOnly) {
        Write-Host "MNIST Delta native/Java toolchain is ready in this process."
        Write-Host "JDK archive SHA-256: $($javaToolchain.ArchiveSha256)"
        Write-Host "java.exe SHA-256: $($javaToolchain.JavaSha256)"
        Write-Host "javac.exe SHA-256: $($javaToolchain.JavacSha256)"
        Write-Host "jar.exe SHA-256: $($javaToolchain.JarSha256)"
        Write-Host "Native adapter: $env:DELTA_MNIST_NATIVE_NODE"
        Write-Host "Relay classpath: $env:DELTA_MNIST_RELAY_CLASSPATH"
        Write-Host "Stage C sidecar: $env:DELTA_STAGEC_NATIVE_SIDECAR"
        Write-Host "Stage C transport harness: $env:DELTA_STAGEC_TRANSPORT_HARNESS"
        return
    }

    Write-Host "[5/5] Starting the loopback-only commission workspace..."
    $arguments = @(
        "run",
        "--offline",
        "delta-mnist-demo",
        "serve",
        "--cache-dir", $cacheDir,
        "--output-root", $outputRoot,
        "--repository-root", $repoRoot,
        "--port", "$Port"
    )
    if ($Offline) {
        $arguments += "--offline"
    }
    if (-not $NoBrowser) {
        $arguments += "--open-browser"
    }

    & uv @arguments
    Assert-ExitCode "DeltaReduce MNIST demo"
}
finally {
    Pop-Location
}
