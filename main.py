import base64
import datetime
import hashlib
import os
import subprocess
import rsa
from threading import Timer
from tkinter import filedialog
from zipfile import ZipFile
from sympy.utilities.decorator import public
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

qtCreatorFile = "ELGUI.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class GUICKO(QMainWindow, Ui_MainWindow): 

    fileName = ''
    publicKey = None
    privateKey = None
    FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')

    def msgBox(self, title, text):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec_()

    def browseFile(self):
        self.fileName, _ = QFileDialog.getOpenFileName(
            self, 'Vyber subor', '','(*)'
        )
        if not self.fileName: return

        self.file_path.setText(f'{self.fileName}')
        self.file_name.setText(f'Name:{os.path.basename(self.fileName)}')
        self.file_type.setText(f'Type:{os.path.splitext(self.fileName)[1]}')
        self.file_size.setText(f'Size:{os.path.getsize(self.fileName)}')
        self.file_created.setText(f'Created:{os.path.getctime(self.fileName)}')
        self.file_lastm.setText(f'Last modified:{os.path.getmtime(self.fileName)}')

    def browsePublicKey(self):
        self.publicKey, _ = QFileDialog.getOpenFileName(
            self, 'Vyber verejný klúč', '','(*.pub)'
        )
        if not self.fileName: return
        self.public_key_path.setText(f'{self.publicKey}')

    def browsePrivateKey(self):
        self.privateKey, _ = QFileDialog.getOpenFileName(
            self, 'Select Private Key', '','(*.priv)'
        )
        if not self.fileName: return
        self.private_key_path.setText(f'{self.privateKey}')

    def generateKeys(self, dirPath, showMsgBox=True):

        dirPath = QFileDialog.getExistingDirectory(self, 'vyber složky pre uloženie súboru',)
        if not dirPath: return

        privFileName = dirPath + f'/privateKey.priv'
        pubFileName = dirPath + f'/publicKey.pub'

        keys = rsa.generateKey()
        base64_privKey = self.dobase64(str(keys['e']) + ' ' + str(keys['n']))
        base64_pubKey = self.dobase64(str(keys['d']) + ' ' + str(keys['n']))

        with open(privFileName, 'w') as file:
            file.write('RSA ' + base64_privKey)
        with open(pubFileName, "w") as file:
            file.write('RSA ' + base64_pubKey)

        if showMsgBox:
            self.msgBox('Success!!!', 'Keys generated!')

        return keys

    def sign(self):
        if not self.fileName : return
        nameOfFile = os.path.basename(self.fileName)

        dirPath = QFileDialog.getExistingDirectory(self, 'Select Directory To Save Files',)
        if not dirPath: return

        zipFileName = dirPath + f'/{nameOfFile}.zip'

        with open(self.privateKey, 'rb') as file:
                fileContent = file.read().split()[1]
        keysArray = self.undoBase64(fileContent).split()
        keys = {'e': int(keysArray[0]), 'n': int(keysArray[1])}

        with open(self.fileName, 'rb') as file:
            hashText = hashlib.sha3_512(file.read()).hexdigest()
        encodedText = rsa.sifruj(keys['e'], keys['n'], hashText)
        base64_text = self.dobase64(encodedText)

        with ZipFile(zipFileName, 'w') as zipObj:
            with open(self.fileName, 'rb') as file:
                zipObj.writestr(os.path.basename(self.fileName), file.read())
            zipObj.writestr(nameOfFile + '.sign', 'RSA_SHA3-512 ' + base64_text)

        self.msgBox('Success!!!', 'Electronic signature generated!')


    def dobase64(self, text):
        base64_b = base64.b64encode(text.encode('ascii'))
        return base64_b.decode('ascii')

    def undoBase64(self, text):
        text_b = base64.b64decode(text)
        return text_b.decode('ascii')

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pushButton_browseFile.clicked.connect(self.browseFile)
        self.pushButton_browsePubKey.clicked.connect(self.browsePublicKey)
        self.pushButton_browsePrivKey.clicked.connect(self.browsePrivateKey)
        self.pushButton_sign.clicked.connect(self.sign)
        self.pushButton_genKeys.clicked.connect(self.generateKeys)

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUICKO()
    window.show()
    sys.exit(app.exec_())