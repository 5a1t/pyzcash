import os.path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from zcash.ZDaemon import *

#for tests (sample data here - replace with your own)
TEST_TXID = '229b48e82366c52e977b51c664691d0b0e5870240c0b80a50f80c0e18287b78d'
TEST_ZADDR = "tnML9eWAXPpun55Wx6NkJugpKxEResbYwk1vuqeB8V3wezNZJqq8RrdE6P4QWiH35Bto14cKvo4GTTTqS5eNveEAFVgVCBs"
TEST_TADDR = "mfhVDFEcYzGBnoGETV7xy4WAmCBji6KfhF"
TEST_ZSECRET = "TKWRH9Ki35CAFTPp3yS21SnqyhpARJgfa8UduWptKDYyAUrHcXUC"


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

