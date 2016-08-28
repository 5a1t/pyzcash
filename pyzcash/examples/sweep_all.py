import os.path
import sys
import time

from pyzcash.rpc.ZDaemon import *
from pyzcash.settings import *


#Sweeps all unspent transparent txs, cleaning them through a temporary zaddr.
def clean_and_collect_all(taddress=TEST_TADDR, fee=DEFAULT_FEE):
	zd = ZDaemon()

	print "Checking balance..."
	tx_unspents = zd.getUnspentTxs()
	if not len(tx_unspents):
		print "No spendable txs available - visit a faucet or mine!"
		exit()
	
	print "Generating temporary zaddress for tx..."
	zaddress_full = zd.getNewRawZAddress()
	zaddress = zaddress_full.get('zcaddress')
	zsecret = zaddress_full.get('zcsecretkey')

	print "Generated: " + zaddress
	print "Secret: " + zsecret

	print "Gathering and transmitting unspent txs..."
	print "Please wait..."
	notes =  zd.pourAllUnspentTxs(zaddress)
	encnote1 = notes.get('encryptednote1')

	
	print "Found a note to use: \n--------------------------------------------\n" + encnote1 + "\n--------------------------------------------"

	print "Waiting for note to show in blockchain before spendable..."
	print "This may take a few minutes..."
	while zd.receiveTx(zsecret, encnote1).get('exists') is not True:
		print zd.receiveTx(zsecret,encnote1)
		time.sleep(5)

	print "Found note in blockchain!"
	total = zd.receiveTx(zsecret, encnote1).get('amount')
	print "Examined note and found total: " + str(total)

	print "Spending note to target transparent address..."
        tx_response = zd.sendNoteToAddress(encnote1, zsecret, taddress, total-fee, zaddress)

	print "Sent! Check " + taddress + " shortly."


if __name__ == "__main__":
	if len(sys.argv) <= 1:
		print "Usage: python sweep_all.py <transparent address>"
		print "Ex: python sweep_all.py mfu8LbjAq15zmCDLCwUuay9cVc2FcGuY4d"
		exit()
	
	taddr = sys.argv[1]
	if len(taddr) != len('mfu8LbjAq15zmCDLCwUuay9cVc2FcGuY4d'):
		print "That doesn't look like a transparent address.. Maybe you are trying to use a zaddress?"
		exit()
	
	print "Address looks good!"
	clean_and_collect_all(taddr)

