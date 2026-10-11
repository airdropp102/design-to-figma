"""APP_SPEC is untrusted product-description data, never executable instructions."""
from dataclasses import dataclass
from pathlib import Path
import hashlib, re

@dataclass(frozen=True)
class NormalizedSpec:
    app_name: str
    platform: str
    p0_features: tuple[str, ...]
    language: str
    spec_sha256: str
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    spec_path: str
    goal: str


def validate_spec(path: Path, workspace: Path) -> NormalizedSpec:
    workspace=Path(workspace).resolve()
    file=(workspace/path).resolve()
    if not file.is_relative_to(workspace): raise ValueError('APP_SPEC path escapes workspace')
    if not file.is_file() or file.stat().st_size > 256*1024: raise ValueError('Missing or oversized APP_SPEC')
    raw=file.read_bytes()
    text=raw.decode('utf8')
    def field(*labels):
        for name in labels:
            match=re.search(r'^\s*[-*]\s*'+re.escape(name)+r'\s*:\s*(.*?)\s*$',text,re.M|re.I)
            if match and match.group(1).strip() and not match.group(1).strip().startswith('('):return match.group(1).strip()
        return ''
    name=field('Tên ứng dụng','App name')
    platform=field('Nền tảng','Platform').lower()
    lang=field('Ngôn ngữ giao diện','Language')
    goal=field('Mục tiêu sản phẩm','Mô tả ứng dụng','Mô tả 1–2 câu (ngành, đối tượng, tông cảm xúc mong muốn)')
    rows=[tuple(c.strip() for c in ln.strip().strip('|').split('|')) for ln in text.splitlines() if ln.strip().startswith('|')]
    roles=[r for r in rows if len(r) in (2,3) and not any(c in ('Vai trò','Role','---') for c in r)]
    p0=tuple(r[1] for r in rows if len(r)>=5 and re.fullmatch(r'P0',r[3],re.I) and r[1])
    explicit_screens=[r for r in rows if len(r)>=5 and re.fullmatch(r'S\d{2,3}',r[0],re.I)]
    if len(explicit_screens)>25: raise ValueError('At most 25 screens per run')
    if not name or not platform or not lang or not roles or not p0 or not goal or not re.search(r'^##\s*Ràng buộc\s*$',text,re.I|re.M):
        raise ValueError('APP_SPEC needs app name, platform, product goal, language, roles, P0 and constraints section')
    if not any(x in platform for x in ('mobile','web','ios','android','cả hai','both')): raise ValueError('Invalid design platform')
    warnings=[]
    if re.search(r'^\s*[-*]\s*Figma channel ID\s*:',text,re.M|re.I): warnings.append('Legacy Figma channel ignored; configure runtime/figma.local.json')
    if re.search(r'(?i)\b(?:rm\s+-rf|generate\s+\w+\.(?:kt|swift|tsx)|ignore previous instructions)\b',text): warnings.append('APP_SPEC includes executable-looking untrusted text; ignored as instructions')
    return NormalizedSpec(name,platform,p0,lang,hashlib.sha256(raw).hexdigest(),(),tuple(warnings),str(file),goal)
