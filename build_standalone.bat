echo exec "conda activate base" before
python -m nuitka --standalone --follow-imports --nofollow-import-to=tkinter --windows-console-mode=disable --enable-plugin=pyqt6 --assume-yes-for-downloads IonogramViewer2.py
rmdir /q /s IonogramViewer2.build
ren IonogramViewer2.dist IonogramViewer2
xcopy ui IonogramViewer2\ui /e /i /h
xcopy data IonogramViewer2\data /e /i /h
xcopy examples IonogramViewer2\examples /e /i /h
