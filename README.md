# custom_script_editor
Maya's script editor customization (synthax highlighter, snippets system and hotkeys).

## Usage
Make sure this package is available for Maya (into Maya's script folder, or into
some folder added to `MAYA_SCRIPT_PATH`).
Add the following line to Maya's `userSetup.mel` script file, and the Script Editor
should be customized at startup :

`python("from custom_script_editor import main as cse_main\ncse_main.run()");`

Sometimes the Custom Menu added to the Script Editor's hotbox may not appear properly.
Switching tab should add it back.

WIP : the Palette Editor is in progress.
