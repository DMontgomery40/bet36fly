"""Build contact sheets only from scenes in the current export timeline."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def frame_paths(root, phase):
    timeline = json.loads((root / 'timeline.json').read_text())
    return [root / f'qa/frames/{scene["id"]:02}-{phase}.jpg' for scene in timeline['scenes']]


def main():
    font = ImageFont.truetype('/System/Library/Fonts/Avenir Next.ttc', 22)
    for phase in ['early', 'mid', 'late']:
        files = frame_paths(ROOT, phase)
        for batch in range(0, len(files), 6):
            sheet = Image.new('RGB', (1280, 1170), (10, 17, 24))
            draw = ImageDraw.Draw(sheet)
            for index, path in enumerate(files[batch:batch+6]):
                x, y = (index % 2) * 640, (index // 2) * 390
                with Image.open(path) as source:
                    sheet.paste(source.resize((640, 360)), (x, y))
                draw.text((x+12, y+361), path.stem, font=font, fill='white')
            sheet.save(ROOT / f'qa/{phase}-{batch//6+1}.jpg', quality=92)


if __name__ == '__main__':
    main()
