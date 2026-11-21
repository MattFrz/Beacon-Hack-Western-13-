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
    Write-Output ("{0,-16} {1}" -f "$name.wav", $clips[$name])
}
$synth.Dispose()
Write-Output "Made $($clips.Count) clips in $outDir"
