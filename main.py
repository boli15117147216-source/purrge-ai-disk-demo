import sys
import argparse
from pathlib import Path

CACHE_EXT = {'.log', '.tmp', '.cache', '.DS_Store'}
LARGE_SIZE = 50 * 1024 * 1024

def ai_score(path: Path, size: int) -> tuple[str, str]:
    ext = path.suffix.lower()
    name = path.name.lower()
    if ext in CACHE_EXT or name.endswith('.log'):
        return 'high', '缓存/日志文件，通常可重建'
    if 'download' in str(path).lower() and size > LARGE_SIZE:
        return 'medium', '下载目录中的大文件，请确认'
    if size > 200 * 1024 * 1024:
        return 'low', '体积较大，建议人工确认'
    return 'skip', '未命中清理规则'

def scan(root: Path):
    items = []
    for p in root.rglob('*'):
        if p.is_file():
            try:
                size = p.stat().st_size
            except OSError:
                continue
            level, reason = ai_score(p, size)
            if level != 'skip':
                items.append((p, size, level, reason))
    return sorted(items, key=lambda x: x[1], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='Purrge Demo: AI-style disk cleanup assistant')
    parser.add_argument('path', nargs='?', default='.', help='directory to scan')
    parser.add_argument('--delete', action='store_true', help='actually delete selected files')
    args = parser.parse_args()
    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        sys.exit(f'Path not found: {root}')
    print(f'Scanning: {root}')
    items = scan(root)
    if not items:
        print('No cleanable items found.')
        return
    for i, (p, size, level, reason) in enumerate(items[:20], 1):
        print(f'{i:2}. [{level}] {size/1024/1024:.1f} MB {p}')
        print(f'    AI: {reason}')
    choice = input('Enter numbers to delete (comma-separated), or press Enter to cancel: ').strip()
    if not choice:
        print('Cancelled.')
        return
    indexes = {int(x) for x in choice.split(',') if x.strip().isdigit()}
    selected = [items[i-1] for i in indexes if 1 <= i <= len(items)]
    for p, size, _, _ in selected:
        if args.delete:
            try:
                p.unlink()
                print(f'Deleted: {p}')
            except OSError as e:
                print(f'Failed: {p} ({e})')
        else:
            print(f'[DRY-RUN] Would delete: {p}')
    print('Done. Use --delete to actually remove files.')

if __name__ == '__main__':
    main()