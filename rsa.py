import sympy
import random
import unidecode
from sympy.core.evalf import N

def genPrimeNum():
    return sympy.randprime(1*(10**12), (1*10**13))

def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def modInverse(a, m):
    j = m
    x = 1
    y = 0 
    if (m == 1): 
        return 0

    while (a > 1):
        q = a // m
        t = m
        m = a % m
        a = t
        t = y
        y = x - q * y
        x = t
        
    if (x < 0):
        x += j
    return x

def generateKey():
    kluce = {}
    p = genPrimeNum()
    q = genPrimeNum()

    n = p * q

    phi = (p-1) * (q-1)

    e = 0
    index = 0
    while index != 1:
        e = random.randrange(1, phi)
        index = gcd(e, phi)
    d = modInverse(e, phi)

    kluce = {'d': d, 'e': e, 'n': n}
    return kluce

def rozdelenie(vstup, pocet):
    part = []
    for i in range(0,len(vstup),pocet):
        part.append(vstup[i:i + pocet])
    return part

def binToDec(number):
    x = int(number,2)
    return x
    
def decToBin(number,pos):
    x = bin(number).replace("0b","").zfill(pos)
    return x

def sifruj(e,n, vstupText):
    vstupText = unidecode.unidecode(vstupText)
    
    text = rozdelenie(vstupText,5)
    
    sifrovanyText = ''
    bpart = ''
    chars = []
    bchars = []

    for part in text:   
        for char in part:
            chars.append(ord(char))
        
        #print(chars)

        for bchar in chars:
            bchars.append(decToBin(bchar,12))
        
        #print(bchars)
        
        bpart = ''.join(bchars)
        number = binToDec(bpart)
        sifra = pow(number, e,n)
        sifrovanyText = sifrovanyText + str(sifra)
        sifrovanyText = sifrovanyText + " "
        bchars.clear()
        chars.clear()
    
    # print(text)
    # print(chars)
    # print(bchars)
    # print(number)
    return sifrovanyText
    
def asciiToChar(vstup):
    return''.join(chr(i) for i in vstup)  

def desifruj(d,n, sifrovanyText):
    text = []
    text = sifrovanyText.split()
    desifrovanyText = ''
    bchars = []
    chars = []

    for part in text:
        number = int(part)
        desifra = pow(number,d,n)

        bpart = decToBin(desifra,60)
        #print(bpart)
        bchars = rozdelenie(bpart,12)
        #print(bchars)
        for bchar in bchars:
            #print(bchar)
            bnum = binToDec(bchar)
            #print(bnum)
            if bnum != 0:
                chars.append(bnum)
                #print(bnum)
        #print(chars)
        desifrovanyText = desifrovanyText + asciiToChar(chars)
        #print(desifrovanyText)
        bchars.clear()
        chars.clear()
          
    #print(desifrovanyText)    
    return desifrovanyText