call conda activate base
python --version
python -m nuitka ^
  --standalone ^
  --onefile ^
  --windows-console-mode=disable ^
  --enable-plugin=pyside6 ^
  --assume-yes-for-downloads ^
  --include-data-dir=images=images ^
  --windows-icon-from-ico=images/IonogramViewer2_icon.png ^
  --windows-company-name=IION ^
  --windows-product-name=IonogramViewer2 ^
  --windows-product-version=1.7.0 ^
  --windows-file-description="A program for scaling ionograms." ^
  IonogramViewer2.py

rmdir /q /s IonogramViewer2.build
rmdir /q /s IonogramViewer2.dist
rmdir /q /s IonogramViewer2.onefile-build
rmdir /q /s IonogramViewer2

md IonogramViewer2
move IonogramViewer2.exe IonogramViewer2\IonogramViewer2.exe
copy README.md IonogramViewer2\README.md
xcopy data IonogramViewer2\data /e /i /h
xcopy examples IonogramViewer2\examples /e /i /h
