python -m PyInstaller ^
--distpath "%cd%/Output/dist" ^
--workpath "%cd%/Output/build" ^
--noconfirm ^
--onedir ^
--windowed ^
--add-data "C:\Users\1589l\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\customtkinter;customtkinter/" ^
--icon "%cd%/assets/icon.ico" ^
--add-data "%cd%/assets/icon.ico;."  "%cd%/app.pyw" ^
--add-data "%cd%/assets;assets/"

pause