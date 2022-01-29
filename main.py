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

    def msgBox(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.exec_()

    def browsePublicKey(self):
        self.publicKey, _ = QFileDialog.getOpenFileName(
            self, 'Vyber verejný klúč', '','(*.pub)'
        )
        if not self.fileName: return

        self.public_key_path.setText(f'{self.publicKey}')

    def browsePrivateKey(self):
        self.privateKey, _ = QFileDialog.getOpenFileName(
            self, 'Vyber privatny kluč', '','(*.priv)'
        )
        if not self.privateKey: return

        self.private_key_path.setText(f'{self.privateKey}')

    def generateKeys(self, savePath):

        savePath = QFileDialog.getExistingDirectory(self, 'vyber složky pre uloženie súboru',)
        if not savePath: return

        keys = rsa.generateKey()
        klucE = str(keys['e'])
        klucN = str(keys['n'])
        klucD = str(keys['d'])

        privKluc = klucE + ' ' + klucN
        base64klucP = base64.b64encode(privKluc.encode('ascii'))
        b64klucP = str(base64klucP.decode('ascii'))

        verKluc = klucD + ' ' + klucN
        base64klucV = base64.b64encode(verKluc.encode('ascii'))
        b64klucV = str(base64klucV.decode('ascii'))

        privatnyKlucMeno = savePath + f'/privateKey.priv'
        with open(privatnyKlucMeno, 'w') as file:
            file.write('RSA ' + b64klucP)
        
        verejnyKlucMeno = savePath + f'/publicKey.pub'
        with open(verejnyKlucMeno, "w") as file:
            file.write('RSA ' + b64klucV)

        self.msgBox('Keys generated!')

        return keys

    def sign(self):

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
        if not self.fileName : return

        dirPath = QFileDialog.getExistingDirectory(self, 'Select Directory To Save Files',)
        if not dirPath: return

        nameOfFile = os.path.basename(self.fileName)
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

        self.msgBox('Electronic signature generated!')


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
        self.pushButton_browsePubKey.clicked.connect(self.browsePublicKey)
        self.pushButton_browsePrivKey.clicked.connect(self.browsePrivateKey)
        self.pushButton_sign.clicked.connect(self.sign)
        self.pushButton_genKeys.clicked.connect(self.generateKeys)

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUICKO()
    window.show()
    sys.exit(app.exec_())