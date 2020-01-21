# Name: Joost Lauwen
# Module: Blockchain
# Date: 20-01-2019

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
import pickle

class Blockchain:

    def __init__(self):
        self.chain = []
        self.blocksInChain = []
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

    def addTransaction(self, sender, receiver, vote):
        self.transactions.append({'sender': sender,
                                'receiver': receiver,
                                'vote': vote})

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

    def persistBlock(self, block):
        self.blocksInChain.append(block)
        blockData = 'blockchainData'

        newBlockData = open(blockData, 'wb')
        pickle.dump(self.blocksInChain,newBlockData)
        newBlockData.close()

# The code below is just for the teachers to show that the chain is being persisted in the pickle file
        infile = open(blockData, 'rb')
        newerBlockData = pickle.load(infile)
        infile.close()

        print(newBlockData)
        print(newerBlockData)
       
#---------------------------------------------------------------------#

app = Flask(__name__)

# Create address for node on Port 5000
nodeAddress = str(uuid4()).replace('-', '')

blockchain = Blockchain()

@app.route('/mineBlock', methods = ['GET'])

def mineBlock():
    prevBlock = blockchain.getPrevBlock()
    prevProof = prevBlock['proof']
    proof = blockchain.proofOfWork(prevProof)
    prevHash = blockchain.hash(prevBlock)

    # make the vote data variable
    blockchain.addTransaction(sender = nodeAddress, receiver = 'Keeper', vote = "Joost") 
    block = blockchain.createBlock(proof, prevHash)
    blockchain.persistBlock(block)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'prevHash': block['prevHash'],
                'transactions': block['transactions']
                }
    
    return jsonify(response), 200

@app.route('/getChain', methods = ['GET'])

def getChain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)
                }
    return jsonify(response), 200

@app.route('/isValid', methods = ['GET'])

def isValid():
    isValid = blockchain.isChainValid(blockchain.chain)

    if isValid:
        response = {'message': 'All good. The blockchain is valid'}
    else:
        response = {'message': 'The blockchain is not valid'}
        
    return jsonify(response), 200

@app.route('/addTransaction', methods = ['POST'])

def addTransaction():
    json = request.get_json()
    transactionKeys = ['sender', 'receiver', 'vote']
    if not all (key in json for key in transactionKeys):
        return 'Some variables of the transaction are missing', 400

    index = blockchain.addTransaction(json['sender'], json['receiver'], json['vote'])
    response = {'message': f'This transaction will be added to Block {index}'}

    return jsonify(response), 201

@app.route('/connectNode', methods = ['POST'])

def connectNode():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        blockchain.addNode(node)
    response = {'message': 'Connected nodes: ',
                'totalNodes': list(blockchain.nodes)
                }
    
    return jsonify(response), 201

@app.route('/replaceChain', methods = ['GET'])

def replaceChain():
    isChainReplaced = blockchain.replaceChain()

    if isChainReplaced:
        response = {'message': 'The chain has been replaced by the longest chain.',
                    'newChain': blockchain.chain}
    else:
        response = {'message': 'The chain is already the longest chain.',
                    'currentChain': blockchain.chain}
        
    return jsonify(response), 200


app.run(host = '0.0.0.0', port = 5002)