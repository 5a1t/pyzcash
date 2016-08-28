import requests
import json


from pyzcash.settings import *


#https://en.bitcoin.it/wiki/Original_Bitcoin_client/API_calls_list

class ZDaemon(object):

	id_count = 0
	
	def __init__(self, url=ZURL, user=RPCUSER, password=RPCPASSWORD, timeout=TIMEOUT):
		#TODO: check utf safety
		self.url = url
		self.user = user.encode('utf8')
		self.password = password.encode('utf8')
		self.timeout = timeout
		
	def _call(self,  method, *args):

		
		jsondata = json.dumps({	'version': '2', 
				'method': method,
				'params': args, 
				'id': self.id_count})


		r = requests.post(self.url, auth=(self.user,self.password), data=jsondata, timeout=self.timeout)

		self.id_count += 1

		resp = json.loads(r.text)

		#TODO: deal with errors better.
		error = resp['error']
		if error:
			print error
		
		return resp['result']

	#Block Info
	def getBlockHash(self, blockheight):
		return self._call('getblockhash', blockheight)

	def getBlockByHash(self, blockhash):
		return self._call('getblock', blockhash)
	
	def getBlockByHeight(self, blockheight):
		return self.getBlockByHash(self.getBlockHash(blockheight))


	#Network Info
	def getNetworkHeight(self):
		return self._call('getblockcount')

	def getNetworkDifficulty(self):
		return self._call('getdifficulty')


	def getConnectionCount(self):
		return self._call('getconnectioncount')	

	
	#Wallet Info (transparent)
	def getTotalBalance(self, account=""):
		if account:
			return self._call('getbalance', account)
		else:
			return self._call('getbalance')

	def getAllAddresses(self):
		return self._call('getaddressesbyaccount', "")
	
	def getUnspentTxs(self, minconf=1):
		return self._call('listunspent', minconf)

	#Raw Txs
	def getTxInfo(self, txid):
		return self._call('gettransaction', txid)

	def createNewRawTxFromTxid(self, txid):
		tx_info = self.getTxInfo(txid)
		tx = [{}]
		#tx['amount'] = tx_info['details']['amount']
		tx[0]['txid'] = txid
		tx[0]['vout'] = tx_info.get('details')[0].get('vout')

		return self.createNewRawTx(tx)

	def createNewRawTx(self, tx_in=[], taddr_output={}):

		return self._call('createrawtransaction', tx_in, taddr_output)

	def signRawTx(self, rawtx):
		return self._call('signrawtransaction', rawtx)

	def sendRawTx(self, hextx):
		return self._call('sendrawtransaction', hextx)

	def gatherUnspentArray(self, minconf=1):
		unspent = self.getUnspentTxs()
		#tx_array = [{tx['txid'],tx['vout']} for tx in unspent]
		tx_array = []
		acc = 0
		for tx in unspent:
			tx_array.append({'txid':tx['txid'],'vout':tx['vout']})
			acc += tx['amount']

		return acc, tx_array

	#taddr methods
	def getNewAddress(self, account=""):
		if account:
			return self._call('getnewaddress', account)
		else:
			return self._call('getnewaddress')

	def sendTransparent(self, taddress):
		return self._call('sendtoaddress', taddress)
		
	#zaddr methods
	#generates keypair, but does not save to wallet.
	def getNewRawZAddress(self):
		return self._call('zcrawkeygen')
	
	#generates and saves to wallet.
	def getNewZAddress(self):
		return self._call('z_getnewaddress')
	
	def getZAddressKey(self, zaddress):
		return self._call('z_exportkey', zaddress)

	def getAllZAddresses(self):
		return self._call('z_listaddresses')

	#portal between transparent and zcash
	def rawJoinSplit(self, tx, note_input={}, zaddr_output={}, total_in = 0.0, total_out=0.0):

		return self._call('zcrawjoinsplit', tx, note_input, zaddr_output, total_in, total_out)

	#TODO multi-output
	#turns transparent into zcash notes
	#has important output encryptednote1 and encryptednote2
	def pourRawTx(self, tx, zaddress, amount, fee=DEFAULT_FEE):
		return self.rawJoinSplit( tx, zaddr_output={zaddress : amount-fee}, total_in=amount-fee)

	#Pours all unspent transactions (from mining, etc.) into a single poured note.
	def pourAllUnspentTxs(self, zaddress, fee=DEFAULT_FEE):
		amount, tx_array = self.gatherUnspentArray()
		tx = self.createNewRawTx(tx_array)
		pourtx = self.pourRawTx(tx, zaddress, amount, fee)
		hextx = self.signRawTx(pourtx.get('rawtxn'))

		self.sendRawTx(hextx.get('hex'))

		#encnote1 now contains all spendable outputs
		return pourtx


	def receiveTx(self, zsecret, claimnote):
		return self._call('zcrawreceive', zsecret, claimnote)

	#Given a poured (protected) note, and it's corresponding secret, send amount to zaddress_to and send
	#remainder to the provided protected change address.
	def sendNoteToZAddress(self, note, zsecret, zaddress_to, amount, zaddress_change, fee=DEFAULT_FEE):

		note_info = self.receiveTx(zsecret, note)
		amount_left = note_info.get('amount')-amount
		note_note = note_info.get('note')

		blanktx = self.createNewRawTx()
		note_input = {note_note:zsecret}


		if amount_left-fee > 0:
			zaddr_output = {zaddress_to:amount,zaddress_change:amount_left-fee}
		else:
			#nothing left after fee, no change address
			zaddr_output = {zaddress_to:amount}

		join_result =  self.rawJoinSplit(blanktx, note_input, zaddr_output, total_out=fee)

		hextx = self.signRawTx(join_result.get('rawtxn'))

		self.sendRawTx(hextx.get('hex'))

		return join_result

	
	#Given a poured (protected) note, and it's corresponding secret, send amount to transparent address
	#address_to  and send remainder to the provided protected change address.
	def sendNoteToAddress(self, note, zsecret, address_to, amount, zaddress_change, fee=DEFAULT_FEE):
		
		note_info = self.receiveTx(zsecret, note)
		amount_left = note_info.get('amount')-amount
		note_note = note_info.get('note')


		note_input = {note_note:zsecret}

		tx = self.createNewRawTx( taddr_output={address_to:amount})


		if amount_left-fee > 0:
			zaddr_output = {zaddress_change:amount_left-fee}
		else:
			#nothing left after fee, no change address
			zaddr_output = {}
		
		
		
		join_result =  self.rawJoinSplit(tx, note_input, zaddr_output, total_out=amount+fee)

		hextx = self.signRawTx(join_result.get('rawtxn'))

		self.sendRawTx(hextx.get('hex'))

		return join_result

