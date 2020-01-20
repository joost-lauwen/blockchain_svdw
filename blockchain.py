import datetime
import hashlib
import json
import requests
from urllib.parse import urlparse

class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.createBlock(proof = 1, prevHash = '0')
        self.nodes = set()

    def createBlock(self, proof, prevHash):
        block = {'index': len(self.chain) + 1,
                'timestamp': str(datetime.datetime.now()),
                'proof': proof,
                'prevHash': prevHash,
                'transactions': self.transactions
                 }

        # Possibility to implemtent persistancy
        self.transactions = []
        self.chain.append(block)

        return block

    def getPrevBlock(self):
        return self.chain[-1]

    def proofOfWork(self, prevProof):
        newProof = 1
        checkProof = False

        while checkProof is False:
            hashOperation = hashlib.sha256(str(newProof**2 - prevProof**2).encode()).hexdigest()
            if hashOperation[:4] == '0000':
                checkProof = True
            else:
                newProof += 1
        
        return newProof

    def hash(self, block):
        encodedBlock = json.dumps(block, sort_keys= True).encode()

        return hashlib.sha256(encodedBlock).hexdigest()

    def isChainValid(self, chain):
        prevBlock = chain[0]
        blockIndex = 1
        
        while blockIndex < len(chain):
            block = chain[blockIndex]

            if block['prevHash'] != self.hash(prevBlock):
                return False

            prevProof = prevBlock['proof']
            proof = block['proof']
            hashOperation = hashlib.sha256(str(proof**2 - prevProof**2).encode()).hexdigest()

            if hashOperation[:4] != '0000':
                return False
            
            prevBlock = block
            blockIndex += 1
        
        return True

    # Change variables to something for a voting system?
    def addTransaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                'receiver': receiver,
                                'amount': amount})

        previousBlock = self.getPrevBlock()

        return previousBlock['index'] + 1

    def addNode(self, address):
        parsedUrl = urlparse(address)
        self.nodes.add(parsedUrl.netloc)

    def replaceChain(self):
        network = self.nodes
        longestChain = None
        maxLength = len(self.chain)

        for node in network:
            response = requests.get(f'http://{node}/getChain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > maxLength and self.isChainValid(chain):
                    maxLength = length
                    longestChain = chain
        if longestChain:
            self.chain = longestChain
            return True
        return False