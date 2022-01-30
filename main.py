import base64
import datetime
import hashlib
import os
import rsa
from zipfile import ZipFile
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

qtCreatorFile = "ELGUI.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class GUICKO(QMainWindow, Ui_MainWindow): 

    def vysOkno(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.exec_()

    def tvorbaKluc(self, savePath):

        savePath = QFileDialog.getExistingDirectory(self, 'vyber složky pre uloženie súboru',)
        if not savePath: return

        kluce = rsa.generateKey()
        klucE = str(kluce['e'])
        klucN = str(kluce['n'])
        klucD = str(kluce['d'])

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

        self.vysOkno('Kluce vygenerovane ')

        return kluce

    def podpis(self):

        self.nazov, _ = QFileDialog.getOpenFileName(
            self, 'Vyber subor', '','(*)'
        )
        if not self.nazov: return

        info = os.stat(self.nazov)
        time = datetime.datetime.fromtimestamp(info.st_ctime).strftime('%d/%m/%Y %H:%M')
        posUpravaTime = datetime.datetime.fromtimestamp(info.st_mtime).strftime('%d/%m/%Y %H:%M')
        
        self.cesta_suboru.setText(f'{self.nazov}')
        self.nazov_suboru.setText(f'Názov:{os.path.basename(self.nazov)}')
        self.typ_suboru.setText(f'Typ:{os.path.splitext(self.nazov)[1]}')
        self.sub_velkost.setText(f'Velkosť:{os.path.getsize(self.nazov)}')
        self.vytvorenie.setText(f'Vytvorenie:{time}')
        self.suborPosledna.setText(f'Posledna uprava:{posUpravaTime}')
        if not self.nazov : return

        saveP = QFileDialog.getExistingDirectory(self, 'Vyber priecinok pre ulozenie',)
        if not saveP: return

        self.privatnyKluc, _ = QFileDialog.getOpenFileName(
            self, 'Vyber privatny kluč', '','(*.priv)'
        )
        if not self.privatnyKluc: return

        self.private_key_path.setText(f'{self.privatnyKluc}')

        with open(self.privatnyKluc, 'rb') as file:
                fileContent = file.read().split()[1]
        text_b = base64.b64decode(fileContent)
        text_b = text_b.decode('ascii')
        keysArray = text_b.split()
        keys = {'e': int(keysArray[0]), 'n': int(keysArray[1])}

        with open(self.nazov, 'rb') as file:
            x = file.read()
            hashText = hashlib.sha3_512(x).hexdigest()
        sifText = rsa.sifruj(keys['e'], keys['n'], hashText)
        bas64Text = base64.b64encode(sifText.encode('ascii'))
        bas64Text = bas64Text.decode('ascii')

        nazovZipFile = os.path.basename(self.nazov)
        zipFileName = saveP + f'/{nazovZipFile}.zip'

        with ZipFile(zipFileName, 'w') as zipObj:
            with open(self.nazov, 'rb') as file:
                naz = os.path.basename(self.nazov)
                zipObj.writestr(naz, file.read())
            zipObj.writestr(nazovZipFile + '.sign', 'RSA_SHA3-512 ' + bas64Text)

        self.vysOkno('Electronic podpis vytvoreny')

    def overenie(self):

        self.verejnyKluc, _ = QFileDialog.getOpenFileName(
            self, 'Vyber verejný klúč', '','(*.pub)'
        )
        if not self.verejnyKluc: return

        self.public_key_path.setText(f'{self.verejnyKluc}')

        nazovZipFile, _ = QFileDialog.getOpenFileName(self, 'Vyber subor s priponou .zip', '', '(*.zip)')
        if not nazovZipFile: return

        with ZipFile(nazovZipFile, 'r') as zipObj:

            if len(zipObj.namelist()) != 2:
                self.vysOkno( 'Nesprávny format zipFile', True)
                return

            for obj in zipObj.namelist():

                if obj.endswith('.sign'): podFile = obj

                if not obj.endswith('.sign'): fileOnl = obj

            if not podFile or not fileOnl:
                self.vysOkno('Nesprávny format zipFile', True)
                return
            textik = base64.b64decode(zipObj.read(podFile).split()[1])
            textik = textik.decode('ascii')
            signContent = textik


            sif = hashlib.sha3_512(zipObj.read(fileOnl)).hexdigest()

        with open(self.verejnyKluc, 'rb') as obj:
            fileContent = obj.read().split()[1]
        kluceH = base64.b64decode(fileContent)
        kluceH = kluceH.decode('ascii')
        keys = kluceH.split()
    
        desif = rsa.desifruj(int(keys[0]), int(keys[1]), signContent)

        if desif == sif:
            self.vysOkno('Podpis sa zhoduje!')
        else:
            self.vysOkno('Podpis sa nezhoduje')

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.signBut.clicked.connect(self.podpis)
        self.checkBut.clicked.connect(self.overenie)
        self.generate.clicked.connect(self.tvorbaKluc)

     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GUICKO()
    window.show()
    sys.exit(app.exec_())