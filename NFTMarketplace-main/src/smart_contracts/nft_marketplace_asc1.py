from pyteal import *
import algosdk

class NFTMarketplaceASC1:
    def __init__(self):
        self.escrow_address = Bytes("ESCROW_ADDRESS")
        self.asa_id = Bytes("ASA_ID")
        self.asa_price = Bytes("ASA_PRICE")
        self.asa_owner = Bytes("ASA_OWNER")
        self.app_state = Bytes("APP_STATE")
        self.app_admin = Bytes("APP_ADMIN")

    def on_creation(self):
        return Seq([
            App.globalPut(self.app_state, Int(0)),
            Return(Int(1))
        ])

    def on_closeout(self):
        return Return(Int(1))

    def on_opted_in(self, asset_id, sender):
        return Return(Int(1))

    def on_delete(self, asset_id):
        return Return(Int(1))

    def initialize_escrow(self, escrow_address):
        return Seq([
            Assert(Txn.application_args.length() == Int(2)),
            Assert(Txn.application_args[0] == Bytes("initializeEscrow")),
            Assert(Txn.sender() == App.globalGet(self.app_admin)),
            Assert(App.globalGet(self.app_state) == Int(0)),
            App.globalPut(self.app_state, Int(1)),
            App.globalPut(self.escrow_address, escrow_address),
            Return(Int(1))
        ])

    def make_sell_offer(self, sell_price):
        return Seq([
            Assert(Txn.application_args.length() == Int(2)),
            Assert(Txn.application_args[0] == Bytes("makeSellOffer")),
            Assert(App.globalGet(self.app_state) == Int(1)),
            Assert(Txn.sender() == App.globalGet(self.asa_owner)),
            App.globalPut(self.asa_price, Btoi(sell_price) * Int(10**6)),
            App.globalPut(self.app_state, Int(2)),
            Return(Int(1))
        ])

    def buy(self):
        return Seq([
            Assert(Txn.application_args.length() == Int(1)),
            Assert(Txn.application_args[0] == Bytes("buy")),
            Assert(App.globalGet(self.app_state) == Int(2)),
            Assert(Gtxn[1].type_enum() == TxnType.Payment),
            Assert(Gtxn[1].receiver() == App.globalGet(self.asa_owner)),
            Assert(Gtxn[1].amount() == App.globalGet(self.asa_price)),
            Assert(Gtxn[1].sender() == Gtxn[0].sender()),
            Assert(Gtxn[1].sender() != App.globalGet(self.asa_owner)),
            Assert(Gtxn[2].type_enum() == TxnType.AssetTransfer),
            Assert(Gtxn[2].sender() == App.globalGet(self.escrow_address)),
            Assert(Gtxn[2].xfer_asset() == App.globalGet(self.asa_id)),
            Assert(Gtxn[2].asset_amount() == Int(1)),
            App.globalPut(self.asa_owner, Gtxn[0].sender()),
            App.globalPut(self.app_state, Int(1)),
            Return(Int(1))
        ])

    def stop_sell_offer(self):
        return Seq([
            Assert(Txn.application_args.length() == Int(1)),
            Assert(Txn.application_args[0] == Bytes("stopSellOffer")),
            Assert(App.globalGet(self.app_state) != Int(0)),
            Assert(Txn.sender() == App.globalGet(self.asa_owner)),
            App.globalPut(self.app_state, Int(1)),
            Return(Int(1))
        ])

    def approval_program(self):
        return Cond(
            [Txn.application_id() == Int(0), self.on_creation()],
            [Txn.on_closeout(), self.on_closeout()],
            [Txn.on_opted_in(), self.on_opted_in(Txn.asset_id(), Txn.sender())],
            [Txn.on_delete(), self.on_delete(Txn.asset_id())],
            [Txn.application_args[0] == Bytes("initializeEscrow"), self.initialize_escrow(Txn.application_args[1])],
            [Txn.application_args[0] == Bytes("makeSellOffer"), self.make_sell_offer(Txn.application_args[1])],
            [Txn.application_args[0] == Bytes("buy"), self.buy()],
            [Txn.application_args[0] == Bytes("stopSellOffer"), self.stop_sell_offer()]
        )

    def clear_program(self):
        return Return(Int(1))

    @property
    def global_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=3, num_byte_slices=3)

    @property
    def local_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=0, num_byte_slices=0)

# Instantiate the contract
nft_marketplace_contract = NFTMarketplaceASC1()
