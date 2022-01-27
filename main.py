import base64
import datetime
import hashlib
import os
import subprocess
from tkinter import filedialog
from zipfile import ZipFile
from sympy.utilities.decorator import public
import rsa
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

qtCreatorFile = "ELGUI.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class GUICKO(QMainWindow, Ui_MainWindow): 

    fileName = None
    publicKey = None
    privateKey = None
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')

    def msgBox(self, title, text, error=False):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        if error:
            msg.setIcon(QMessageBox.Critical)
        msg.exec_()

    def browseFile(self):
        self.fileName, _ = QFileDialog.getOpenFileName(self, 'Choose File To Sign', '',
                                                       'All Files (*)', options=self.options)
        self.printFileStats()

    def browsePublicKey(self):
        self.publicKey, _ = QFileDialog.getOpenFileName(self, 'Select Public Key', '',
                                                        'Public Key Files (*.pub)', options=self.options)
        self.public_key_path.setText(f'Path: {self.publicKey}')

    def browsePrivateKey(self):
        self.privateKey, _ = QFileDialog.getOpenFileName(self, 'Select Private Key', '',
                                                         'Private Key Files (*.priv)', options=self.options)
        self.private_key_path.setText(f'Path: {self.privateKey}')

    def printFileStats(self):
        if not self.fileName: return
        self.file_path.setText(f'Path: {self.fileName}')
        stats = os.stat(self.fileName)

        self.file_name.setText(f'Name:\t\t{os.path.basename(self.fileName)}')
        self.file_type.setText(f'Type:\t\t{os.path.splitext(self.fileName)[1]}')
        self.file_size.setText(f'Size:\t\t{stats.st_size} B')
        timeCreated = datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%d/%m/%Y %H:%M:%S')
        self.file_created.setText(f'Created:\t\t{timeCreated}')
        timeLastM = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
        self.file_lastm.setText(f'Last modified:\t{timeLastM}')
        timeLastOP = datetime.datetime.fromtimestamp(stats.st_atime).strftime('%d/%m/%Y %H:%M:%S')
        self.file_lastop.setText(f'Last opened:\t{timeLastOP}')

    def generateKeys(self, nameOfFile=None, dirPath=None, showMsgBox=True, openFileExplorer=True):
        if not dirPath:
            dirPath = QFileDialog.getExistingDirectory(self, 'Select Directory To Save Files',
                                                       options=self.options | QFileDialog.ShowDirsOnly)
            if not dirPath: return

        if not nameOfFile:
            privFileName = dirPath + f'/privateKey.priv'
            pubFileName = dirPath + f'/publicKey.pub'
        else:
            privFileName = dirPath + f'/{nameOfFile}.priv'
            pubFileName = dirPath + f'/{nameOfFile}.pub'

        keys = rsa.generateKey()
        base64_privKey = self.dobase64(str(keys['e']) + ' ' + str(keys['n']))
        base64_pubKey = self.dobase64(str(keys['d']) + ' ' + str(keys['n']))

        with open(privFileName, 'w') as file:
            file.write('RSA ' + base64_privKey)
        with open(pubFileName, "w") as file:
            file.write('RSA ' + base64_pubKey)

        if showMsgBox:
            self.msgBox('Success!!!', 'Keys generated!')
        if openFileExplorer:
            try:
                subprocess.run([self.FILEBROWSER_PATH, os.path.normpath(dirPath)])
            except:
                pass

        return keys

    def sign(self):
        if not self.fileName : return
        nameOfFile = os.path.basename(self.fileName).split('.')[0]

        dirPath = QFileDialog.getExistingDirectory(self, 'Select Directory To Save Files',
                                                   options=self.options | QFileDialog.ShowDirsOnly)
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
        try:
            subprocess.run([self.FILEBROWSER_PATH, os.path.normpath(dirPath)])
        except:
            pass

    def check_sign(self):
        if not self.publicKey: return
        zipFileName, _ = QFileDialog.getOpenFileName(self, 'Select .zip File', '', 'ZIP Files (*.zip)',
                                                     options=self.options)
        if not zipFileName: return

        with ZipFile(zipFileName, 'r') as zipObj:
            if len(zipObj.namelist()) != 2:
                self.msgBox('Aborted!!!', 'Not the right .zip file!!!', True)
                return
            for file in zipObj.namelist():
                if file.endswith('.sign'): signFileName = file
                if not file.endswith('.sign'): fileName = file
            if not signFileName or not fileName:
                self.msgBox('Aborted!!!', 'Not the right .zip file!!!', True)
                return
            signContent = self.undoBase64(zipObj.read(signFileName).split()[1])
            fileContentHash = hashlib.sha3_512(zipObj.read(fileName)).hexdigest()

        with open(self.publicKey, 'rb') as file:
            fileContent = file.read().split()[1]
        keys = self.undoBase64(fileContent).split()
        content = rsa.desifruj(int(keys[0]), int(keys[1]), signContent)

        if content == fileContentHash:
            self.msgBox('Match!!!', 'Signature match the file!')
        else:
            self.msgBox('Not a Match!!!', 'Signature doesnt match the file!', True)

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
        self.pushButton_check_sign.clicked.connect(self.check_sign)
        self.pushButton_genKeys.clicked.connect(self.generateKeys)

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUICKO()
    window.show()
    sys.exit(app.exec_())