
rmdir /q /s IonogramViewer2.build
rmdir /q /s IonogramViewer2.dist
rmdir /q /s IonogramViewer2

python --version
python -m nuitka ^
  --standalone ^
  --windows-console-mode=disable ^
  --enable-plugin=pyside6 ^
  --assume-yes-for-downloads ^
  --include-data-dir=images=images ^
  --windows-icon-from-ico=images/IonogramViewer2_icon.png ^
  --windows-company-name=IION ^
  --windows-product-name=IonogramViewer2 ^
  --windows-product-version=1.7.2 ^
  --windows-file-description="A program for scaling ionograms." ^
  --no-deployment-flag=self-execution ^
  IonogramViewer2.py

md IonogramViewer2

xcopy IonogramViewer2.dist IonogramViewer2 /e /i /h
xcopy data IonogramViewer2\data /e /i /h
xcopy examples IonogramViewer2\examples /e /i /h

python utils/make_html.py README.md IonogramViewer2\Readme.html

rmdir /q /s IonogramViewer2.build
rmdir /q /s IonogramViewer2.dist
