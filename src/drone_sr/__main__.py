"""Phase 01 entry point: process one image in input/."""

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Upscale one image from input/ into output/.")
    parser.parse_args()
    print("Drone Image Super-Resolution")
    input_directory = Path("input")
    output_directory = Path("output")
    if not input_directory.is_dir():
        print("Input directory not found or not a directory: input/")
        return 1
    if input_directory.resolve() == output_directory.resolve():
        print("Input and output directories must be different")
        return 1
    extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    images = sorted(
        (path for path in input_directory.iterdir() if path.is_file() and path.suffix.lower() in extensions),
        key=lambda path: (path.name.casefold(), path.name),
    )
    if not images:
        print("No supported images found in input/")
        return 0
    if len(images) != 1:
        print(f"Phase 01 expects exactly one supported image in input/; found {len(images)}")
        return 1

    from .image_io import read_image, write_png
    from .inference import load_model, upscale

    try:
        descriptor = load_model()
    except Exception as error:
        print(str(error))
        return 1
    print(f"Device: {descriptor.device}")
    print("Model: loaded")
    print("Images: 1")
    source = images[0]
    destination = output_directory / f"{source.stem}.png"
    try:
        result = upscale(read_image(source), descriptor)
        write_png(result, destination, source)
    except Exception as error:
        print(f"[1/1] {source.name} — Failed: {error}")
        failed = 1
    else:
        print(f"[1/1] {source.name}")
        failed = 0
    print("Finished")
    print(f"Processed: {1 - failed}")
    print(f"Failed: {failed}")
    print("Output: output/")
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
