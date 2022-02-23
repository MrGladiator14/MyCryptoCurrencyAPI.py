# module 2: creating crypto
# importing libraries
import datetime
import hashlib
import json  #cause postman accepts it
from flask import Flask, jsonify , request #to display results on postman
import requests
from uuid import uuid4
from urllib.parse import urlparse



# Pt 1 - building a blockchain

class Blockchain:
    def __init__(self):  #kindof a constructor
        self.chain = []
        self.transactions = []
        
        self.create_block (proof = 1 , previous_hash ='0')
        self.nodes = set()
        
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain)+1 , 
                 'timestamp':str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash':previous_hash,
                 'transactions': self.transactions}
        self.transactions=[]
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
         return self.chain[-1]
     
    def proof_of_work(self,previous_proof):
        new_proof=1 #looks similar to NONCE
        check_proof=False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:5]=='00000':
                check_proof=True
            else:
                new_proof+=1
        return new_proof 
    
    def hash(self,block): #hashing the entire block
        encoded_block = json.dumps(block, sort_keys =True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self,chain):
        previous_block=chain[0]
        block_index=1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash']!=self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof=block['proof']
            hash_operation= hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:5]!='00000':
                return False
            previous_block = block
            block_index+=1
        return True
    def add_transactions(self, sender,receiver,amount):
        self.transactions.append({'sender': sender, 'receiver':receiver, 'amount':amount})
        previous_block = self.get_previous_block()
        return previous_block['index']+1
    
    def add_node(self, address):  #this function returns the (i guess) port number i.e. 5000,5001,5002 etc
        parsed_url = urlparse(address)   
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network=self.nodes
        longest_chain=None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain') #checks chain at each node
            if response.status_code == 200:
                length = response.json['length']
                chain = response.json['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length=length
                    longest_chain=chain
        if longest_chain:
            self.chain= longest_chain # checks all the chain of longest one and then updates the self.chain
            return True
        return False
        
# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# creating anaddress for the node on port 5000
node_address = str(uuid4()).replace('-','')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender=node_address, receiver = 'Bryson', amount= 777 ) #here the receiver mines the coins to get rewards
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions':block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': ' The blockchain hasnt been tempered.'}
    else:
        response = {'message': ' We have a problem. The blockchain hasn been tempered with.'}
    return jsonify(response), 200

#adding new transactions to the blockchain
@app.route('/add_transactions', methods=['POST'])
def add_trsaction():
    json=request.get_jason()
    transaction_keys = ['sender','receiver','amount']
    if not all(key in json for key in transaction_keys):
        return 'some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'this transaction will be added to block {index}'}
    return jsonify(response),201

#part 3 i.e. decentralizing the blockchain
#connecting a new node
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json=request.get_json()
    nodes= json.get('nodes')
    if nodes is None:
        return " NO Node ", 400
    for node in nodes:
        blockchain.add_node(node)
        response = { 'message': 'All nodes are now connectef. Tipcoin now contains the following nodes:',
                    'total_nodes': list(blockchain.nodes)}
        return jsonify(response),201
    
# replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200
# Running the app
app.run(host = '0.0.0.0', port = 5000)
    
                                                      
        

        
        
