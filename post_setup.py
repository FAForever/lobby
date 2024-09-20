import pathlib
import sys


def remove_some_redundant_qt_files() -> None:
    current_dir = pathlib.Path(__file__).parent
    build_dir = current_dir / "build"
    app_dir, = build_dir.iterdir()
    app_qt6 = app_dir / "lib" / "PyQt6" / "Qt6"

    # cx_Freeze copies these into lib directory itself
    # and into every plugin directory for some reason
    libfiles = [file.name for file in (app_qt6 / "lib").iterdir()]

    # not all of them, but the most obvious and largest ones
    redundant_plugins_files = [
        "libffmpegmediaplugin.so",
        "libQt6Pdf.so.6",
        "libQt6Qml.so.6",
        "libQt6QmlModels.so.6",
        "libQt6Quick.so.6",
    ]

    plugins_dir = app_qt6 / "plugins"
    for plugin in plugins_dir.iterdir():
        for file in plugin.iterdir():
            if file.name in libfiles + redundant_plugins_files:
                print(f"Removing {file}...")
                file.unlink()


def main() -> None:
    if sys.platform == "win32":
        return
    remove_some_redundant_qt_files()


if __name__ == "__main__":
    raise SystemExit(main())
