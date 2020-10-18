# !!! MIGRATED ON https://gitlab.com/OlivierMonteil/custom_script_editor !!!

## custom_script_editor
Maya's script editor customization (synthax highlighter, snippets system and hotkeys).

### Usage
Make sure this package is available for Maya (into Maya's script folder, or into
some folder added to `MAYA_SCRIPT_PATH`).
Add the following line to Maya's `userSetup.mel` script file, and the Script Editor
should be customized at startup :

`python("from custom_script_editor import main as cse_main\ncse_main.run()");`

**Warning:** Sometimes the Custom Menu added to the Script Editor's hotbox may not appear properly.
Switching tab should add it back.

### Features
- synthax highlight for MEL and Python tabs.
- synthax highlight for Script Editor's console.

- multi-line editing (add cursors on `Ctrl +LMB`, work in progress).
- snippets (auto-completion) manager (for now, not compatible with the multi-line editing).
- text blocks collapse/expand (work in progress)

- some useful hotkeys:
    - `Ctrl +Shift +D` : lines duplication
    - `Ctrl +Alt +UP/DOWN` : add new multi-cursor up/down
    - `Ctrl +/` : toggle blocks comment
    - `Ctrl +UP/DOWN` : move lines
    - `Ctrl +V` : (multi-paste enabled)
    - embracing characters : `()`, `{}`, `[]`, ` `` `, `""`, `''`

- some tools are also available in the Script Editor's hotbox menu:
    - Toggle Word-wrap on console
    - Toggle Snippets on tabs
    - Palette editing (wip)
    - dir() navigation tool
    - regex tool (wip, QRegex only for now)

TO DO :
    - `Tab` key with multi-editing
    - `Enter`/`Return` key with multi-editing
    - `Home` key (go to the start of the indented line)
    - Increment digits on multi-cursors (`Ctrl +digit`)
    - Palette editor commands, colors link
    - `re` module regex match (Regex Simulator)
    - Remove escape highlights on `r''` string (Python)
    - Improve Search/Replace
    - Linter?
