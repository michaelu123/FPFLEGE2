# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew

block_cipher = None


a = Analysis(['..\\src\\main.py'],
             pathex=['..\\venv\\lib\\site-packages'],
             binaries=[],
             datas=[
                ("../venv/Lib/site-packages/kivymd/fonts", "kivymd/fonts"),
                ("../venv/Lib/site-packages/kivymd/images", "kivymd/images"),
             ],
             hiddenimports=["plyer.platforms.win.filechooser","kivymd.icon_definitions", "kivymd.uix.boxlayout","kivymd.uix.toolbar"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='fpflege',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
