from stellar_sdk import Server, Asset, TransactionBuilder, Network, Keypair
from Daily_Loop import *
import sys
import requests
from random import random
from random import randint as rand
server = Server(horizon_url="https://horizon-testnet.stellar.org")
passphrase = Network.TESTNET_NETWORK_PASSPHRASE
base_fee = server.fetch_base_fee()
# assets = ['KRMA','AIR','SEA','LAND','TREE','HNGR','HLTH','WATR']
assets = ['T00','T01','T10','T11']

def generate_keypair():
    pair=Keypair.random()
    try:
        url = 'https://friendbot.stellar.org?addr='+pair.public_key
        fetch = requests.get(url)
        response = fetch.json()
        if response['successful']: print("new keypair funded:"+"\n"+pair.public_key+"\n"+pair.secret)
    except:
        print(sys.exc_info())
        print("account fund error")
    return pair

def set_trust(source_kp,asset,issuer_kp,pf,bf,server):
    source_acc = server.load_account(source_kp.public_key)
    transaction = TransactionBuilder(
        source_account=source_acc,
        network_passphrase=pf,
        base_fee=bf).append_change_trust_op(
        asset_code=asset,
        asset_issuer=issuer_kp.public_key).build()
    transaction.sign(source_kp)
    try:
        response = server.submit_transaction(transaction)
        if response['successful']: print(asset+" trust set successfull")
    except:
        print(sys.exc_info())
        print("something went wrong setting "+asset+" trustline")

def make_payment(source_kp,destination_kp,asset,issuer_kp,amt,pf,bf,server,asset0):
    if asset == asset0:
        amount = str(10000*amt)
    else:
        amount = str(100000*amt)
    source_acc = server.load_account(source_kp.public_key)
    transaction = TransactionBuilder(
        source_account=source_acc,
        network_passphrase=pf,
        base_fee=bf).append_payment_op(
        destination=destination_kp.public_key,
        amount=amount,
        asset_code=asset,
        asset_issuer=issuer_kp.public_key).build()
    transaction.sign(source_kp)
    try:
        response = server.submit_transaction(transaction)
        if response['successful']: print(asset+" tokens successfully paid out")
    except:
        print(sys.exc_info())
        print("something went wrong paying out "+asset)

def generate_hot_wallets(assets):
    a_h_h = {}
    for i in range(len(assets)):
        new_pair = generate_keypair()
        a_h_h[assets[i]]=new_pair
    return a_h_h

def post_sell_offer(source_kp,asset,issuer_kp,amount,price,pf,bf,server):
    source_acc = server.load_account(source_kp.public_key)
    transaction = TransactionBuilder(
        source_account = source_acc,
        network_passphrase=pf,
        base_fee=bf).append_create_passive_sell_offer_op(
        selling_code=asset,
        selling_issuer=issuer_kp.public_key,
        buying_code='XLM',
        buying_issuer=None,
        amount=amount,
        price=price).build()
    transaction.sign(source_kp)
    try:
        response = server.submit_transaction(transaction)
        if response['successful']: print(asset+" sell offer posted successfully")
    except:
        print(sys.exc_info())
        print("something went wrong posting "+asset+" sell offer")

def make_path_payment(source_kp,asset,issuer_kp,amount,pf,bf,server):
    source_acc = server.load_account(source_kp.public_key)
    path = [
    Asset('XLM',None),
    Asset(asset,issuer_kp.public_key)
    ]
    try:
        transaction = TransactionBuilder(
            source_account = source_acc,
            network_passphrase=pf,
            base_fee=bf).append_path_payment_strict_send_op(
            source_kp.public_key,"XLM",None,str(amount),asset,
            issuer_kp.public_key,str(round(amount*0.1*0.95,0)),path).build()
        transaction.sign(source_kp)
        response = server.submit_transaction(transaction)
        if response['successful']: print("Successfully bought "+str(amount*10)+" "+asset)
    except:
        print(sys.exc_info())
        print("something went wrong buying "+str(amount*10)+" "+asset)

def write_arg_file(assets,issuer_keypair,distributor_keypair):
    filename = 'TEST_'+assets[0]+'.txt'
    w_file = open(filename, "w")
    lines=[]
    lines.append('TOKENS\n')
    for asset in assets:
        lines.append(asset+":"+issuer_keypair.public_key+"\n")
    lines.append('EXCEPTIONS\n')
    lines.append(distributor_keypair.public_key+"\n")
    lines.append('POT\n')
    lines.append('100:'+assets[0]+":"+issuer_keypair.public_key+":"+distributor_keypair.public_key+":"+distributor_keypair.secret+"\n")
    lines.append('MEMOS\nTHANKS!\nThank you\nTYSM\n')
    lines.append('EMAIL\nstephen.d.board@gmail.com\nme@writner.com\nURTH2Moon\n')
    lines.append('NEXT_TIME\n202106181900')
    w_file.writelines(lines)
    w_file.close()
    return filename

def main(assets,server,passphrase,base_fee):

    issuer_keypair = generate_keypair()
    distributor_keypair = generate_keypair()

    for asset in assets:
        set_trust(distributor_keypair,asset,issuer_keypair,passphrase,base_fee,server)
        # issue tokens
        make_payment(issuer_keypair,distributor_keypair,asset,issuer_keypair,1,passphrase,base_fee,server,assets[0])

    asset_hot_holders = generate_hot_wallets(assets)
    for asset in assets:
        set_trust(asset_hot_holders[asset],asset,issuer_keypair,passphrase,base_fee,server)
        # supply hot wallets
        make_payment(distributor_keypair,asset_hot_holders[asset],asset,issuer_keypair,0.1,passphrase,base_fee,server,assets[0])

        if asset != assets[0]:
            post_sell_offer(asset_hot_holders[asset],asset,issuer_keypair,'9000','0.1',passphrase,base_fee,server)

    # generate 10 active users
    for x in range(3):
        pair = generate_keypair()
        set_trust(pair,assets[0],issuer_keypair,passphrase,base_fee,server)
        for i in range(len(assets)):
            asset = assets[rand(0,len(assets)-1)]
            if asset == assets[0]:
                print("can't buy "+assets[0])
            else:
                amount = round(20 + (30*random()),2)
                set_trust(pair,asset,issuer_keypair,passphrase,base_fee,server)
                make_path_payment(pair,asset,issuer_keypair,amount,passphrase,base_fee,server)

    # generate seed file
    arg_file = write_arg_file(assets,issuer_keypair,distributor_keypair)

    # start distribution
    mainloop(arg_file,False)

main(assets,server,passphrase,base_fee)
