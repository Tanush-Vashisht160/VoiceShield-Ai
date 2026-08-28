#!/usr/bin/env python3
"""Fix the live transcription display issue"""

import re

with open('frontend/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

print("=== Analyzing app.js ===")

# Check if flag exists
if 'liveTranscriptBoxShowing' in content:
    print("✓ Transcript tracking flag already added")
else:
    print("⚠ Flag not found - adding it...")
    if 'let liveSpeechRestartTimer = null;' in content:
        content = content.replace(
            'let liveSpeechRestartTimer = null;',
            'let liveSpeechRestartTimer = null;\nlet liveTranscriptBoxShowing = false;'
        )
        print("✓ Added flag")

# Count listening messages
listening_count = content.count('Listening for speech')
print(f"Found {listening_count} 'Listening for speech' messages")

# Fix the transcript display to only show "Listening..." once
# Replace the section that shows listening message with flag-based display
old_listening_code = '''        transcriptBox.innerHTML =
            `
            <div style="
                font-size:9px;
                letter-spacing:0.12em;
                opacity:0.5;
                margin-bottom:4px;
            ">
                LIVE TRANSCRIPT
            </div>

            <div style="
                opacity:0.45;
            ">
                Listening for speech...
            </div>
            `;

        return;'''

new_listening_code = '''        if (!liveTranscriptBoxShowing) {
            transcriptBox.innerHTML = `<div style="font-size:9px;letter-spacing:0.12em;opacity:0.5;margin-bottom:8px;">LIVE TRANSCRIPT</div><div style="opacity:0.45;">Listening for speech...</div>`;
            liveTranscriptBoxShowing = true;
        }
        return;'''

if old_listening_code in content:
    content = content.replace(old_listening_code, new_listening_code)
    print("✓ Fixed listening message to only show once")
else:
    print("⚠ Could not find exact listening code pattern")

# Also fix the final display code to properly show transcription
old_display = '''    transcriptBox.innerHTML =
        `
        <div style="
            font-size:9px;
            letter-spacing:0.12em;
            opacity:0.5;
            margin-bottom:4px;
        ">
            LIVE TRANSCRIPT
        </div>

        <div>
            ${escapeHtml(finalText)}

            <span style="
                opacity:0.45;
            ">
                ${escapeHtml(interimText)}
            </span>
        </div>
        `;'''

new_display = '''    liveTranscriptBoxShowing = true;
    transcriptBox.innerHTML = `<div style="font-size:9px;letter-spacing:0.12em;opacity:0.5;margin-bottom:8px;">LIVE TRANSCRIPT</div><div style="color:#f1f7f5;line-height:1.5;">${escapeHtml(finalText)}<span style="opacity:0.5;">${escapeHtml(interimText)}</span></div>`;'''

if old_display in content:
    content = content.replace(old_display, new_display)
    print("✓ Fixed actual transcription display")
else:
    print("⚠ Could not find exact transcription display pattern")

# Reset the flag when starting a new call
if 'liveTranscriptBoxShowing = false;' in content:
    # Add flag reset in startRealTimeMicrophone
    if 'liveChunksProcessed = 0;' in content:
        content = content.replace(
            'liveChunksProcessed = 0;',
            'liveChunksProcessed = 0;\n        liveTranscriptBoxShowing = false;'
        )
        print("✓ Added flag reset on new microphone call")

with open('frontend/js/app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ app.js updated successfully!")
