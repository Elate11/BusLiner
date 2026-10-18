import subprocess
import os

svg_full_bleed = """<svg width="1024" height="1024" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1E40AF" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#0B132B" stop-opacity="1"/>
    </radialGradient>
    <linearGradient id="squircleGrad" x1="192" y1="192" x2="832" y2="832" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#2563EB"/>
      <stop offset="40%" stop-color="#1E3A8A"/>
      <stop offset="100%" stop-color="#0F2156"/>
    </linearGradient>
    <filter id="shadow" x="132" y="142" width="760" height="760" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="24" stdDeviation="32" flood-color="#000000" flood-opacity="0.5"/>
      <feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#1E3A8A" flood-opacity="0.4"/>
    </filter>
  </defs>

  <!-- Deep background -->
  <rect width="1024" height="1024" fill="url(#bgGlow)"/>

  <!-- Logo squircle from site: scaled from 28x28 -->
  <g filter="url(#shadow)">
    <rect x="192" y="192" width="640" height="640" rx="144" fill="url(#squircleGrad)" stroke="#3B82F6" stroke-width="6" stroke-opacity="0.4"/>
    
    <!-- White forward arrow: M6 14H22M22 14L16 8.5M22 14L16 19.5 scaled to 640 -->
    <!-- offset: (192, 192), scale: 640/28 = 22.857 -->
    <!-- X(x) = 192 + x * 22.857 -->
    <!-- Y(y) = 192 + y * 22.857 -->
    <!-- 6 -> 329, 22 -> 695, 14 -> 512, 16 -> 558, 8.5 -> 386, 19.5 -> 638, 9 -> 398, 11.5 -> 455, 19 -> 626 -->
    <path d="M329 512H695M695 512L558 386M695 512L558 638" stroke="#FFFFFF" stroke-width="54" stroke-linecap="round" stroke-linejoin="round"/>
    
    <!-- Speed lines in ice blue #93C5FD -->
    <path d="M329 398H455M329 626H455" stroke="#93C5FD" stroke-width="46" stroke-linecap="round"/>
  </g>
</svg>"""

svg_circle_fill = """<svg width="1024" height="1024" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="circleGrad" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#2563EB"/>
      <stop offset="45%" stop-color="#1E3A8A"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </radialGradient>
    <radialGradient id="rimGlow" cx="50%" cy="50%" r="50%">
      <stop offset="70%" stop-color="#38BDF8" stop-opacity="0"/>
      <stop offset="100%" stop-color="#38BDF8" stop-opacity="0.3"/>
    </radialGradient>
  </defs>

  <!-- Full Circle Avatar (perfect for Telegram's circle crop) -->
  <circle cx="512" cy="512" r="512" fill="url(#circleGrad)"/>
  <circle cx="512" cy="512" r="506" stroke="url(#rimGlow)" stroke-width="12"/>

  <!-- Main arrow: stroke-width 64 -->
  <path d="M280 512H744M744 512L570 350M744 512L570 674" stroke="#FFFFFF" stroke-width="68" stroke-linecap="round" stroke-linejoin="round"/>
  
  <!-- Speed lines in ice blue #93C5FD -->
  <path d="M280 366H440M280 658H440" stroke="#93C5FD" stroke-width="58" stroke-linecap="round"/>
</svg>"""

with open("/tmp/avatar_squircle.svg", "w") as f:
    f.write(svg_full_bleed)

with open("/tmp/avatar_circle.svg", "w") as f:
    f.write(svg_circle_fill)

subprocess.run(["/opt/homebrew/bin/rsvg-convert", "-w", "1024", "-h", "1024", "/tmp/avatar_squircle.svg", "-o", "/Users/aleksandr/BusLiner/busliner_bot_avatar_exact.png"], check=True)
subprocess.run(["/opt/homebrew/bin/rsvg-convert", "-w", "1024", "-h", "1024", "/tmp/avatar_circle.svg", "-o", "/Users/aleksandr/BusLiner/busliner_bot_avatar_circle.png"], check=True)

# Also create JPG versions
from PIL import Image
im1 = Image.open("/Users/aleksandr/BusLiner/busliner_bot_avatar_exact.png").convert("RGB")
im1.save("/Users/aleksandr/BusLiner/busliner_bot_avatar_exact.jpg", quality=98)
im1.save("/Users/aleksandr/busliner_bot_avatar_exact.jpg", quality=98)

im2 = Image.open("/Users/aleksandr/BusLiner/busliner_bot_avatar_circle.png").convert("RGB")
im2.save("/Users/aleksandr/BusLiner/busliner_bot_avatar_circle.jpg", quality=98)
im2.save("/Users/aleksandr/busliner_bot_avatar_circle.jpg", quality=98)

print("Generated exact avatars successfully!")
