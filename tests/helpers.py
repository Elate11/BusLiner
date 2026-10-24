"""
BusLiner Quiet Luxury E2E Test Suite - Core Helpers and Utilities
Authoritative standards from ORIGINAL_REQUEST.md and PROJECT.md.
"""

import os
import re
import json
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup


@dataclass
class TestResult:
    test_id: str
    tier: int
    feature: str
    name: str
    description: str
    target: str
    passed: bool
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class TargetInspector:
    """Opaque-box inspector for BusLiner HTML/CSS/JS artifacts."""

    def __init__(self, file_path: str, raw_content: Optional[str] = None):
        self.file_path = file_path
        self.filename = os.path.basename(file_path) if file_path else "synthetic_fixture.html"
        if raw_content is not None:
            self.content = raw_content
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                self.content = f.read()

        self.soup = BeautifulSoup(self.content, "html.parser")
        self._extract_styles()
        self._extract_scripts()
        self._extract_css_variables()

    def _extract_styles(self):
        style_tags = self.soup.find_all("style")
        self.css_content = "\n".join(s.string or "" for s in style_tags)

    def _extract_scripts(self):
        script_tags = self.soup.find_all("script")
        # only inline scripts without src
        inline = [s.string or "" for s in script_tags if not s.get("src")]
        self.js_content = "\n".join(inline)

    def _extract_css_variables(self):
        self.css_vars = {}
        # Match :root { ... } blocks
        root_blocks = re.findall(r":root\s*\{([^}]+)\}", self.css_content, re.DOTALL)
        for block in root_blocks:
            matches = re.findall(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+);", block)
            for var_name, var_val in matches:
                # Strip inline comments
                val = re.sub(r"/\*.*?\*/", "", var_val).strip()
                self.css_vars[var_name] = val

    def get_css_var(self, var_name: str) -> Optional[str]:
        return self.css_vars.get(var_name)

    def extract_media_blocks(self, query_substr: str = "768px") -> List[str]:
        """Extract contents of all @media rules containing query_substr, correctly handling nested braces."""
        blocks = []
        css = self.css_content
        idx = 0
        while True:
            pos = css.find("@media", idx)
            if pos == -1:
                break
            open_brace = css.find("{", pos)
            if open_brace == -1:
                break
            header = css[pos:open_brace]
            depth = 1
            i = open_brace + 1
            while i < len(css) and depth > 0:
                if css[i] == "{":
                    depth += 1
                elif css[i] == "}":
                    depth -= 1
                i += 1
            content = css[open_brace + 1:i - 1]
            if query_substr in header:
                blocks.append(content)
            idx = i
        return blocks

    def has_pure_white(self) -> List[str]:
        """Detect any forbidden pure white color tokens or literal values in executable CSS/HTML."""
        violations = []
        # Strip CSS comments first so explanatory comments don't false-positive
        clean_css = re.sub(r"/\*.*?\*/", "", self.css_content, flags=re.DOTALL)

        white_patterns = [
            r"#ffffff\b",
            r"#fff\b",
            r"rgb\(\s*255\s*,\s*255\s*,\s*255\s*\)",
            r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*1(?:\.0)?\s*\)"
        ]
        for pattern in white_patterns:
            matches = re.finditer(pattern, clean_css, re.IGNORECASE)
            for m in matches:
                start = max(0, m.start() - 30)
                end = min(len(clean_css), m.end() + 30)
                snippet = clean_css[start:end].replace("\n", " ").strip()
                violations.append(f"CSS match '{m.group(0)}': ...{snippet}...")

        # Also check inline styles in HTML
        for tag in self.soup.find_all(True, style=True):
            style_attr = re.sub(r"/\*.*?\*/", "", tag["style"], flags=re.DOTALL)
            for pattern in white_patterns:
                if re.search(pattern, style_attr, re.IGNORECASE):
                    violations.append(f"Inline style tag <{tag.name}> style='{style_attr}'")

        return violations

    def has_pure_black(self) -> List[str]:
        """Detect any forbidden pure black color tokens or literal values in executable CSS/HTML."""
        violations = []
        clean_css = re.sub(r"/\*.*?\*/", "", self.css_content, flags=re.DOTALL)

        black_patterns = [
            r"#000000\b",
            r"#000\b",
            r"rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)",
            r"rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*1(?:\.0)?\s*\)"
        ]
        for pattern in black_patterns:
            matches = re.finditer(pattern, clean_css, re.IGNORECASE)
            for m in matches:
                start = max(0, m.start() - 30)
                end = min(len(clean_css), m.end() + 30)
                snippet = clean_css[start:end].replace("\n", " ").strip()
                violations.append(f"CSS match '{m.group(0)}': ...{snippet}...")

        for tag in self.soup.find_all(True, style=True):
            style_attr = re.sub(r"/\*.*?\*/", "", tag["style"], flags=re.DOTALL)
            for pattern in black_patterns:
                if re.search(pattern, style_attr, re.IGNORECASE):
                    violations.append(f"Inline style tag <{tag.name}> style='{style_attr}'")

        return violations

    def has_dispatcher_references(self) -> List[str]:
        """Strict check for any occurrence of dispatcher references."""
        violations = []
        dispatcher_regex = re.compile(r"диспетчер\w*", re.IGNORECASE)

        # 1. Check visible text in DOM (excluding style and script)
        soup_copy = BeautifulSoup(self.content, "html.parser")
        for s in soup_copy(["script", "style"]):
            s.decompose()
        visible_text = soup_copy.get_text()
        for m in dispatcher_regex.finditer(visible_text):
            start = max(0, m.start() - 30)
            end = min(len(visible_text), m.end() + 30)
            snippet = visible_text[start:end].replace("\n", " ").strip()
            violations.append(f"Visible DOM text: '...{snippet}...'")

        # 2. Check HTML attributes (e.g. onclick, title, aria-label)
        for tag in self.soup.find_all(True):
            for attr_name, attr_val in tag.attrs.items():
                val_str = str(attr_val)
                if dispatcher_regex.search(val_str):
                    violations.append(f"Tag <{tag.name}> attribute '{attr_name}=\"{val_str}\"'")

        # 3. Check JavaScript string literals
        js_matches = dispatcher_regex.finditer(self.js_content)
        for m in js_matches:
            start = max(0, m.start() - 40)
            end = min(len(self.js_content), m.end() + 40)
            snippet = self.js_content[start:end].replace("\n", " ").strip()
            violations.append(f"JS code: '...{snippet}...'")

        return violations

    def has_oxblood_or_burgundy(self) -> List[str]:
        """Strict check for any occurrence of forbidden Burgundy/Oxblood hex codes."""
        violations = []
        forbidden_hexes = [r"#7a2320\b", r"#5c2e2e\b", r"#631917\b", r"#4b2424\b"]
        for pattern in forbidden_hexes:
            for m in re.finditer(pattern, self.content, re.IGNORECASE):
                start = max(0, m.start() - 30)
                end = min(len(self.content), m.end() + 30)
                snippet = self.content[start:end].replace("\n", " ").strip()
                violations.append(f"Forbidden oxblood hex '{m.group(0)}': ...{snippet}...")
        return violations

    def has_square_brackets_in_ui(self) -> List[str]:
        """Check for square brackets [...] in visible UI copy."""
        violations = []
        soup_copy = BeautifulSoup(self.content, "html.parser")
        for s in soup_copy(["script", "style", "svg"]):
            s.decompose()
        visible_text = soup_copy.get_text()
        bracket_matches = re.finditer(r"\[([^\]]+)\]", visible_text)
        for m in bracket_matches:
            start = max(0, m.start() - 25)
            end = min(len(visible_text), m.end() + 25)
            snippet = visible_text[start:end].replace("\n", " ").strip()
            violations.append(f"Visible UI copy: '...{snippet}...'")
        return violations

    def get_img_tags(self) -> List[Any]:
        return self.soup.find_all("img")

    def find_rule_property(self, selector: str, property_name: str) -> List[str]:
        """Find property values for a given selector in CSS."""
        results = []
        escaped_sel = re.escape(selector)
        pattern = rf"{escaped_sel}\s*\{{([^}}]+)\}}"
        blocks = re.findall(pattern, self.css_content)
        for block in blocks:
            prop_pattern = rf"{re.escape(property_name)}\s*:\s*([^;]+);"
            matches = re.findall(prop_pattern, block)
            for m in matches:
                clean_val = re.sub(r"/\*.*?\*/", "", m).strip()
                results.append(clean_val)
        return results

    def execute_in_node(self, js_test_code: str, timeout_sec: int = 5) -> Dict[str, Any]:
        """Execute a JS test harness in Node.js with the file's JavaScript context."""
        harness = f"""
        try {{
            const storage = {{}};
            global.localStorage = {{
                getItem: (k) => storage[k] || null,
                setItem: (k, v) => {{ storage[k] = String(v); }},
                removeItem: (k) => {{ delete storage[k]; }},
                clear: () => {{ Object.keys(storage).forEach(k => delete storage[k]); }}
            }};
            global.window = {{
                location: {{ hash: '', href: '' }},
                innerWidth: 1024,
                innerHeight: 768,
                addEventListener: () => {{}},
                removeEventListener: () => {{}},
                scrollTo: () => {{}}
            }};
            global.navigator = {{
                vibrate: () => true
            }};
            global.document = {{
                getElementById: (id) => ({{
                    id,
                    style: {{}},
                    classList: {{
                        add: () => {{}},
                        remove: () => {{}},
                        contains: () => false,
                        toggle: () => {{}}
                    }},
                    innerHTML: '',
                    innerText: '',
                    value: '',
                    appendChild: () => {{}},
                    addEventListener: () => {{}},
                    setAttribute: () => {{}},
                    getAttribute: () => null,
                    querySelectorAll: () => [],
                    querySelector: () => null
                }}),
                querySelector: () => null,
                querySelectorAll: () => [],
                createElement: (tag) => ({{
                    tagName: tag,
                    style: {{}},
                    classList: {{ add: () => {{}}, remove: () => {{}} }},
                    appendChild: () => {{}},
                    setAttribute: () => {{}}
                }}),
                body: {{
                    appendChild: () => {{}},
                    style: {{}},
                    classList: {{
                        add: () => {{}},
                        remove: () => {{}},
                        contains: () => false,
                        toggle: () => {{}}
                    }}
                }}
            }};

            global.setInterval = () => {{}};
            global.clearInterval = () => {{}};
            global.setTimeout = (fn) => {{}};
            global.clearTimeout = () => {{}};
            global.requestAnimationFrame = () => {{}};

            // Embed file JS content
            {self.js_content}

            // Execute test assertion code
            const __test_run = () => {{
                {js_test_code}
            }};

            const __result = __test_run();
            console.log(JSON.stringify({{ success: true, result: __result }}));
            process.exit(0);
        }} catch (err) {{
            console.log(JSON.stringify({{ success: false, error: err.message, stack: err.stack }}));
            process.exit(0);
        }}
        """

        res = subprocess.run(
            ["node", "-e", harness],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )

        stdout = res.stdout.strip()
        if not stdout:
            return {"success": False, "error": f"Node empty output: {res.stderr}"}
        try:
            return json.loads(stdout)
        except Exception as e:
            return {"success": False, "error": f"JSON decode error on '{stdout}': {e}"}
