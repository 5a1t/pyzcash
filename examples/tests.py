import os.path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from zcash.ZDaemon import *
from settings import *


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

#	print zd.sendNoteToAddress(encnote, TEST_ZSECRET, TEST_TADDR, 0.33, TEST_ZADDR)

#	print zd.sendNoteToAddress(encnote, TEST_ZSECRET, faucet_addr, 0.33, TEST_ZADDR)


if __name__ == "__main__":
	test_daemon()

