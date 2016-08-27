import requests
import json

ZURL = "http://localhost:18232"
TIMEOUT = 600
RPCUSER = "username"
RPCPASSWORD = "password"
DEFAULT_FEE = 0.01

#for tests
TEST_TXID = '229b48e82366c52e977b51c664691d0b0e5870240c0b80a50f80c0e18287b78d'
TEST_ZADDR = "tnML9eWAXPpun55Wx6NkJugpKxEResbYwk1vuqeB8V3wezNZJqq8RrdE6P4QWiH35Bto14cKvo4GTTTqS5eNveEAFVgVCBs"
TEST_TADDR = "mfhVDFEcYzGBnoGETV7xy4WAmCBji6KfhF"
TEST_ZSECRET = "TKWRH9Ki35CAFTPp3yS21SnqyhpARJgfa8UduWptKDYyAUrHcXUC"

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

	#	print {	'version': '2', 
	#			'method': method,
	#			'params': args, 
	#			'id': self.id_count}

		
		jsondata = json.dumps({	'version': '2', 
				'method': method,
				'params': args, 
				'id': self.id_count})


		r = requests.post(self.url, auth=(self.user,self.password), data=jsondata, timeout=self.timeout)

		self.id_count += 1

		resp = json.loads(r.text)

		#throw later if fails.
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
	def getNewAddress(self, account=""):
		if account:
			return self._call('getnewaddress', account)
		else:
			return self._call('getnewaddress')

	def getTotalBalance(self, account=""):
		if account:
			return self._call('getbalance', account)
		else:
			return self._call('getbalance')

	def getAllAddresses(self):
		return self._call('getaddressesbyaccount', "")
	
	def getUnspentTxs(self):
		return self._call('listunspent')

	#Txs
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

	def receiveTx(self, zsecret, claimnote):
		return self._call('zcrawreceive', zsecret, claimnote)

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
	


def test_daemon():
	zd = ZDaemon()

	print zd.getBlockHash(100)
	print zd.getBlockByHash(zd.getBlockHash(100))
	print zd.getBlockByHeight(100)
	print zd.getNetworkHeight()
	print zd.getNetworkDifficulty()
	print zd.getTotalBalance()
	print zd.getConnectionCount()
	print zd.getNewAddress()
	print zd.getNewZAddress()

	print zd.getUnspentTxs()
	tx_amount = zd.getTxInfo(TEST_TXID).get('details')[0].get('amount')
	tx =  zd.createNewRawTxFromTxid(TEST_TXID)
	pourtx =  zd.pourRawTx(tx, TEST_ZADDR, tx_amount)
	hextx = zd.signRawTx(pourtx.get('rawtxn'))

	print zd.sendRawTx(hextx.get('hex'))

	print pourtx
	print hextx	

	#print zd.receiveTx(TEST_ZSECRET, encnote)
	#print zd.receiveTx(TEST_ZSECRET, encnote1)
	faucet_addr = 'mt35ftTYrriCmTN18EcG8y7oyM1j7ardXw'	

#	print zd.sendNoteToAddress(encnote, TEST_ZSECRET, TEST_TADDR, 0.33, TEST_ZADDR)

#	print zd.sendNoteToAddress(encnote, TEST_ZSECRET, faucet_addr, 0.33, TEST_ZADDR)



