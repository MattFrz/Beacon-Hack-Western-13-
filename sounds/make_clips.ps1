# Makes every Beacon voice clip as a 16 kHz mono 16-bit WAV using the
# text-to-speech voice built into Windows. No installs needed.
#
#   powershell -ExecutionPolicy Bypass -File sounds\make_clips.ps1
#
# Add a line to $clips to make a new clip. Object names use name_<label>.

Add-Type -AssemblyName System.Speech

$clips = [ordered]@{
    'num_0' = 'zero';  'num_1' = 'one';   'num_2' = 'two';   'num_3' = 'three'; 'num_4' = 'four'
    'num_5' = 'five';  'num_6' = 'six';   'num_7' = 'seven'; 'num_8' = 'eight'; 'num_9' = 'nine'
    'metre' = 'metre'; 'metres' = 'metres'
    'ahead' = 'ahead'; 'left' = 'left'; 'right' = 'right'; 'up' = 'up'; 'down' = 'down'
    'about' = 'about'; 'a_little' = 'a little'; 'you_are_back' = 'you are back'
    'lost_target'    = 'I lost the target'
    'stopping'       = 'stopping'
    'not_seen'       = 'I have not seen that'
    'did_not_catch'  = 'I did not catch that'
    'cannot_help'    = 'I cannot help with that'
    'cannot_retrace' = 'I cannot retrace without a path'
    'name_keys'      = 'keys'
    'name_keychain'  = 'keychain'
    'name_cup'       = 'cup'
    'name_mug'       = 'mug'
    'name_bottle'    = 'bottle'
    'name_phone'     = 'phone'
}

# The Windows voice leaves ~0.7 s of silence after every word. Cut it down to
# 30 ms each side so stitched cues ("keys, about two metres") stay quick.
function Remove-WavSilence([string]$path) {
    $b = [IO.File]::ReadAllBytes($path)
    # Find the 'data' chunk (the Windows voice writes an 18-byte fmt chunk).
    $pos = 12; $data = -1; $dataLen = 0
    while ($pos + 8 -le $b.Length) {
        $id = [Text.Encoding]::ASCII.GetString($b, $pos, 4)
        $size = [BitConverter]::ToInt32($b, $pos + 4)
        if ($id -eq 'data') { $data = $pos + 8; $dataLen = [Math]::Min($size, $b.Length - $data); break }
        $pos += 8 + $size + ($size % 2)
    }
    if ($data -lt 0) { Write-Warning "$path has no data chunk; left untrimmed"; return }
    $n = [int][Math]::Floor($dataLen / 2)
    $first = -1; $last = -1
    for ($i = 0; $i -lt $n; $i++) {
        $v = [Math]::Abs([int][BitConverter]::ToInt16($b, $data + 2 * $i))
        if ($v -gt 500) { if ($first -lt 0) { $first = $i }; $last = $i }
    }
    if ($first -lt 0) { return }
    $pad = 480   # 30 ms at 16 kHz
    $s = [Math]::Max(0, $first - $pad)
    $e = [Math]::Min($n - 1, $last + $pad)
    $len = ($e - $s + 1) * 2
    # Write a plain 44-byte PCM header: 16 kHz, mono, 16-bit.
    $out = New-Object byte[] (44 + $len)
    $ascii = [Text.Encoding]::ASCII
    $ascii.GetBytes('RIFF').CopyTo($out, 0)
    [BitConverter]::GetBytes([int](36 + $len)).CopyTo($out, 4)
    $ascii.GetBytes('WAVEfmt ').CopyTo($out, 8)
    [BitConverter]::GetBytes([int]16).CopyTo($out, 16)
    [BitConverter]::GetBytes([int16]1).CopyTo($out, 20)      # PCM
    [BitConverter]::GetBytes([int16]1).CopyTo($out, 22)      # mono
    [BitConverter]::GetBytes([int]16000).CopyTo($out, 24)    # sample rate
    [BitConverter]::GetBytes([int]32000).CopyTo($out, 28)    # byte rate
    [BitConverter]::GetBytes([int16]2).CopyTo($out, 32)      # block align
    [BitConverter]::GetBytes([int16]16).CopyTo($out, 34)     # bits
    $ascii.GetBytes('data').CopyTo($out, 36)
    [BitConverter]::GetBytes([int]$len).CopyTo($out, 40)
    [Array]::Copy($b, $data + 2 * $s, $out, 44, $len)
    [IO.File]::WriteAllBytes($path, $out)
}

$outDir = $PSScriptRoot
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000,
    [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
    [System.Speech.AudioFormat.AudioChannel]::Mono)
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 1   # a little faster than default; short cues matter

foreach ($name in $clips.Keys) {
    $path = Join-Path $outDir "$name.wav"
    $synth.SetOutputToWaveFile($path, $fmt)
    $synth.Speak($clips[$name])
    $synth.SetOutputToNull()
    Remove-WavSilence $path
    Write-Output ("{0,-16} {1}" -f "$name.wav", $clips[$name])
}
$synth.Dispose()
Write-Output "Made $($clips.Count) clips in $outDir"
