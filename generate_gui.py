import pyqt5ac

pyqt5ac.main(uicOptions='--from-imports', force=False, ioPaths=[
    ['src/py_cfd_2/gui/*.ui', 'src/py_cfd_2/generated/%%FILENAME%%_ui.py'],
    ['src/py_cfd_2/basic_geometries/gui_adaptions/infos/gui/*.ui', 'src/py_cfd_2/basic_geometries/gui_adaptions/infos/generated/%%FILENAME%%_ui.py'],
    ['src/py_cfd_2/resources/*.qrc', 'src/py_cfd_2/generated/%%FILENAME%%_rc.py'],
    ['src/py_cfd_2/resources/*.qrc', 'src/py_cfd_2/basic_geometries/gui_adaptions/infos/generated/%%FILENAME%%_rc.py'],
    ['modules/*/*.ui', '%%DIRNAME%%/generated/%%FILENAME%%_ui.py'],
    ['modules/*/resources/*.qrc', '%%DIRNAME%%/generated/%%FILENAME%%_rc.py']
])