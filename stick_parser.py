import re

def parse_control_string(control_str: str) -> dict:
    """Parses EAFC control strings into structured mechanical steps."""
    modifiers = list(set(re.findall(r'(L1|L2|R1|R2|LB|LT|RB|RT|Q|Z|C|E)', control_str)))
    
    stick = "RS" if re.search(r'\b(RS|R|Right Stick)\b', control_str) else None
    stick = "LS" if re.search(r'\b(LS|L|Left Stick)\b', control_str) else stick
    
    action = "Flick" if re.search(r'\b(Flick|Tap)\b', control_str, re.IGNORECASE) else "Hold"
    action = "Rotate" if re.search(r'\b(Rotate|Roll|Spin)\b', control_str, re.IGNORECASE) else action
    
    # Extract strict arrows or map natural language to directions
    arrows = re.findall(r'[↑↓←→]+', control_str)
    direction = "".join(arrows) if arrows else ""
    if not direction:
        text = control_str.lower()
        if 'up' in text or 'forward' in text: direction += '↑'
        if 'down' in text or 'back' in text: direction += '↓'
        if 'left' in text: direction += '←'
        if 'right' in text: direction += '→'
        
    return {
        "stick": stick,
        "action": action,
        "direction": direction,
        "modifiers": modifiers
    }

def generate_animated_svg(parsed: dict) -> str:
    """Generates an inline Dark-Mode SVG visualizing the stick movement."""
    if not parsed.get("stick"):
        return ""

    cx, cy = 50, 50
    keyframes = ["0% { cx: 50px; cy: 50px; }"]
    
    dir_str = parsed.get("direction", "")
    if dir_str:
        for i, char in enumerate(dir_str):
            if char == '↑': cy -= 25
            elif char == '↓': cy += 25
            elif char == '←': cx -= 25
            elif char == '→': cx += 25
            pct = int(((i + 1) / len(dir_str)) * 100)
            keyframes.append(f"{pct}% {{ cx: {cx}px; cy: {cy}px; }}")

    css_keyframes = "\n".join(keyframes)
    
    return f"""
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <style>
            .stick {{
                animation: moveStick 2s infinite alternate ease-in-out;
                fill: #E5E7EB; stroke: #374151; stroke-width: 2;
            }}
            @keyframes moveStick {{ {css_keyframes} }}
        </style>
        <circle cx="50" cy="50" r="40" fill="#1F2937" stroke="#4B5563" stroke-width="4"/>
        <circle class="stick" cx="50" cy="50" r="15" />
        <text x="50" y="54" font-size="12" fill="#9CA3AF" font-family="sans-serif" text-anchor="middle" font-weight="bold">{parsed['stick']}</text>
    </svg>
    """